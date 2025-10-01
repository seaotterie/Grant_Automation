# Catalynx Data Transformation Pipeline

Comprehensive guide for the Catalynx data transformation system that converts scraped JSON data into normalized database records for efficient analytical operations.

## Overview

The data transformation pipeline handles:
- Web scraping results from frontend
- Board member data from database JSON fields
- Tax filing verification data
- Name parsing and normalization
- Cross-source deduplication
- Data validation and quality scoring
- Normalized database storage

## Architecture

### Core Components

1. **Pydantic Models** (`src/data_transformation/models.py`)
   - Input models for raw scraped data
   - Output models for normalized records
   - Configuration and result models
   - Comprehensive validation rules

2. **Transformation Service** (`src/data_transformation/transformation_service.py`)
   - Name parsing and normalization
   - Cross-source deduplication
   - Data validation and quality scoring
   - Conflict resolution

3. **Database Integration** (`src/data_transformation/database_integration.py`)
   - Normalized table management
   - Batch insert operations
   - Data migration and update detection
   - Performance optimization

4. **Main Service** (`src/data_transformation/main_service.py`)
   - High-level orchestration
   - Error handling and recovery
   - Integration with existing workflow
   - Performance monitoring

## Usage Examples

### Basic Usage

```python
from src.data_transformation import CatalynxDataTransformer
from src.database.database_manager import DatabaseManager

# Initialize
db_manager = DatabaseManager()
transformer = CatalynxDataTransformer(db_manager)

# Transform profile data
result = transformer.transform_profile_data(
    profile_id="profile_123",
    web_scraping_results={
        "extracted_info": {
            "leadership": [
                {
                    "name": "Dr. John Smith Jr.",
                    "title": "Executive Director", 
                    "biography": "20 years of nonprofit experience",
                    "quality_score": 85.0
                }
            ],
            "programs": [
                {
                    "name": "Community Health Initiative",
                    "description": "Direct health services for underserved populations",
                    "type": "direct_service",
                    "quality_score": 90.0
                }
            ],
            "contact_info": [
                {
                    "type": "email",
                    "value": "info@example.org",
                    "label": "General Contact",
                    "quality_score": 95.0
                }
            ]
        },
        "successful_scrapes": ["https://example.org"],
        "total_quality_score": 90.0
    },
    board_members_json=[
        {
            "name": "Jane Doe",
            "title": "Board Chair",
            "background": "Former nonprofit executive",
            "committees": ["Executive", "Finance"]
        }
    ]
)

# Check results
if result.success:
    print(f"Transformed {result.statistics.total_records_processed} records")
    print(f"Found {result.statistics.duplicates_found} duplicates")
    print(f"Data quality score: {result.statistics.data_quality_score}%")
else:
    print(f"Transformation failed: {len(result.validation_errors)} errors")
```

### Transform from Existing Database Data

```python
# Transform using existing profile JSON fields
result = transformer.transform_profile_from_database("profile_123")

if result.success:
    print(f"Successfully transformed existing data")
    print(f"People: {len(result.people)}")
    print(f"Roles: {len(result.roles)}")
    print(f"Programs: {len(result.programs)}")
    print(f"Contacts: {len(result.contacts)}")
```

### Get Transformation Summary

```python
# Get comprehensive transformation summary
summary = transformer.get_transformation_summary("profile_123")

print(f"Profile: {summary['profile_name']}")
print(f"Total transformations: {summary['total_transformations']}")
print(f"Data quality score: {summary['data_quality']['quality_score']}%")
print(f"Normalized records: {summary['normalized_records']}")

if summary['last_transformation']:
    last = summary['last_transformation']
    print(f"Last transformation: {last['date']} (Success: {last['success']})")
```

### Data Quality Monitoring

```python
# Get system-wide data quality report
report = transformer.get_data_quality_report()

print(f"Generated: {report['generated_at']}")
print(f"Success rate: {report['transformation_statistics']['success_rate_percent']}%")
print(f"Profile coverage: {report['profile_coverage']['web_data_coverage_percent']}%")

# Quality metrics by data type
metrics = report['data_quality_metrics']
print(f"People: {metrics['people']['total_count']} (avg confidence: {metrics['people']['avg_confidence']})")
print(f"Programs: {metrics['programs']['total_count']} (avg confidence: {metrics['programs']['avg_confidence']})")
```

### Configuration and Validation

```python
from src.data_transformation.models import (
    TransformationConfig, NameParsingConfig, DeduplicationConfig
)

# Custom configuration
config = TransformationConfig(
    name_parsing=NameParsingConfig(
        strip_titles=True,
        handle_nicknames=True,
        min_name_length=2
    ),
    deduplication=DeduplicationConfig(
        fuzzy_match_threshold=0.85,
        merge_strategy="highest_quality",
        auto_merge_duplicates=False
    ),
    enable_fuzzy_matching=True,
    batch_size=100
)

# Initialize with custom config
transformer = CatalynxDataTransformer(db_manager, config)

# Validate configuration
validation = transformer.validate_configuration()
if not validation['config_valid']:
    print(f"Configuration warnings: {validation['warnings']}")
    print(f"Recommendations: {validation['recommendations']}")
```

## Data Models

### Input Models

#### ScrapedLeadership
```python
class ScrapedLeadership(BaseModel):
    name: str  # Full name (required)
    title: Optional[str]  # Position/title
    biography: Optional[str]  # Biography text
    quality_score: float  # 0-100 scraping quality score
```

#### ScrapedProgram
```python
class ScrapedProgram(BaseModel):
    name: str  # Program name (required)
    description: Optional[str]  # Program description
    type: Optional[str]  # Program type/category
    quality_score: float  # 0-100 scraping quality score
```

#### ScrapedContact
```python
class ScrapedContact(BaseModel):
    type: ContactType  # email, phone, website, etc.
    value: str  # Contact value (required)
    label: Optional[str]  # Contact label/description
    quality_score: float  # 0-100 scraping quality score
```

### Output Models

#### Person
```python
class Person(BaseModel):
    parsed_name: ParsedName  # Structured name components
    primary_title: Optional[str]  # Primary/most recent title
    all_titles: List[str]  # All known titles
    biography: Optional[str]  # Biography/background
    confidence_score: float  # 0-1 confidence in data
    data_sources: List[DataSource]  # Sources of data
    quality_flags: List[str]  # Quality issues or notes
    match_key: str  # Generated key for deduplication
```

#### OrganizationRole
```python
class OrganizationRole(BaseModel):
    person_match_key: str  # Reference to person
    organization_ein: str  # Organization EIN
    position_title: str  # Position/role title
    start_date: Optional[date]
    end_date: Optional[date]
    is_current: bool
    is_board_member: bool
    is_executive: bool
    compensation: Optional[Decimal]
    data_source: DataSource
    confidence_score: float
    committees: List[str]
```

## Database Schema

The transformation pipeline creates normalized tables:

### people
Stores normalized person records with parsed names and deduplication keys.

```sql
CREATE TABLE people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_key TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    normalized_name TEXT NOT NULL,
    primary_title TEXT,
    all_titles TEXT, -- JSON array
    biography TEXT,
    confidence_score REAL DEFAULT 1.0,
    data_sources TEXT, -- JSON array
    quality_flags TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### organization_roles
Stores person-organization relationships with position details.

```sql
CREATE TABLE organization_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_match_key TEXT NOT NULL,
    organization_ein TEXT NOT NULL,
    position_title TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    is_board_member BOOLEAN DEFAULT FALSE,
    is_executive BOOLEAN DEFAULT FALSE,
    compensation DECIMAL(12,2),
    data_source TEXT NOT NULL,
    confidence_score REAL DEFAULT 1.0,
    committees TEXT, -- JSON array
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### organization_programs
Stores normalized program/service information.

### organization_contacts  
Stores contact information with verification tracking.

### board_connections
Stores network connections between organizations through shared board members.

## Name Parsing

The name parser handles complex name structures:

### Features
- **Title Recognition**: Dr, Prof, Mr, Mrs, CEO, etc.
- **Suffix Handling**: Jr, Sr, III, PhD, MD, etc.
- **Nickname Conversion**: Bill → William, Bob → Robert
- **Normalization**: Consistent format for matching
- **Similarity Scoring**: Fuzzy matching for duplicates

### Examples
```python
# Complex name parsing
parser = NameParser(config)
parsed = parser.parse_name("Dr. John Q. Smith Jr.")

print(parsed.prefix)      # "Dr"
print(parsed.first_name)  # "John"
print(parsed.middle_name) # "Q"
print(parsed.last_name)   # "Smith"
print(parsed.suffix)      # "Jr"
print(parsed.normalized_name)  # "John Q Smith" (normalized)

# Similarity scoring
similarity = parser.calculate_name_similarity(
    "John Smith", "Jon Smith"
)  # Returns ~0.9 (high similarity)
```

## Deduplication

Cross-source deduplication identifies and merges duplicate records:

### Strategies
1. **Exact Match**: Identical normalized names
2. **Fuzzy Match**: Similar names above threshold
3. **Conflict Resolution**: Merge strategy for duplicates

### Configuration
```python
DeduplicationConfig(
    fuzzy_match_threshold=0.85,  # Similarity threshold
    exact_match_required_fields=["normalized_name"],
    merge_strategy="highest_quality",  # or "newest", "manual"
    auto_merge_duplicates=False  # Manual review recommended
)
```

## Data Validation

Comprehensive validation ensures data quality:

### Contact Validation
- **Email**: RFC-compliant format validation
- **Phone**: US format normalization and validation
- **Website**: URL format and protocol handling

### Name Validation
- **Length**: Minimum 2 characters
- **Format**: Proper name structure
- **Encoding**: UTF-8 character handling

### Quality Scoring
- **Confidence**: 0-1 scale based on data sources
- **Quality Flags**: Automatic issue detection
- **Source Attribution**: Track data provenance

## Error Handling

Robust error handling at multiple levels:

### Validation Errors
```python
class ValidationError(BaseModel):
    field: str  # Field with error
    error_type: str  # Type of error
    message: str  # Error message
    severity: Literal["warning", "error", "critical"]
```

### Recovery Strategies
- **Graceful Degradation**: Continue processing valid records
- **Partial Success**: Report successful and failed records
- **Rollback**: Database transaction safety
- **Retry Logic**: Temporary failure recovery

## Performance Optimization

### Batch Processing
- Configurable batch sizes
- Memory-efficient streaming
- Progress tracking

### Database Optimization
- Indexed queries
- Upsert operations
- Transaction management
- Connection pooling

### Caching
- Parsed name caching
- Similarity score caching
- Configuration caching

## Integration Points

### Frontend Integration
```javascript
// Frontend webScrapingResults structure
const webScrapingResults = {
    extracted_info: {
        leadership: [/* ScrapedLeadership objects */],
        programs: [/* ScrapedProgram objects */],
        mission_statements: [/* strings */],
        contact_info: [/* ScrapedContact objects */]
    },
    successful_scrapes: [/* URLs */],
    source_attribution: {/* metadata */}
};

// Call transformation via API
fetch('/api/profiles/123/transform', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        web_scraping_results: webScrapingResults,
        board_members_json: boardMembers
    })
});
```

### Database Profile Integration
```python
# Update profile with transformation results
def save_profile_with_transformation(profile_form_data):
    # Save basic profile
    profile = create_profile_from_form(profile_form_data)
    db_manager.create_profile(profile)
    
    # Transform enhanced data
    transformer = CatalynxDataTransformer(db_manager)
    result = transformer.transform_profile_data(
        profile_id=profile.id,
        web_scraping_results=profile_form_data.get('webScrapingResults'),
        board_members_json=profile_form_data.get('board_members')
    )
    
    return profile, result
```

## Testing

Run the comprehensive test suite:

```bash
# Run all transformation tests
python -m pytest tests/test_data_transformation.py -v

# Run specific test categories
python -m pytest tests/test_data_transformation.py::TestNameParser -v
python -m pytest tests/test_data_transformation.py::TestDataDeduplicator -v

# Run with coverage
python -m pytest tests/test_data_transformation.py --cov=src.data_transformation
```

## Monitoring and Maintenance

### Health Checks
```python
# Validate system configuration
validation = transformer.validate_configuration()
if not validation['config_valid']:
    print(f"Issues: {validation['warnings']}")

# Monitor data quality
report = transformer.get_data_quality_report()
if report['transformation_statistics']['success_rate_percent'] < 95:
    # Alert on low success rate
    send_alert("Low transformation success rate")
```

### Cleanup and Maintenance
```python
# Clean up old transformation records
stats = transformer.cleanup_old_data(days_old=30)
print(f"Cleaned up {stats['transformation_records_deleted']} records")

# Database maintenance
db_manager.vacuum_database()  # Optimize storage
```

## Troubleshooting

### Common Issues

1. **Name Parsing Failures**
   - Check minimum name length configuration
   - Review title/suffix recognition lists
   - Validate character encoding

2. **Duplicate Detection Issues**
   - Adjust fuzzy match threshold
   - Review normalization logic
   - Check for data quality issues

3. **Database Integration Errors**
   - Verify schema is up to date
   - Check foreign key constraints
   - Review transaction isolation

4. **Performance Issues**
   - Reduce batch size
   - Optimize database indexes
   - Monitor memory usage

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('src.data_transformation').setLevel(logging.DEBUG)

# Detailed transformation analysis
result = transformer.transform_profile_data(profile_id, debug=True)
for error in result.validation_errors:
    print(f"{error.severity}: {error.field} - {error.message}")
```

## API Reference

See the complete API documentation in the code docstrings:

- `CatalynxDataTransformer`: Main service class
- `DataTransformationService`: Core transformation logic  
- `NameParser`: Name parsing and normalization
- `DataDeduplicator`: Duplicate detection and merging
- `NormalizedDatabaseManager`: Database operations

For additional support, review the unit tests in `tests/test_data_transformation.py` for comprehensive usage examples.
