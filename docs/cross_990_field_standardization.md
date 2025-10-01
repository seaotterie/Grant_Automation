# Cross-990 Field Standardization for Network Analysis

## Purpose
Standardize officer and grant fields across 990, 990-PF, and 990-EZ forms to enable:
- Board member connection mapping between grantors and grantees
- Network analysis of relationships between foundations and nonprofits
- Consistent data structure for AI-powered relationship discovery

## Officer/Board Member Standardization

### Core Identity Fields (Required for Network Analysis)
| Standardized Field | 990 (RegularNonprofitOfficer) | 990-PF (FoundationOfficer) | 990-EZ | Notes |
|-------------------|-------------------------------|---------------------------|---------|-------|
| `ein` | ✓ | ✓ | ✓ | Organization identifier |
| `person_name` | ✓ (person_name) | ✓ (person_name) | ✓ | **PRIMARY KEY** for board matching |
| `title` | ✓ (title) | ✓ (title) | ✓ | Role normalization needed |
| `tax_year` | ✓ | ✓ | ✓ | Temporal context |
| `data_source` | ✓ | ✓ | ✓ | Form provenance |

### Role Identification Fields (Critical for Network Analysis)
| Standardized Field | 990 | 990-PF | 990-EZ | Purpose |
|-------------------|-----|--------|---------|---------|
| `is_officer` | ✓ | ✓ | ✓ | Executive decision maker |
| `is_director` | ✓ (is_individual_trustee) | ✓ (is_director) | ✓ | Board voting member |
| `is_trustee` | ✓ (is_individual_trustee/institutional_trustee) | Combine with is_director | ✓ | Fiduciary role |
| `is_key_employee` | ✓ | Map to compensation check | ✓ | Operational influence |

### Compensation Fields (Network Influence Indicators)
| Standardized Field | 990 | 990-PF | 990-EZ | Purpose |
|-------------------|-----|--------|---------|---------|
| `total_compensation` | reportable_comp_from_org | compensation | ✓ | Relationship strength indicator |
| `average_hours_per_week` | ✓ | ✓ | ✓ | Engagement level |
| `other_compensation` | other_compensation | expense_account_allowance | ✓ | Additional relationship depth |

### Network Analysis Enhancement Fields (New)
Add to all forms:
- `normalized_person_name`: Cleaned name for fuzzy matching (UPPERCASE, no punctuation)
- `role_category`: Standardized role (Executive, Board, Staff, Volunteer)
- `influence_score`: Calculated from compensation + hours + role flags
- `connection_match_key`: Hash of normalized_person_name for fast lookup

## Grant/Assistance Standardization

### Core Grant Fields (Required for Grantor-Grantee Mapping)
| Standardized Field | 990 (Form990GrantRecord) | 990-PF (FoundationGrant) | 990-EZ | Notes |
|-------------------|--------------------------|-------------------------|---------|-------|
| `ein` | ✓ | ✓ | ✓ | Grantor EIN |
| `recipient_name` | ✓ | ✓ | ✓ | **GRANTEE** organization name |
| `recipient_ein` | ✓ | Add extraction | Add | **KEY** for network mapping |
| `grant_amount` | ✓ | ✓ | ✓ | Relationship strength |
| `grant_purpose` | ✓ | ✓ | ✓ | Funding area alignment |
| `tax_year` | ✓ | ✓ | ✓ | Temporal context |

### Recipient Identification Fields (Network Discovery)
| Standardized Field | 990 | 990-PF | 990-EZ | Purpose |
|-------------------|-----|--------|---------|---------|
| `recipient_ein` | ✓ | **ADD** (extract from XML) | **ADD** | Direct org-to-org link |
| `recipient_type` | assistance_type | recipient_type | Add | Organization vs Individual |
| `recipient_address` | ✓ | ✓ | Add | Geographic matching |
| `relationship_description` | ✓ | recipient_relationship | Add | Connection type |

### Grant Intelligence Fields (Relationship Context)
| Standardized Field | 990 | 990-PF | 990-EZ | Purpose |
|-------------------|-----|--------|---------|---------|
| `foundation_status_of_recipient` | Add | ✓ | Add | 501(c)(3) verification |
| `grant_monitoring_procedures` | Add | ✓ | Add | Relationship formality |
| `schedule_part` | ✓ | ✓ | ✓ | Data provenance |

### Network Analysis Enhancement Fields (New)
Add to all forms:
- `normalized_recipient_name`: Cleaned name for matching
- `multi_year_grant`: Boolean flag for ongoing relationships
- `grant_amount_percentile`: Size relative to grantor capacity
- `connection_match_key`: Hash for fast org-to-org lookup

## Implementation Priority

### Phase 2A: Officer Field Standardization (CURRENT)
1. **Add normalized_person_name** to all three officer classes
2. **Add role_category** enum (Executive, Board, Staff, Volunteer)
3. **Standardize is_director/is_trustee** across forms
4. **Add influence_score** calculation in extractors

### Phase 2B: Grant Field Standardization
1. **Add recipient_ein extraction** to 990-PF parser (critical missing field)
2. **Add normalized_recipient_name** to all three grant classes
3. **Standardize recipient_type** values across forms
4. **Add connection_match_key** for fast lookup

### Phase 2C: Network Matching Tool (Future)
1. Create board member connection mapping tool
2. Input: Profile nonprofit EIN (grantee)
3. Process:
   - Extract board members from profile's 990/990-EZ
   - Normalize names with fuzzy matching
   - Search 990-PF FoundationOfficer records for name matches
   - Cross-reference with FoundationGrant records (grantor → profile grantee)
4. Output: Ranked list of foundations with board connections

## Standardized Role Categories

### Role Category Mapping
```python
ROLE_CATEGORIES = {
    'Executive': ['President', 'CEO', 'CFO', 'COO', 'Executive Director', 'President/CEO'],
    'Board': ['Chair', 'Vice Chair', 'Director', 'Trustee', 'Board Member', 'Secretary', 'Treasurer'],
    'Staff': ['Manager', 'Coordinator', 'Administrator', 'Officer'],
    'Volunteer': ['Volunteer', 'Committee Member', 'Advisory Board']
}
```

## Name Normalization Algorithm

### Standardized Cleaning Process
```python
def normalize_person_name(name: str) -> str:
    """
    Normalize person name for fuzzy matching across 990 forms

    Examples:
    - "Christine M. Connolly" → "CHRISTINE M CONNOLLY"
    - "CHRISTINE M CONNOLLY" → "CHRISTINE M CONNOLLY"
    - "Dr. Major Warner" → "MAJOR WARNER"
    - "John W. McCarthy III" → "JOHN W MCCARTHY III"
    """
    # Remove titles
    titles = ['Dr', 'Dr.', 'MD', 'PhD', 'Esq', 'Jr', 'Jr.', 'Sr', 'Sr.']
    # Remove punctuation
    # Convert to uppercase
    # Normalize whitespace
    # Return hash or cleaned string
    pass
```

## Benefits for Network Analysis

1. **Board Member Connection Mapping**
   - Match person_name across 990 (grantee) and 990-PF (grantor) forms
   - Identify foundations where profile board members also serve
   - Prioritize grant opportunities based on board connections

2. **Grant Relationship Discovery**
   - Link recipient_ein in 990-PF grants to profile EIN
   - Identify existing grantor relationships
   - Find similar recipients for peer analysis

3. **Influence Scoring**
   - Combine role flags + compensation + hours
   - Rank board members by decision-making power
   - Prioritize connections to high-influence individuals

4. **Multi-Dimensional Matching**
   - Direct board overlap (same person_name)
   - Indirect connections (board member of grantee on board of grantor)
   - Historical patterns (repeat grants, relationship evolution)

## Data Quality Requirements

### For Successful Network Analysis
- **Name consistency**: Person names must be extracted accurately from XML
- **EIN accuracy**: Both grantor and recipient EINs required
- **Role clarity**: Officer/director flags must be set correctly
- **Temporal data**: Tax years enable relationship timeline analysis

### Known Data Gaps (To Address)
1. **990-PF missing recipient_ein**: Need to extract from XML if available
2. **Name variations**: Middle initials, suffixes, nicknames need normalization
3. **Role ambiguity**: "Director" could be board member or staff position
4. **Multi-year relationships**: Currently single-year snapshots only