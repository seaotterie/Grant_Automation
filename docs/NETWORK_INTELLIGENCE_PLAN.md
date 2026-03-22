# Network Intelligence Enhancement Plan — "ConnectionGraph"

## Vision

Transform Catalynx's network intelligence from a per-opportunity analysis tool into a **persistent, LinkedIn-style relationship graph** that continuously maps board members, officers, program contacts, and influencers across the nonprofit/foundation ecosystem. The core insight: **who you know matters as much as what you do** when pursuing funding opportunities.

---

## Current State Assessment

### What Works Well
- **Tool 12 (Network Intelligence)** profiles board members with centrality metrics and connection pathways
- **Tool 14 (Grantee Bundling)** identifies co-funding patterns via Jaccard similarity
- **NetworkGraphBuilder** ingests leadership from 990 filings and web scraping into `network_memberships`
- **Normalized schema** already defines `people`, `organization_roles`, `board_connections`, and influence metrics tables
- **Tax filing extraction** provides high-confidence officer/board data from 990/990-PF XML

### Key Gaps
1. **No persistent people database** — `network_memberships` is flat; the normalized `people` table exists in schema but isn't populated
2. **No person deduplication** — same person across multiple orgs appears as separate entries (only `person_hash` on name)
3. **No relationship strength decay** — connections don't weaken over time as people leave boards
4. **No proactive connection discovery** — system only maps connections when a user runs analysis
5. **No "warm introduction" pathways** — can't trace "your board member → shared board → funder program officer"
6. **No contact enrichment** — no LinkedIn URLs, emails, or phone numbers tracked systematically
7. **No network visualization** — data exists but no interactive graph UI
8. **No competitive intelligence** — can't see which peer nonprofits share your network

---

## Phased Implementation Plan

### Phase 1: People Database & Deduplication Engine
**Priority: CRITICAL | Effort: Large | Dependencies: None**

Everything else depends on having a clean, deduplicated people registry.

#### 1A. Populate the `people` Table
- Migrate existing `network_memberships` records into the normalized `people` + `organization_roles` tables
- Build an ETL pipeline that extracts officers from all cached 990/990-PF XML filings
- Parse `web_enhanced_data.leadership` from existing profiles into the people table

#### 1B. Person Deduplication Service
Create `src/network/person_deduplication.py`:
- **Fuzzy name matching** using normalized names (strip prefixes/suffixes, standardize Jr/Sr/III)
- **Title-based disambiguation** — "John Smith, Treasurer at Org A" vs "John Smith, CEO at Org B" may be same person
- **Affiliation clustering** — if two "Jane Doe" entries share any organization, likely same person
- **Confidence scoring** — high (exact name + shared org), medium (fuzzy name + same city), low (fuzzy name only)
- **Merge UI** — surface potential duplicates for user confirmation before merging

#### 1C. Data Quality Scoring
- Score each person record: how many sources confirm this person? (990 filing = high, web scrape = medium, user-entered = varies)
- Track `last_verified_at` from most recent filing year
- Flag stale records (officer not in latest filing)

**New files:**
```
src/network/person_deduplication.py
src/network/people_etl.py
src/web/routers/people.py
```

**Schema additions:**
```sql
-- Deduplication tracking
person_merge_history (
  merge_id, kept_person_id, merged_person_id,
  confidence_score, merge_reason, merged_by, merged_at
)
```

---

### Phase 2: Relationship Strength & Temporal Modeling
**Priority: HIGH | Effort: Medium | Dependencies: Phase 1**

Connections aren't binary — they have strength, recency, and context.

#### 2A. Enhanced Connection Strength Model
Extend `board_connections` with a multi-factor strength score:

| Factor | Weight | Logic |
|--------|--------|-------|
| Concurrent service | 0.30 | Both currently serving at shared org |
| Recency | 0.25 | Exponential decay from last shared service year |
| Duration overlap | 0.15 | Years of concurrent board service |
| Role proximity | 0.15 | Both executive = strong; one board + one staff = moderate |
| Interaction frequency | 0.15 | Board size proxy (small board = more interaction) |

#### 2B. Temporal Network Snapshots
- Track `start_date` and `end_date` for every `organization_role`
- Build yearly network snapshots so users can see "who was connected to whom in 2023"
- Detect **trending connections** — relationships strengthening over time (person joining more shared boards)

#### 2C. Relationship Type Taxonomy
Expand beyond board connections:
- `BOARD_COLLEAGUE` — served on same board
- `REPORTING_CHAIN` — officer reporting to executive director
- `GRANT_RELATIONSHIP` — program officer who approved grants to an org
- `CO_FUNDER` — officers at foundations that co-fund same grantees
- `ALUMNI` — formerly at same organization (weaker, still valuable)
- `SECTOR_PEER` — officers at organizations in same NTEE code

**New/modified files:**
```
src/network/connection_strength.py    # multi-factor scoring
src/network/temporal_network.py       # yearly snapshots
tools/network_intelligence_tool/app/network_models.py  # extended enums
```

---

### Phase 3: Warm Introduction Pathway Engine
**Priority: HIGH | Effort: Medium | Dependencies: Phase 1, Phase 2**

The killer feature — "How do I get an introduction to the Gates Foundation program director?"

#### 3A. Multi-Hop Path Discovery
Create `tools/connection_pathway_tool/`:
- Given: seeker's board/staff and a target funder
- Find all paths of length 1–4 hops between any seeker person and any funder person
- Rank paths by: **aggregate connection strength** (product of edge strengths along path)
- Filter by: relationship recency, person influence scores

#### 3B. Introduction Strategy Generator
For each viable pathway, generate AI-powered cultivation recommendations:
- **Direct connection (1 hop):** "Your board chair Sarah Chen served with their program director at United Way 2019–2022. Recommend: personal email referencing shared United Way experience."
- **2-hop connection:** "Your ED knows Maria Lopez (Nonprofit Alliance board), who sits on the target foundation's advisory committee. Recommend: ask Maria for a warm introduction at the upcoming sector conference."
- **Cold but strategic (no path):** "No direct connections found. Recommend: attend their next grantee convening, or recruit [suggested board member] who has foundation connections."

#### 3C. Pathway Scoring in Opportunity Pipeline
Integrate pathway scores into the opportunity scoring model:
- Add `network_proximity_score` (0–100) to `ScoringResult` dimensions
- Weight: strong direct connection = 85–100, 2-hop = 60–80, 3-hop = 30–55, no path = 0–20
- Surface in opportunity cards: "2 connection pathways found" badge

**New tool:**
```
tools/connection_pathway_tool/
├── 12factors.toml
├── app/
│   ├── __init__.py
│   ├── pathway_tool.py        # PathwayDiscoveryTool(BaseTool)
│   ├── pathway_models.py      # IntroductionPathway, CultivationStrategy
│   └── pathway_scorer.py      # Multi-hop path ranking
└── tests/
    └── test_pathway_tool.py
```

---

### Phase 4: Contact & Enrichment Intelligence
**Priority: MEDIUM | Effort: Medium | Dependencies: Phase 1**

Build the "contact card" layer on top of the people database.

#### 4A. Contact Information Aggregation
Extend the `people` table with enrichment data:
- **From 990 filings:** Address (Part VII), compensation, hours/week
- **From web scraping (Tool 25):** LinkedIn URL, organization bio page, email patterns
- **From ProPublica API:** Cross-reference officer names with filing history

#### 4B. Program Officer Intelligence
For foundations specifically, identify the **grant decision-makers**:
- Parse 990-PF Part XV grant descriptions for program officer names
- Cross-reference with Part VIII officer list to identify who manages which program areas
- Build `program_officer_assignments` table linking officers to grant categories

#### 4C. Contact Reachability Scoring
Score how "reachable" a target contact is:
- Has a known warm introduction path? (+40)
- Has a public-facing email/LinkedIn? (+20)
- Regularly attends sector conferences? (+15)
- Organization has open grant inquiry process? (+25)

**New files:**
```
src/network/contact_enrichment.py
src/network/program_officer_tracker.py
```

**Schema additions:**
```sql
program_officer_assignments (
  officer_id REFERENCES people(id),
  foundation_ein, program_area, grant_category,
  estimated_budget_authority, first_seen_year, last_seen_year
)

contact_methods (
  person_id REFERENCES people(id),
  method_type, -- email, linkedin, phone, twitter
  method_value, is_verified, source, discovered_at
)
```

---

### Phase 5: Network Visualization & Interactive Explorer
**Priority: MEDIUM | Effort: Large | Dependencies: Phases 1–3**

Make the relationship graph visible and interactive.

#### 5A. Network Graph Visualization
Add a `/network/explorer` page to the web UI:
- **Force-directed graph** using D3.js or vis.js
- Nodes = people (sized by influence) and organizations (colored by type: seeker/funder/peer)
- Edges = connections (thickness = strength, color = type)
- Click a node to see: person card, all affiliations, connection paths to seeker

#### 5B. Pathway Visualization
When viewing an opportunity, show the introduction pathway visually:
- Highlight the shortest/strongest paths from seeker board to funder contacts
- Animate the "hop" sequence: Your Board → Shared Org → Their Program Officer

#### 5C. Network Health Dashboard
Profile-level dashboard showing:
- **Network reach:** How many funders are within 1/2/3 hops
- **Network gaps:** High-value funders with zero connections (recruitment opportunities)
- **Network growth:** Connections added this quarter vs. last
- **Board effectiveness:** Which board members contribute the most network value

**New files:**
```
src/web/routers/network_explorer.py
src/web/static/js/network-graph.js
src/web/templates/network_explorer.html
```

---

### Phase 6: Competitive & Strategic Intelligence
**Priority: LOWER | Effort: Medium | Dependencies: Phases 1–3**

Understand the competitive landscape through network analysis.

#### 6A. Peer Organization Network Mapping
- Identify nonprofits that share board members with the same funders you're targeting
- Surface: "3 other nonprofits in your space have board connections to the Ford Foundation"
- Distinguish: complementary peers (potential partners) vs. direct competitors

#### 6B. Board Recruitment Intelligence
Analyze network gaps and recommend board candidates:
- "You have zero connections to health-focused foundations. Adding someone from [list] would open 12 new pathways."
- Score potential board members by: network reach gained, sector expertise, geographic coverage
- Track a "wish list" of target board recruits

#### 6C. Funder Relationship Lifecycle
Track the progression of funder relationships:
- **Unknown** → **Mapped** (connections identified) → **Introduced** (warm intro made) → **Cultivating** (in dialogue) → **Applied** → **Funded/Declined**
- Integrate with opportunity pipeline stages
- AI-generated next-step recommendations at each stage

**New tool:**
```
tools/board_recruitment_intelligence_tool/
├── 12factors.toml
├── app/
│   ├── board_recruitment_tool.py
│   ├── recruitment_models.py
│   └── gap_analyzer.py
└── tests/
```

---

## Implementation Priority Matrix

```
                    HIGH VALUE
                        │
   Phase 3 (Pathways)  │  Phase 1 (People DB)
   Phase 5A (Viz)      │  Phase 2 (Strength)
                        │
  ──────────────────────┼──────────────────────
                        │
   Phase 6B (Recruit)   │  Phase 4 (Contacts)
   Phase 6C (Lifecycle) │  Phase 6A (Competitors)
                        │
                    LOW VALUE
        HIGH EFFORT          LOW EFFORT
```

**Recommended order:** 1 → 2 → 3 → 4 → 5A → 6B → 5B → 5C → 6A → 6C

---

## Technical Considerations

### Data Privacy
- Board member data from 990 filings is **public record** — no privacy concern
- Web-scraped contact info should be flagged with source and used responsibly
- Provide opt-out mechanism if an individual requests removal
- Never store or display SSNs, personal financial data, or non-public PII

### Performance
- The people table could grow to 500K+ records from 990 parsing
- Use PostgreSQL-style indexing on `normalized_name`, `person_hash`, `org_ein`
- Pre-compute connection paths for active profiles (cache in `board_connections`)
- Limit path discovery to 4 hops max (combinatorial explosion beyond that)

### AI Cost Estimates
| Feature | Model | Est. Cost |
|---------|-------|-----------|
| Person deduplication (batch) | Haiku | $0.001/pair |
| Introduction strategy generation | Sonnet | $0.03/pathway |
| Board recruitment recommendations | Sonnet | $0.05/analysis |
| Network gap analysis | Haiku | $0.01/profile |

### Integration Points
- **Tool 1 (Screening):** Add network_proximity as a screening dimension
- **Tool 2 (Deep Intelligence):** Enrich reports with connection pathways
- **Tool 20 (Scorer):** Add network dimension to multi-dimensional scoring
- **Tool 25 (Web Intelligence):** Enhanced leadership scraping for contact enrichment

---

## Success Metrics

1. **Coverage:** % of funders in pipeline with at least one mapped connection pathway
2. **Pathway quality:** Average connection strength of top pathway per opportunity
3. **Conversion lift:** Win rate for opportunities with strong network connections vs. cold applications
4. **Network growth:** New people/connections added per month
5. **User engagement:** % of opportunities where user views network insights before applying

---

## Open Questions for Discussion

1. **Scope of initial people ETL:** Process all 2M+ records in nonprofit_intelligence.db, or start with funders linked to active profiles only?
2. **Person deduplication threshold:** How aggressive should auto-merging be? Conservative (high confidence only) vs. aggressive (surface more potential matches)?
3. **Board recruitment feature:** Should this be a standalone tool or integrated into the profile dashboard?
4. **Network visualization library:** D3.js (maximum flexibility) vs. vis.js (easier) vs. Cytoscape.js (best for biological/network graphs)?
5. **Competitive intelligence sensitivity:** How much competitor information should be surfaced? Some users may find it uncomfortable.
