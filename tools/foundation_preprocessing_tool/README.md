# Foundation Preprocessing Tool

Monthly batch preprocessing of foundation intelligence for instant profile-to-foundation matching.

## Architecture

```
UNIVERSAL (run monthly, all profiles benefit)
├── FoundationPreprocessor      → foundation_intelligence_index table
│   ├── Compliance pre-filter   → is_eligible_grantmaker flag
│   ├── Capacity tier scoring   → mega/major/significant/modest/minimal
│   ├── Giving trend analysis   → growing/stable/declining/erratic
│   ├── Financial health        → strong/stable/declining/distressed
│   ├── Portfolio profiling     → conservative/balanced/growth/aggressive
│   └── Board network index     → board_network_index table
│
├── GrantArchetypeClustering    → 30 giving archetypes
│   ├── Rule-based keywords     → $0 cost
│   └── NTEE code mapping       → foundation → archetype assignment
│
└── PDFNarrativeExtractor       → foundation_narratives table
    ├── Mission statements      → from Part I
    ├── Application process     → from Part XV
    └── Program descriptions    → from Part XVI

PER-PROFILE (run on profile create/update, cached)
└── compute_profile_matches()   → profile_foundation_matches table
    ├── NTEE alignment          → 30% weight
    ├── Geographic overlap      → 20% weight
    ├── Grant size fit          → 20% weight
    ├── Archetype match         → 15% weight
    ├── Giving trend bonus      → 10% weight
    └── Board connections       → 5% weight
```

## Usage

### Monthly Batch Preprocessing
```python
from tools.foundation_preprocessing_tool.app.foundation_preprocessor import FoundationPreprocessor

preprocessor = FoundationPreprocessor("data/nonprofit_intelligence.db")
stats = await preprocessor.run_full_preprocessing(batch_size=1000)
```

### Profile Matching
```python
matches = await preprocessor.compute_profile_matches(
    profile_id="profile_youth_education_001",
    profile_ntee_codes=["B25", "P20"],
    profile_states=["VA", "MD", "DC"],
    profile_annual_revenue=500000,
    profile_focus_areas=["youth education", "after school programs"],
    profile_mission="Empowering underserved youth through education",
    min_capacity_tier="significant",
    limit=200,
)
```

### PDF Narrative Extraction
```python
from tools.foundation_preprocessing_tool.app.pdf_narrative_extractor import PDFNarrativeExtractor

extractor = PDFNarrativeExtractor("data/nonprofit_intelligence.db")
result = await extractor.extract_from_pdf_url(
    ein="123456789",
    pdf_url="https://projects.propublica.org/nonprofits/download-filing/123456789",
    tax_year=2023,
)
extractor.cache_narrative(result)
```

### CLI
```bash
python -m tools.foundation_preprocessing_tool.app.foundation_preprocessor --db data/nonprofit_intelligence.db
python -m tools.foundation_preprocessing_tool.app.foundation_preprocessor --db data/nonprofit_intelligence.db --stats-only
```

## Cost

| Component | Cost | Frequency |
|-----------|------|-----------|
| Foundation Intelligence Index | $0 | Monthly |
| Grant Archetype Clustering | $0 | Quarterly |
| PDF Narrative Extraction | ~$0.01/PDF | On-demand, cached |
| Profile Matching | $0 | On profile change |

## Database Tables

- `foundation_intelligence_index` - Precomputed foundation features
- `foundation_narratives` - Extracted PDF narrative content
- `grant_archetypes` - 30 giving archetype definitions
- `profile_foundation_matches` - Cached profile-to-foundation scores
- `board_network_index` - Cross-foundation board member connections
