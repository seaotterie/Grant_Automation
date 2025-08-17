# Foundation Data Structure

This directory contains foundation entities organized by EIN/Foundation ID.

## Directory Structure

- `{foundation_ein}/` - Individual foundation entity directories
- `indices/` - Search and classification indices
- `990pf_filings/` - 990-PF tax filings data
- `grantmaking_data/` - Grant awards and recipient information
- `board_data/` - Board member and governance information

## Entity Organization

Each foundation entity follows the standard entity-based structure:
- `metadata.json` - Entity metadata and data source information
- `foundation_metadata.json` - Foundation-specific classification data
- `foundation_propublica.json` - ProPublica 990 data (when available)
- `990pf_data.json` - 990-PF specific data (when available)
- `grantmaking_history.json` - Grant-making patterns and recipients
- `board_members.json` - Board member and officer information

## Migration Information

This structure was created during Phase 2.3 Foundation Data Migration.
Foundation entities are extracted from nonprofit data based on:
- Foundation codes (10-14 in ProPublica data)
- NTEE codes starting with 'T' (grantmaking)
- 990-PF filing history
- Organization name patterns

Ready for integration with Foundation Directory API and other foundation data sources.
