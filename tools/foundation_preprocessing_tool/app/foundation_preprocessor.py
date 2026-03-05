#!/usr/bin/env python3
"""
Foundation Preprocessing Tool - Monthly Batch Intelligence Index Builder

Precomputes foundation features from 990-PF data so that profile-to-foundation
matching is instant (<100ms) instead of requiring per-query calculations.

Universal preprocessing (profile-independent):
  1. Compliance pre-filter (eliminate ineligible foundations)
  2. Capacity tier scoring (Mega/Major/Significant/Modest/Minimal)
  3. Giving trend analysis (Growing/Stable/Declining/Erratic)
  4. Financial health classification (Strong/Stable/Declining/Distressed)
  5. Portfolio diversity scoring
  6. Board network index building
  7. Geographic concentration from grant patterns

Profile-specific matching (per-profile, cached):
  8. NTEE alignment scoring
  9. Geographic overlap scoring
  10. Grant size fit scoring
  11. Archetype match scoring
  12. Composite match score with weighted dimensions

Cost: $0 (pure SQL + algorithmic, no AI calls)
Runtime: ~5-30 minutes for full 235K foundation database
Frequency: Monthly batch, with on-demand refresh per foundation
"""

import asyncio
import json
import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# STRUCTURED OUTPUT MODELS
# =============================================================================

@dataclass
class PreprocessingStats:
    """Results from a preprocessing batch run."""
    foundations_processed: int = 0
    foundations_eligible: int = 0
    foundations_disqualified: int = 0
    capacity_distribution: Dict[str, int] = field(default_factory=dict)
    trend_distribution: Dict[str, int] = field(default_factory=dict)
    health_distribution: Dict[str, int] = field(default_factory=dict)
    board_members_indexed: int = 0
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class FoundationFeatures:
    """Precomputed features for a single foundation."""
    ein: str
    capacity_tier: str = "unknown"
    grants_paid_latest: int = 0
    assets_fmv_latest: int = 0
    avg_grant_size: int = 0
    annual_grant_budget_estimate: int = 0
    giving_trend: str = "unknown"
    giving_trend_pct: Optional[float] = None
    years_of_data: int = 0
    is_eligible_grantmaker: bool = True
    disqualification_reasons: List[str] = field(default_factory=list)
    grants_to_individuals_only: bool = False
    is_operating_foundation: bool = False
    non_charity_grants: bool = False
    health_status: str = "unknown"
    payout_compliance: str = "unknown"
    payout_ratio: Optional[float] = None
    undistributed_income: Optional[int] = None
    future_grants_approved: int = 0
    portfolio_type: str = "unknown"
    portfolio_diversity_score: float = 0.0
    investment_return_rate: Optional[float] = None
    primary_states: List[str] = field(default_factory=list)
    geographic_concentration: float = 0.0
    ntee_code: Optional[str] = None
    ntee_major_group: Optional[str] = None
    data_quality_score: float = 0.0
    source_tax_year: Optional[int] = None


@dataclass
class ProfileMatchResult:
    """Match scores between a profile and a foundation."""
    profile_id: str
    foundation_ein: str
    overall_match_score: float = 0.0
    ntee_alignment_score: float = 0.0
    geographic_alignment_score: float = 0.0
    grant_size_fit_score: float = 0.0
    archetype_match_score: float = 0.0
    giving_trend_score: float = 0.0
    board_connection_score: float = 0.0
    matching_ntee_codes: List[str] = field(default_factory=list)
    matching_states: List[str] = field(default_factory=list)
    matching_archetypes: List[str] = field(default_factory=list)
    recommended_ask_range: str = ""


# =============================================================================
# FOUNDATION PREPROCESSING ENGINE
# =============================================================================

class FoundationPreprocessor:
    """
    Batch preprocessor that builds the Foundation Intelligence Index.

    Reads from: bmf_organizations, form_990pf (multiple years)
    Writes to: foundation_intelligence_index, board_network_index
    """

    # Match score weights (sum to 1.0)
    MATCH_WEIGHTS = {
        "ntee_alignment": 0.30,
        "geographic_alignment": 0.20,
        "grant_size_fit": 0.20,
        "archetype_match": 0.15,
        "giving_trend": 0.10,
        "board_connection": 0.05,
    }

    # Capacity tier thresholds (grants paid annually)
    CAPACITY_TIERS = {
        "mega": 5_000_000,
        "major": 1_000_000,
        "significant": 100_000,
        "modest": 10_000,
        "minimal": 0,
    }

    def __init__(self, intelligence_db_path: str, app_db_path: Optional[str] = None):
        self.intelligence_db_path = intelligence_db_path
        self.app_db_path = app_db_path
        self.version = "1.0.0"

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory."""
        conn = sqlite3.connect(self.intelligence_db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _ensure_tables(self, conn: sqlite3.Connection):
        """Create preprocessing tables if they don't exist."""
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "src", "database", "migrations",
            "add_foundation_preprocessing_tables.sql"
        )
        if os.path.exists(migration_path):
            with open(migration_path, "r") as f:
                sql = f.read()
            # Execute each statement separately (split on semicolons)
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    try:
                        conn.execute(statement)
                    except sqlite3.OperationalError:
                        pass  # View/index may already exist
            conn.commit()
        else:
            logger.warning(f"Migration file not found at {migration_path}")

    # =========================================================================
    # BATCH PREPROCESSING (Foundation-side, universal)
    # =========================================================================

    async def run_full_preprocessing(self, batch_size: int = 1000) -> PreprocessingStats:
        """
        Run the complete monthly preprocessing batch.

        Steps:
          1. Ensure tables exist
          2. Load all foundation 990-PF data
          3. Compute features per foundation
          4. Write to foundation_intelligence_index
          5. Build board network index
          6. Return stats
        """
        start_time = time.time()
        stats = PreprocessingStats()
        conn = self._get_connection()

        try:
            self._ensure_tables(conn)

            # Step 1: Get all foundations with 990-PF data
            foundations = self._load_foundation_data(conn)
            logger.info(f"Loaded {len(foundations)} foundations with 990-PF data")

            # Step 2: Compute features for each foundation
            features_batch = []
            for ein, years_data in foundations.items():
                try:
                    features = self._compute_foundation_features(ein, years_data, conn)
                    features_batch.append(features)

                    if features.is_eligible_grantmaker:
                        stats.foundations_eligible += 1
                    else:
                        stats.foundations_disqualified += 1

                    # Track distributions
                    stats.capacity_distribution[features.capacity_tier] = (
                        stats.capacity_distribution.get(features.capacity_tier, 0) + 1
                    )
                    stats.trend_distribution[features.giving_trend] = (
                        stats.trend_distribution.get(features.giving_trend, 0) + 1
                    )
                    stats.health_distribution[features.health_status] = (
                        stats.health_distribution.get(features.health_status, 0) + 1
                    )

                    # Write in batches
                    if len(features_batch) >= batch_size:
                        self._write_features_batch(conn, features_batch)
                        stats.foundations_processed += len(features_batch)
                        features_batch = []
                        logger.info(f"Processed {stats.foundations_processed} foundations...")

                except Exception as e:
                    stats.errors.append(f"Error processing {ein}: {str(e)}")
                    logger.error(f"Error processing foundation {ein}: {e}")

            # Write remaining batch
            if features_batch:
                self._write_features_batch(conn, features_batch)
                stats.foundations_processed += len(features_batch)

            # Step 3: Build board network index
            board_count = self._build_board_network_index(conn)
            stats.board_members_indexed = board_count

            conn.commit()
            stats.execution_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Preprocessing complete: {stats.foundations_processed} foundations, "
                f"{stats.foundations_eligible} eligible, "
                f"{stats.foundations_disqualified} disqualified, "
                f"{stats.board_members_indexed} board members indexed, "
                f"{stats.execution_time_ms:.0f}ms"
            )

            return stats

        except Exception as e:
            logger.error(f"Fatal preprocessing error: {e}")
            stats.errors.append(f"Fatal: {str(e)}")
            stats.execution_time_ms = (time.time() - start_time) * 1000
            return stats
        finally:
            conn.close()

    def _load_foundation_data(self, conn: sqlite3.Connection) -> Dict[str, List[Dict]]:
        """
        Load all foundation 990-PF data grouped by EIN, with BMF metadata.
        Returns: {ein: [year1_data, year2_data, ...]}
        """
        query = """
            SELECT
                pf.ein,
                pf.tax_year,
                pf.contrpdpbks,
                pf.fairmrktvalamt,
                pf.totassetsend,
                pf.distribamt,
                pf.undistribincyr,
                pf.grntapprvfut,
                pf.netinvstinc,
                pf.adjnetinc,
                pf.totexcapgnls,
                pf.invstgovtoblig,
                pf.invstcorpstk,
                pf.invstcorpbnd,
                pf.totinvstsec,
                pf.operatingcd,
                pf.grntindivcd,
                pf.nchrtygrntcd,
                pf.propgndacd,
                pf.ipubelectcd,
                pf.compofficers,
                b.ntee_code,
                b.state,
                b.foundation_code,
                b.name
            FROM form_990pf pf
            LEFT JOIN bmf_organizations b ON pf.ein = b.ein
            ORDER BY pf.ein, pf.tax_year DESC
        """

        foundations: Dict[str, List[Dict]] = {}
        try:
            cursor = conn.execute(query)
            for row in cursor:
                ein = row["ein"]
                if ein not in foundations:
                    foundations[ein] = []
                foundations[ein].append(dict(row))
        except sqlite3.OperationalError as e:
            logger.error(f"Error loading foundation data: {e}")

        return foundations

    def _compute_foundation_features(
        self, ein: str, years_data: List[Dict], conn: sqlite3.Connection
    ) -> FoundationFeatures:
        """Compute all precomputed features for a single foundation."""
        features = FoundationFeatures(ein=ein)

        if not years_data:
            return features

        # Use most recent year as primary
        latest = years_data[0]
        features.source_tax_year = latest.get("tax_year")
        features.ntee_code = latest.get("ntee_code")
        features.ntee_major_group = (
            latest.get("ntee_code", "")[0] if latest.get("ntee_code") else None
        )

        # --- Capacity Tier ---
        grants_paid = latest.get("contrpdpbks") or 0
        assets_fmv = latest.get("fairmrktvalamt") or 0
        features.grants_paid_latest = grants_paid
        features.assets_fmv_latest = assets_fmv
        features.capacity_tier = self._compute_capacity_tier(grants_paid)
        features.annual_grant_budget_estimate = int(assets_fmv * 0.05) if assets_fmv > 0 else 0

        # Estimate average grant size (rough: assume 1 grant per $25K)
        if grants_paid > 0:
            est_count = max(1, grants_paid // 25000)
            features.avg_grant_size = grants_paid // est_count
        features.years_of_data = len(years_data)

        # --- Giving Trend ---
        features.giving_trend, features.giving_trend_pct = self._compute_giving_trend(years_data)

        # --- Compliance Pre-Filter ---
        self._compute_compliance_flags(features, latest)

        # --- Financial Health ---
        features.health_status = self._compute_health_status(latest, years_data)
        features.payout_compliance, features.payout_ratio = self._compute_payout_compliance(latest)
        features.undistributed_income = latest.get("undistribincyr")
        features.future_grants_approved = latest.get("grntapprvfut") or 0

        # --- Portfolio Profile ---
        features.portfolio_type, features.portfolio_diversity_score = (
            self._compute_portfolio_profile(latest)
        )
        assets = latest.get("fairmrktvalamt") or latest.get("totassetsend") or 0
        net_inv = latest.get("netinvstinc") or 0
        features.investment_return_rate = net_inv / assets if assets > 0 else None

        # --- Data Quality Score ---
        features.data_quality_score = self._compute_data_quality(latest, years_data)

        return features

    def _compute_capacity_tier(self, grants_paid: int) -> str:
        """Classify foundation by annual grants paid."""
        for tier, threshold in self.CAPACITY_TIERS.items():
            if grants_paid >= threshold:
                return tier
        return "minimal"

    def _compute_giving_trend(self, years_data: List[Dict]) -> Tuple[str, Optional[float]]:
        """Analyze giving trend across available years."""
        if len(years_data) < 2:
            return ("new" if len(years_data) == 1 else "unknown"), None

        # Get grants paid per year (most recent first)
        grants_by_year = []
        for yd in years_data:
            gp = yd.get("contrpdpbks") or 0
            year = yd.get("tax_year")
            if year:
                grants_by_year.append((year, gp))

        if len(grants_by_year) < 2:
            return "unknown", None

        # Sort chronologically (oldest first)
        grants_by_year.sort(key=lambda x: x[0])

        # Calculate year-over-year changes
        latest_grants = grants_by_year[-1][1]
        earliest_grants = grants_by_year[0][1]

        if earliest_grants == 0:
            if latest_grants > 0:
                return "growing", None
            return "stable", 0.0

        change_pct = (latest_grants - earliest_grants) / earliest_grants * 100

        # Check for erratic behavior (high variance)
        if len(grants_by_year) >= 3:
            values = [g for _, g in grants_by_year]
            mean_val = sum(values) / len(values)
            if mean_val > 0:
                variance = sum((v - mean_val) ** 2 for v in values) / len(values)
                cv = (variance ** 0.5) / mean_val  # Coefficient of variation
                if cv > 0.5:
                    return "erratic", change_pct

        if change_pct > 15:
            return "growing", change_pct
        elif change_pct < -15:
            return "declining", change_pct
        else:
            return "stable", change_pct

    def _compute_compliance_flags(self, features: FoundationFeatures, data: Dict):
        """Check compliance flags that disqualify a foundation."""
        reasons = []

        # Operating foundation (different rules, usually not a funder)
        if data.get("operatingcd") in ("1", "Y", True):
            features.is_operating_foundation = True
            reasons.append("operating_foundation")

        # Grants only to individuals (not to organizations)
        if data.get("grntindivcd") in ("1", "Y", True):
            features.grants_to_individuals_only = True
            reasons.append("grants_to_individuals_only")

        # Non-charity grants flag
        if data.get("nchrtygrntcd") in ("1", "Y", True):
            features.non_charity_grants = True
            reasons.append("non_charity_grantmaker")

        # No grants paid and no future grants
        grants_paid = data.get("contrpdpbks") or 0
        future_grants = data.get("grntapprvfut") or 0
        if grants_paid == 0 and future_grants == 0:
            reasons.append("no_grant_activity")

        features.disqualification_reasons = reasons
        # Disqualify if grants_to_individuals_only (most restrictive)
        # Operating foundations can still be targets in some cases
        features.is_eligible_grantmaker = not features.grants_to_individuals_only

    def _compute_health_status(self, latest: Dict, years_data: List[Dict]) -> str:
        """Classify foundation financial health."""
        assets = latest.get("fairmrktvalamt") or latest.get("totassetsend") or 0
        grants = latest.get("contrpdpbks") or 0
        net_income = latest.get("adjnetinc") or 0
        cap_gains = latest.get("totexcapgnls") or 0

        if assets <= 0:
            return "distressed"

        # Check asset trend across years
        if len(years_data) >= 2:
            prev_assets = years_data[1].get("fairmrktvalamt") or years_data[1].get("totassetsend") or 0
            if prev_assets > 0:
                asset_change = (assets - prev_assets) / prev_assets
                if asset_change < -0.20:
                    return "declining"

        # Check if spending exceeds income + gains
        total_income = (net_income or 0) + (cap_gains or 0)
        if grants > 0 and total_income < 0 and abs(total_income) > grants * 0.5:
            return "declining"

        # Strong: positive returns and healthy assets
        if net_income > 0 and assets > grants * 15:
            return "strong"

        if assets > grants * 8:
            return "stable"

        return "stable"

    def _compute_payout_compliance(self, data: Dict) -> Tuple[str, Optional[float]]:
        """Check 5% payout requirement compliance."""
        assets = data.get("fairmrktvalamt") or data.get("totassetsend") or 0
        grants = data.get("contrpdpbks") or 0
        required_dist = data.get("distribamt") or 0

        if assets <= 0:
            return "unknown", None

        payout_ratio = grants / assets

        # Use IRS distributable amount if available
        if required_dist > 0:
            if grants >= required_dist:
                return "compliant", payout_ratio
            else:
                return "under_payout", payout_ratio

        # Fall back to 5% rule estimate
        if payout_ratio >= 0.05:
            return "compliant", payout_ratio
        elif payout_ratio >= 0.03:
            return "under_payout", payout_ratio
        else:
            return "under_payout", payout_ratio

    def _compute_portfolio_profile(self, data: Dict) -> Tuple[str, float]:
        """Analyze investment portfolio composition."""
        govt = data.get("invstgovtoblig") or 0
        stocks = data.get("invstcorpstk") or 0
        bonds = data.get("invstcorpbnd") or 0
        total_sec = data.get("totinvstsec") or 0

        if total_sec <= 0:
            return "unknown", 0.0

        # Calculate allocation percentages
        govt_pct = govt / total_sec if total_sec > 0 else 0
        stock_pct = stocks / total_sec if total_sec > 0 else 0
        bond_pct = bonds / total_sec if total_sec > 0 else 0

        # Classify portfolio type
        if stock_pct > 0.7:
            portfolio_type = "aggressive"
        elif stock_pct > 0.5:
            portfolio_type = "growth"
        elif stock_pct > 0.3 or (bond_pct > 0.2 and stock_pct > 0.2):
            portfolio_type = "balanced"
        else:
            portfolio_type = "conservative"

        # Diversity score: how spread across asset classes
        # Uses normalized entropy approximation
        allocations = [a for a in [govt_pct, stock_pct, bond_pct] if a > 0]
        if len(allocations) <= 1:
            diversity = 0.2
        else:
            # Simple diversity: count of non-zero allocations / max possible
            diversity = len(allocations) / 3.0

        return portfolio_type, round(diversity, 3)

    def _compute_data_quality(self, latest: Dict, years_data: List[Dict]) -> float:
        """Score the completeness of source data (0-1.0)."""
        score = 0.0
        max_score = 0.0

        # Key financial fields
        key_fields = [
            "contrpdpbks", "fairmrktvalamt", "totassetsend",
            "netinvstinc", "distribamt"
        ]
        for f in key_fields:
            max_score += 1.0
            if latest.get(f) is not None and latest.get(f) != 0:
                score += 1.0

        # Bonus for multi-year data
        max_score += 1.0
        if len(years_data) >= 3:
            score += 1.0
        elif len(years_data) >= 2:
            score += 0.5

        # Bonus for investment detail
        max_score += 1.0
        inv_fields = ["invstgovtoblig", "invstcorpstk", "invstcorpbnd"]
        if any(latest.get(f) for f in inv_fields):
            score += 1.0

        # Bonus for BMF data
        max_score += 1.0
        if latest.get("ntee_code"):
            score += 0.5
        if latest.get("name"):
            score += 0.5

        return round(score / max_score, 3) if max_score > 0 else 0.0

    def _write_features_batch(self, conn: sqlite3.Connection, batch: List[FoundationFeatures]):
        """Write a batch of computed features to the index table."""
        query = """
            INSERT OR REPLACE INTO foundation_intelligence_index (
                ein, capacity_tier, grants_paid_latest, assets_fmv_latest,
                avg_grant_size, annual_grant_budget_estimate,
                giving_trend, giving_trend_pct, years_of_data,
                is_eligible_grantmaker, disqualification_reasons,
                accepts_applications, grants_to_individuals_only,
                is_operating_foundation, non_charity_grants,
                health_status, payout_compliance, payout_ratio,
                undistributed_income, future_grants_approved,
                portfolio_type, portfolio_diversity_score, investment_return_rate,
                primary_states, geographic_concentration,
                primary_archetype, secondary_archetypes, archetype_confidence,
                ntee_code, ntee_major_group,
                last_computed_at, computation_version,
                data_quality_score, source_tax_year
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """
        now = datetime.now().isoformat()

        rows = []
        for f in batch:
            rows.append((
                f.ein, f.capacity_tier, f.grants_paid_latest, f.assets_fmv_latest,
                f.avg_grant_size, f.annual_grant_budget_estimate,
                f.giving_trend, f.giving_trend_pct, f.years_of_data,
                1 if f.is_eligible_grantmaker else 0,
                json.dumps(f.disqualification_reasons) if f.disqualification_reasons else None,
                "unknown",  # accepts_applications (populated by PDF extraction)
                1 if f.grants_to_individuals_only else 0,
                1 if f.is_operating_foundation else 0,
                1 if f.non_charity_grants else 0,
                f.health_status, f.payout_compliance, f.payout_ratio,
                f.undistributed_income, f.future_grants_approved,
                f.portfolio_type, f.portfolio_diversity_score, f.investment_return_rate,
                json.dumps(f.primary_states) if f.primary_states else None,
                f.geographic_concentration,
                None, None, None,  # archetypes (populated by clustering step)
                f.ntee_code, f.ntee_major_group,
                now, self.version,
                f.data_quality_score, f.source_tax_year,
            ))

        conn.executemany(query, rows)

    def _build_board_network_index(self, conn: sqlite3.Connection) -> int:
        """
        Build board network index from 990-PF officer data.
        Uses the XML-parsed officer data if available, otherwise from compensation fields.
        """
        # For now, this is a placeholder that will be populated when
        # XML 990-PF parser data is integrated
        # The board_member_intelligence table in intelligence_schema.sql
        # already has the data - we just need to copy/normalize it
        try:
            count = conn.execute("""
                INSERT OR REPLACE INTO board_network_index (normalized_name, ein, title, source_tax_year)
                SELECT
                    LOWER(TRIM(member_name)) as normalized_name,
                    ein,
                    title_position,
                    CAST(strftime('%Y', created_at) AS INTEGER) as source_tax_year
                FROM board_member_intelligence
                WHERE member_name IS NOT NULL AND member_name != ''
                ON CONFLICT(normalized_name, ein) DO UPDATE SET
                    title = excluded.title,
                    source_tax_year = excluded.source_tax_year
            """).rowcount
            return count or 0
        except sqlite3.OperationalError:
            logger.info("board_member_intelligence table not available for network indexing")
            return 0

    # =========================================================================
    # PROFILE-SPECIFIC MATCHING (Per-profile, cached)
    # =========================================================================

    async def compute_profile_matches(
        self,
        profile_id: str,
        profile_ntee_codes: List[str],
        profile_states: List[str],
        profile_annual_revenue: Optional[int],
        profile_focus_areas: List[str],
        profile_mission: Optional[str] = None,
        profile_board_members: Optional[List[str]] = None,
        min_capacity_tier: str = "modest",
        limit: int = 500,
    ) -> List[ProfileMatchResult]:
        """
        Compute match scores between a profile and all eligible foundations.

        Uses precomputed foundation features for instant scoring.
        Results are cached in profile_foundation_matches table.
        """
        conn = self._get_connection()
        try:
            # Build the SQL filter based on profile criteria
            tier_order = ["mega", "major", "significant", "modest", "minimal"]
            min_tier_idx = tier_order.index(min_capacity_tier) if min_capacity_tier in tier_order else 3
            eligible_tiers = tier_order[:min_tier_idx + 1]

            placeholders = ",".join("?" * len(eligible_tiers))
            query = f"""
                SELECT *
                FROM foundation_intelligence_index
                WHERE is_eligible_grantmaker = 1
                  AND capacity_tier IN ({placeholders})
                  AND giving_trend != 'declining'
                ORDER BY grants_paid_latest DESC
                LIMIT ?
            """
            params = eligible_tiers + [limit]

            cursor = conn.execute(query, params)
            foundations = cursor.fetchall()

            # Score each foundation against the profile
            results = []
            for f in foundations:
                match = self._score_profile_match(
                    profile_id=profile_id,
                    foundation=dict(f),
                    profile_ntee_codes=profile_ntee_codes,
                    profile_states=profile_states,
                    profile_annual_revenue=profile_annual_revenue,
                    profile_focus_areas=profile_focus_areas,
                    profile_board_members=profile_board_members,
                )
                results.append(match)

            # Sort by overall match score descending
            results.sort(key=lambda m: m.overall_match_score, reverse=True)

            # Cache results
            self._cache_profile_matches(conn, results)
            conn.commit()

            return results

        finally:
            conn.close()

    def _score_profile_match(
        self,
        profile_id: str,
        foundation: Dict[str, Any],
        profile_ntee_codes: List[str],
        profile_states: List[str],
        profile_annual_revenue: Optional[int],
        profile_focus_areas: List[str],
        profile_board_members: Optional[List[str]] = None,
    ) -> ProfileMatchResult:
        """Score a single profile-foundation pair."""
        result = ProfileMatchResult(
            profile_id=profile_id,
            foundation_ein=foundation["ein"],
        )

        # 1. NTEE Alignment (0-1.0)
        f_ntee = foundation.get("ntee_code") or ""
        f_ntee_major = foundation.get("ntee_major_group") or ""
        matching_ntee = []

        for pn in profile_ntee_codes:
            if not pn:
                continue
            # Exact match
            if f_ntee and pn.upper() == f_ntee.upper():
                result.ntee_alignment_score = 1.0
                matching_ntee.append(pn)
            # Major group match (first letter)
            elif f_ntee_major and pn[0].upper() == f_ntee_major.upper():
                result.ntee_alignment_score = max(result.ntee_alignment_score, 0.6)
                matching_ntee.append(f"{pn}(group)")

        result.matching_ntee_codes = matching_ntee

        # 2. Geographic Alignment (0-1.0)
        f_states_json = foundation.get("primary_states")
        f_states = json.loads(f_states_json) if f_states_json else []
        # Also check BMF state
        f_state = foundation.get("state")
        if f_state and f_state not in f_states:
            f_states.append(f_state)

        if profile_states and f_states:
            overlap = set(s.upper() for s in profile_states) & set(s.upper() for s in f_states)
            if overlap:
                result.geographic_alignment_score = min(1.0, len(overlap) / max(1, len(profile_states)))
                result.matching_states = list(overlap)
        elif not f_states:
            # No geographic data = neutral (don't penalize)
            result.geographic_alignment_score = 0.4

        # 3. Grant Size Fit (0-1.0)
        avg_grant = foundation.get("avg_grant_size") or 0
        if profile_annual_revenue and avg_grant > 0:
            # Ideal grant is 5-30% of annual revenue
            ideal_min = profile_annual_revenue * 0.05
            ideal_max = profile_annual_revenue * 0.30
            if ideal_min <= avg_grant <= ideal_max:
                result.grant_size_fit_score = 1.0
            elif avg_grant < ideal_min:
                result.grant_size_fit_score = max(0.2, avg_grant / ideal_min)
            else:
                result.grant_size_fit_score = max(0.2, ideal_max / avg_grant)

            # Build recommended ask range
            ask_min = max(avg_grant * 0.5, ideal_min)
            ask_max = min(avg_grant * 1.5, ideal_max)
            result.recommended_ask_range = f"${ask_min:,.0f} - ${ask_max:,.0f}"
        else:
            result.grant_size_fit_score = 0.3  # Neutral when data missing

        # 4. Archetype Match (0-1.0)
        # Uses primary_archetype from foundation vs profile focus_areas
        f_archetype = foundation.get("primary_archetype") or ""
        if f_archetype and profile_focus_areas:
            # Simple keyword overlap for now (archetype clustering will improve this)
            focus_lower = [fa.lower() for fa in profile_focus_areas]
            archetype_lower = f_archetype.lower()
            if any(fa in archetype_lower or archetype_lower in fa for fa in focus_lower):
                result.archetype_match_score = 0.8
                result.matching_archetypes = [f_archetype]
        # No archetype data = use NTEE alignment as proxy
        if result.archetype_match_score == 0.0 and result.ntee_alignment_score > 0:
            result.archetype_match_score = result.ntee_alignment_score * 0.5

        # 5. Giving Trend Score (0-1.0)
        trend = foundation.get("giving_trend") or "unknown"
        trend_scores = {
            "growing": 1.0,
            "stable": 0.7,
            "new": 0.6,
            "erratic": 0.3,
            "declining": 0.1,
            "unknown": 0.4,
        }
        result.giving_trend_score = trend_scores.get(trend, 0.4)

        # 6. Board Connection Score (0-1.0)
        # TODO: Cross-reference profile board members with board_network_index
        result.board_connection_score = 0.0

        # Composite weighted score
        result.overall_match_score = round(
            result.ntee_alignment_score * self.MATCH_WEIGHTS["ntee_alignment"]
            + result.geographic_alignment_score * self.MATCH_WEIGHTS["geographic_alignment"]
            + result.grant_size_fit_score * self.MATCH_WEIGHTS["grant_size_fit"]
            + result.archetype_match_score * self.MATCH_WEIGHTS["archetype_match"]
            + result.giving_trend_score * self.MATCH_WEIGHTS["giving_trend"]
            + result.board_connection_score * self.MATCH_WEIGHTS["board_connection"],
            4,
        )

        return result

    def _cache_profile_matches(self, conn: sqlite3.Connection, matches: List[ProfileMatchResult]):
        """Cache profile match results for future instant retrieval."""
        if not matches:
            return

        query = """
            INSERT OR REPLACE INTO profile_foundation_matches (
                profile_id, foundation_ein,
                overall_match_score, ntee_alignment_score, geographic_alignment_score,
                grant_size_fit_score, archetype_match_score, giving_trend_score,
                board_connection_score,
                matching_ntee_codes, matching_states, matching_archetypes,
                recommended_ask_range,
                computed_at, is_stale
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """
        now = datetime.now().isoformat()
        rows = []
        for m in matches:
            rows.append((
                m.profile_id, m.foundation_ein,
                m.overall_match_score, m.ntee_alignment_score, m.geographic_alignment_score,
                m.grant_size_fit_score, m.archetype_match_score, m.giving_trend_score,
                m.board_connection_score,
                json.dumps(m.matching_ntee_codes),
                json.dumps(m.matching_states),
                json.dumps(m.matching_archetypes),
                m.recommended_ask_range,
                now,
            ))

        conn.executemany(query, rows)

    # =========================================================================
    # QUERY INTERFACE (For downstream tools)
    # =========================================================================

    def get_top_matches_for_profile(
        self,
        profile_id: str,
        limit: int = 50,
        min_score: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve cached profile matches with foundation details.
        Returns enriched results joining match scores with foundation index.
        """
        conn = self._get_connection()
        try:
            query = """
                SELECT
                    m.profile_id,
                    m.foundation_ein,
                    m.overall_match_score,
                    m.ntee_alignment_score,
                    m.geographic_alignment_score,
                    m.grant_size_fit_score,
                    m.archetype_match_score,
                    m.giving_trend_score,
                    m.board_connection_score,
                    m.matching_ntee_codes,
                    m.matching_states,
                    m.recommended_ask_range,
                    fi.capacity_tier,
                    fi.grants_paid_latest,
                    fi.assets_fmv_latest,
                    fi.giving_trend,
                    fi.health_status,
                    fi.payout_compliance,
                    fi.ntee_code,
                    b.name as foundation_name,
                    b.state as foundation_state,
                    b.city as foundation_city
                FROM profile_foundation_matches m
                JOIN foundation_intelligence_index fi ON m.foundation_ein = fi.ein
                LEFT JOIN bmf_organizations b ON m.foundation_ein = b.ein
                WHERE m.profile_id = ?
                  AND m.overall_match_score >= ?
                  AND m.is_stale = 0
                ORDER BY m.overall_match_score DESC
                LIMIT ?
            """
            cursor = conn.execute(query, (profile_id, min_score, limit))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def invalidate_profile_matches(self, profile_id: str):
        """Mark all cached matches for a profile as stale (e.g., after profile update)."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE profile_foundation_matches SET is_stale = 1 WHERE profile_id = ?",
                (profile_id,),
            )
            conn.commit()
        finally:
            conn.close()

    def get_index_stats(self) -> Dict[str, Any]:
        """Get summary statistics of the foundation intelligence index."""
        conn = self._get_connection()
        try:
            stats = {}

            # Total foundations indexed
            row = conn.execute("SELECT COUNT(*) as cnt FROM foundation_intelligence_index").fetchone()
            stats["total_indexed"] = row["cnt"] if row else 0

            # Eligible vs disqualified
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM foundation_intelligence_index WHERE is_eligible_grantmaker = 1"
            ).fetchone()
            stats["eligible"] = row["cnt"] if row else 0
            stats["disqualified"] = stats["total_indexed"] - stats["eligible"]

            # Capacity distribution
            cursor = conn.execute(
                "SELECT capacity_tier, COUNT(*) as cnt FROM foundation_intelligence_index GROUP BY capacity_tier"
            )
            stats["capacity_distribution"] = {row["capacity_tier"]: row["cnt"] for row in cursor}

            # Trend distribution
            cursor = conn.execute(
                "SELECT giving_trend, COUNT(*) as cnt FROM foundation_intelligence_index GROUP BY giving_trend"
            )
            stats["trend_distribution"] = {row["giving_trend"]: row["cnt"] for row in cursor}

            # Health distribution
            cursor = conn.execute(
                "SELECT health_status, COUNT(*) as cnt FROM foundation_intelligence_index GROUP BY health_status"
            )
            stats["health_distribution"] = {row["health_status"]: row["cnt"] for row in cursor}

            return stats
        finally:
            conn.close()


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

async def main():
    """Run foundation preprocessing from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Foundation Preprocessing Tool")
    parser.add_argument(
        "--db", default="data/nonprofit_intelligence.db",
        help="Path to nonprofit intelligence database"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000,
        help="Batch size for processing"
    )
    parser.add_argument(
        "--stats-only", action="store_true",
        help="Show index stats without reprocessing"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    preprocessor = FoundationPreprocessor(args.db)

    if args.stats_only:
        stats = preprocessor.get_index_stats()
        print(json.dumps(stats, indent=2))
        return

    print("Starting foundation preprocessing...")
    result = await preprocessor.run_full_preprocessing(batch_size=args.batch_size)

    print(f"\nPreprocessing Results:")
    print(f"  Foundations processed: {result.foundations_processed}")
    print(f"  Eligible grantmakers: {result.foundations_eligible}")
    print(f"  Disqualified: {result.foundations_disqualified}")
    print(f"  Board members indexed: {result.board_members_indexed}")
    print(f"  Execution time: {result.execution_time_ms:.0f}ms")
    print(f"\n  Capacity Distribution: {json.dumps(result.capacity_distribution, indent=4)}")
    print(f"  Giving Trends: {json.dumps(result.trend_distribution, indent=4)}")
    print(f"  Health Status: {json.dumps(result.health_distribution, indent=4)}")

    if result.errors:
        print(f"\n  Errors ({len(result.errors)}):")
        for e in result.errors[:10]:
            print(f"    - {e}")


if __name__ == "__main__":
    asyncio.run(main())
