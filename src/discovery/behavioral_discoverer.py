"""
Behavioral Discovery Engine

Queries foundation_grants + form990_financials + bmf_organizations to find funders
who have *actually given grants* matching a profile's signals — not just orgs that
look like funders based on NTEE codes or geography.

Key tables (nonprofit_intelligence.db):
  foundation_grants     — Schedule I / 990-PF Part XV grants (9.7M rows, 2021-2024)
  form990_financials    — Annual financial summaries (1.2M rows)
  bmf_organizations     — IRS Business Master File (~750K orgs)

Performance notes:
  - Always filter by tax_year >= min_year first (uses idx_fg_year index)
  - Keyword scoring is done in Python after fetching, not as SQL LIKE filters
  - Geo filter on recipient_state uses idx_fg_state index (~3s), no geo = ~7s
  - Results are scored and capped at `limit` (default 200)
"""
import sqlite3
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.config.database_config import get_nonprofit_intelligence_db

logger = logging.getLogger(__name__)


@dataclass
class BehavioralCandidate:
    """A funder candidate identified by behavioral grant history."""
    ein: str
    name: str
    state: Optional[str]
    ntee_code: Optional[str]

    # Grant behavior signals
    grant_count: int = 0
    avg_grant: float = 0.0
    last_active_year: int = 0
    grant_purposes: str = ""          # concatenated sample purposes for scoring

    # Financial health
    grants_paid: float = 0.0
    assets_fmv: float = 0.0
    total_revenue: float = 0.0

    # Scoring outputs
    pre_score: float = 0.0
    score_breakdown: Dict[str, float] = field(default_factory=dict)

    # Source tracking
    source: str = "foundation_grants"  # or "public_charity_financials"


def _extract_profile_signals(profile_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a raw profile DB row (JSON fields may be strings) into matching signals.
    Returns a dict with keys: keywords, ntee_codes, ntee_prefixes, states,
    nationwide, min_ask, max_ask.
    """
    import json

    def _parse_json_list(val) -> List[str]:
        if isinstance(val, list):
            return [str(v) for v in val if v]
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return [str(v) for v in parsed if v]
            except Exception:
                pass
        return []

    def _parse_json_dict(val) -> Dict:
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return {}

    # Keywords: combine focus_areas + program_areas + target_populations + keywords field
    keywords: List[str] = []
    for f in ('focus_areas', 'program_areas', 'target_populations'):
        keywords.extend(v.lower().strip() for v in _parse_json_list(profile_dict.get(f)) if v)

    raw_kw = profile_dict.get('keywords') or ''
    if isinstance(raw_kw, str) and raw_kw:
        keywords.extend(k.strip().lower() for k in raw_kw.replace(';', ',').split(',') if k.strip())

    # Deduplicate, remove empties, keep only 2+ char terms
    keywords = list({k for k in keywords if len(k) >= 2})

    # NTEE codes
    ntee_codes = _parse_json_list(profile_dict.get('ntee_codes'))
    ntee_prefixes = list({c[0].upper() for c in ntee_codes if c})

    # Geography
    geo = _parse_json_dict(profile_dict.get('geographic_scope'))
    states: List[str] = geo.get('states') or []
    nationwide: bool = bool(
        geo.get('nationwide') or geo.get('national') or
        geo.get('scope') in ('national', 'nationwide', 'international')
    )

    # Funding ask range
    fp = _parse_json_dict(profile_dict.get('funding_preferences'))
    min_ask: Optional[float] = fp.get('min_amount') or fp.get('minimum_amount')
    max_ask: Optional[float] = fp.get('max_amount') or fp.get('maximum_amount')

    return {
        'keywords': keywords,
        'ntee_codes': ntee_codes,
        'ntee_prefixes': ntee_prefixes,
        'states': [s.upper() for s in states if s],
        'nationwide': nationwide,
        'min_ask': float(min_ask) if min_ask else None,
        'max_ask': float(max_ask) if max_ask else None,
    }


def _score_candidate(
    candidate: BehavioralCandidate,
    signals: Dict[str, Any],
    current_year: int,
) -> float:
    """
    Score a candidate on 6 zero-cost signals (weights sum to 1.0).

    Signals:
      amount_alignment (25%) — avg grant vs profile ask range
      geo_alignment    (20%) — funder state vs profile states
      keyword_density  (15%) — profile keywords found in grant purposes
      recency          (15%) — how recently they gave grants
      frequency        (15%) — consistent giver vs one-time
      payout_health    (10%) — grants_paid / assets ratio
    """
    scores: Dict[str, float] = {}

    # 1. Amount alignment (25%)
    min_ask = signals.get('min_ask')
    max_ask = signals.get('max_ask')
    avg = candidate.avg_grant
    if avg > 0 and (min_ask or max_ask):
        lower = float(min_ask or 0)
        upper = float(max_ask or float('inf'))
        if lower <= avg <= upper:
            scores['amount_alignment'] = 1.0
        elif avg < lower and lower > 0:
            scores['amount_alignment'] = max(0.1, avg / lower)
        else:  # avg > upper
            scores['amount_alignment'] = max(0.1, upper / avg) if avg > 0 else 0.1
    else:
        scores['amount_alignment'] = 0.5  # neutral — no ask range specified

    # 2. Geographic alignment (20%)
    if signals.get('nationwide') or not signals.get('states'):
        scores['geo_alignment'] = 1.0
    elif candidate.state and candidate.state.upper() in signals.get('states', []):
        scores['geo_alignment'] = 1.0
    else:
        scores['geo_alignment'] = 0.2

    # 3. Keyword density (15%) — keyword hits in concatenated grant purposes
    purposes_lower = (candidate.grant_purposes or '').lower()
    kws = signals.get('keywords', [])
    if kws and purposes_lower:
        matched = sum(1 for kw in kws if kw and kw in purposes_lower)
        scores['keyword_density'] = min(1.0, matched / max(len(kws), 1))
    elif not kws:
        scores['keyword_density'] = 0.5  # neutral — no keywords to match
    else:
        scores['keyword_density'] = 0.1  # purposes empty

    # 4. Recency (15%)
    delta = current_year - candidate.last_active_year
    recency_map = {0: 1.0, 1: 0.85, 2: 0.65, 3: 0.40}
    scores['recency'] = recency_map.get(delta, 0.15)

    # 5. Grant frequency (15%)
    cnt = candidate.grant_count
    if cnt >= 10:
        scores['frequency'] = 1.0
    elif cnt >= 5:
        scores['frequency'] = 0.8
    elif cnt >= 3:
        scores['frequency'] = 0.6
    elif cnt >= 2:
        scores['frequency'] = 0.4
    else:
        scores['frequency'] = 0.2

    # 6. Financial payout health (10%)
    if candidate.assets_fmv > 0 and candidate.grants_paid > 0:
        rate = candidate.grants_paid / candidate.assets_fmv
        if rate >= 0.08:
            scores['payout_health'] = 1.0
        elif rate >= 0.05:
            scores['payout_health'] = 0.7
        elif rate >= 0.02:
            scores['payout_health'] = 0.4
        else:
            scores['payout_health'] = 0.1
    elif candidate.grants_paid > 0:
        scores['payout_health'] = 0.5  # has grants_paid but no asset data
    elif candidate.assets_fmv > 1_000_000:
        # grants_paid_total is often NULL in bulk data (community foundations report differently).
        # Large assets = meaningful capacity even without explicit grants_paid.
        scores['payout_health'] = 0.6
    elif candidate.assets_fmv > 100_000:
        scores['payout_health'] = 0.4
    else:
        scores['payout_health'] = 0.2

    weights = {
        'amount_alignment': 0.25,
        'geo_alignment':    0.20,
        'keyword_density':  0.15,
        'recency':          0.15,
        'frequency':        0.15,
        'payout_health':    0.10,
    }
    total = sum(scores[k] * weights[k] for k in weights)
    candidate.score_breakdown = {k: round(v, 3) for k, v in scores.items()}
    return round(total, 4)


def discover_behavioral_candidates(
    profile_dict: Dict[str, Any],
    limit: int = 200,
    min_year: int = 2022,
    min_grant_amount: float = 1000.0,
    include_public_charity_track: bool = True,
) -> List[BehavioralCandidate]:
    """
    Query nonprofit_intelligence.db for funders with proven grant-giving behavior
    matching the profile. Returns up to `limit` candidates sorted by pre_score desc.

    Args:
        profile_dict:  Raw profile row dict from catalynx.db (JSON fields may be strings).
        limit:         Max candidates to return after scoring (default 200).
        min_year:      Earliest tax_year to include (default 2022).
        min_grant_amount: Minimum grant_amount filter (default $1K).
        include_public_charity_track: Also query form990_financials for nonprofits
                       with significant grants_paid but no foundation_grants rows.
    """
    from datetime import datetime
    current_year = datetime.now().year

    db_path = get_nonprofit_intelligence_db()
    signals = _extract_profile_signals(profile_dict)
    states = signals['states']
    nationwide = signals['nationwide']
    min_ask = signals.get('min_ask')
    max_ask = signals.get('max_ask')

    candidates: Dict[str, BehavioralCandidate] = {}

    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # ─────────────────────────────────────────────────────────────────────
        # Track 1: foundation_grants (primary — proven grant behavior)
        # Filter by year + amount (uses indexes). Keyword scoring done in Python.
        # Geo filter on recipient_state or grantor state.
        # ─────────────────────────────────────────────────────────────────────
        where_parts = [
            f"g.tax_year >= {min_year}",
            f"g.grant_amount >= {min_grant_amount}",
        ]
        params: List = []

        # Amount range filter
        if min_ask:
            where_parts.append("g.grant_amount >= ?")
            params.append(min_ask * 0.33)  # wide lower bound (small installments)
        if max_ask:
            where_parts.append("g.grant_amount <= ?")
            params.append(max_ask * 5.0)   # wide upper bound

        # Geographic filter — find grantors headquartered in target states.
        # recipient_state is not populated in the bulk-loaded data, so we use a
        # correlated subquery on bmf_organizations (0.8s vs 26s vs OR-JOIN approach).
        if not nationwide and states:
            placeholders = ",".join("?" * len(states))
            where_parts.append(
                f"g.grantor_ein IN "
                f"(SELECT ein FROM bmf_organizations WHERE state IN ({placeholders}))"
            )
            params.extend(states)

        where_sql = " AND ".join(where_parts)

        # ── Step 1a: foundation_grants — grant behavior (no financial join yet) ──
        sql = f"""
            SELECT
                g.grantor_ein                                           AS ein,
                COALESCE(b.name, 'Unknown')                            AS name,
                b.state                                                 AS state,
                b.ntee_code                                             AS ntee_code,
                COUNT(*)                                               AS grant_count,
                AVG(g.grant_amount)                                    AS avg_grant,
                MAX(g.tax_year)                                        AS last_active,
                SUBSTR(GROUP_CONCAT(
                    DISTINCT SUBSTR(COALESCE(g.grant_purpose,''), 1, 80)
                ), 1, 500)                                             AS purposes
            FROM   foundation_grants g
            LEFT JOIN bmf_organizations b  ON g.grantor_ein = b.ein
            WHERE  {where_sql}
            GROUP  BY g.grantor_ein
            HAVING grant_count >= 1
            ORDER  BY grant_count DESC, avg_grant DESC
            LIMIT  3000
        """

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        logger.info(f"BehavioralDiscovery Track 1: {len(rows)} foundation_grants candidates")

        for row in rows:
            ein = row['ein']
            if not ein:
                continue
            c = BehavioralCandidate(
                ein=ein,
                name=row['name'],
                state=row['state'],
                ntee_code=row['ntee_code'],
                grant_count=row['grant_count'] or 0,
                avg_grant=float(row['avg_grant'] or 0),
                last_active_year=row['last_active'] or 0,
                grant_purposes=row['purposes'] or '',
                source='foundation_grants',
            )
            # Initial score without financial data (payout_health defaults to 0.2)
            c.pre_score = _score_candidate(c, signals, current_year)
            candidates[ein] = c

        # ── Step 1b: Enrich top 500 with financial data (fast EIN-index lookup) ──
        top_eins = [c.ein for c in sorted(
            candidates.values(), key=lambda x: x.pre_score, reverse=True
        )[:500]]
        if top_eins:
            # Split into chunks of 500 to stay under SQLite variable limits
            chunk_size = 500
            financial_data: Dict[str, Dict] = {}
            for i in range(0, len(top_eins), chunk_size):
                chunk = top_eins[i:i + chunk_size]
                ph = ",".join("?" * len(chunk))
                cursor.execute(f"""
                    SELECT ein,
                           SUM(grants_paid_total)                   AS grants_paid,
                           MAX(COALESCE(assets_fmv, total_assets, 0)) AS assets_fmv,
                           MAX(COALESCE(total_revenue, 0))           AS total_revenue
                    FROM   form990_financials
                    WHERE  ein IN ({ph}) AND tax_year >= {min_year}
                    GROUP  BY ein
                """, chunk)
                for frow in cursor.fetchall():
                    financial_data[frow['ein']] = {
                        'grants_paid': float(frow['grants_paid'] or 0),
                        'assets_fmv':  float(frow['assets_fmv'] or 0),
                        'total_revenue': float(frow['total_revenue'] or 0),
                    }

            # Re-score top 500 with financial data added
            for ein in top_eins:
                if ein in candidates and ein in financial_data:
                    fd = financial_data[ein]
                    c = candidates[ein]
                    c.grants_paid   = fd['grants_paid']
                    c.assets_fmv    = fd['assets_fmv']
                    c.total_revenue = fd['total_revenue']
                    c.pre_score = _score_candidate(c, signals, current_year)  # re-score

        # ─────────────────────────────────────────────────────────────────────
        # Track 2: Public charity grants (form990_financials grants_paid_total)
        # Catches nonprofits that give grants but whose individual grants aren't
        # in foundation_grants (Schedule I threshold is $5K per recipient).
        # ─────────────────────────────────────────────────────────────────────
        if include_public_charity_track:
            ntee_prefixes = signals.get('ntee_prefixes', [])

            pub_where_parts = [
                "f.grants_paid_total > 50000",
                f"f.tax_year >= {min_year}",
            ]
            pub_params: List = []

            if ntee_prefixes:
                ntee_placeholders = " OR ".join(["b.ntee_code LIKE ?" for _ in ntee_prefixes])
                pub_where_parts.append(f"({ntee_placeholders})")
                pub_params.extend(f"{p}%" for p in ntee_prefixes)

            if not nationwide and states:
                placeholders = ",".join("?" * len(states))
                pub_where_parts.append(f"b.state IN ({placeholders})")
                pub_params.extend(states)

            pub_where_sql = " AND ".join(pub_where_parts)

            pub_sql = f"""
                SELECT
                    f.ein                                        AS ein,
                    COALESCE(b.name, 'Unknown')                  AS name,
                    b.state                                      AS state,
                    b.ntee_code                                  AS ntee_code,
                    SUM(COALESCE(f.grants_paid_total, 0))        AS grants_paid,
                    MAX(COALESCE(f.assets_fmv, f.total_assets, 0)) AS assets_fmv,
                    MAX(COALESCE(f.total_revenue, 0))            AS total_revenue,
                    MAX(f.tax_year)                              AS last_active
                FROM   form990_financials f
                LEFT JOIN bmf_organizations b ON f.ein = b.ein
                WHERE  {pub_where_sql}
                GROUP  BY f.ein
                ORDER  BY grants_paid DESC
                LIMIT  500
            """

            cursor.execute(pub_sql, pub_params)
            pub_rows = cursor.fetchall()
            logger.info(f"BehavioralDiscovery Track 2: {len(pub_rows)} public_charity candidates")

            for row in pub_rows:
                ein = row['ein']
                if not ein or ein in candidates:
                    continue  # foundation_grants match takes precedence
                c = BehavioralCandidate(
                    ein=ein,
                    name=row['name'],
                    state=row['state'],
                    ntee_code=row['ntee_code'],
                    grant_count=1,          # no per-grant data in this track
                    avg_grant=float(row['grants_paid'] or 0),
                    last_active_year=row['last_active'] or 0,
                    grant_purposes='',
                    grants_paid=float(row['grants_paid'] or 0),
                    assets_fmv=float(row['assets_fmv'] or 0),
                    total_revenue=float(row['total_revenue'] or 0),
                    source='public_charity_financials',
                )
                c.pre_score = _score_candidate(c, signals, current_year)
                candidates[ein] = c

        conn.close()

    except Exception as exc:
        logger.error(f"BehavioralDiscovery query failed: {exc}", exc_info=True)

    # Sort by pre_score descending, cap at limit
    sorted_candidates = sorted(candidates.values(), key=lambda c: c.pre_score, reverse=True)
    result = sorted_candidates[:limit]
    logger.info(
        f"BehavioralDiscovery complete: {len(candidates)} total candidates → "
        f"top {len(result)} returned (limit={limit})"
    )
    return result
