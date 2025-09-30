# Data Export Tool

Multi-format data export with professional templates.

## Features
- **Formats**: PDF, Excel, CSV, JSON, HTML
- **Templates**: Executive, Detailed, Technical, Summary, Custom
- Professional styling and formatting
- Metadata inclusion
- Batch export support

## Usage

```python
from tools.data_export_tool.app import export_data

result = await export_data(
    data={"opportunities": [...], "analysis": {...}},
    export_format="pdf",
    template="executive",
    title="Grant Intelligence Report",
    organization_name="Example Nonprofit"
)

if result.is_success():
    print(f"Exported to: {result.data.output_filepath}")
    print(f"File size: {result.data.file_size_bytes} bytes")
```

## Cost: $0.00 (no AI calls)

## Replaces
- `export_processor.py`
