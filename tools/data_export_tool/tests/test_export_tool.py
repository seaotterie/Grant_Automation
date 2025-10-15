"""Tests for Data Export Tool"""

import pytest
from tools.data_export_tool.app import (
    DataExportTool,
    DataExportInput,
    ExportFormat,
    ExportTemplate
)


@pytest.mark.asyncio
async def test_json_export():
    tool = DataExportTool()
    export_input = DataExportInput(
        data={"test": "data", "count": 123},
        export_format=ExportFormat.JSON,
        output_filename="test_export"
    )
    result = await tool.execute(export_input=export_input)
    assert result.is_success()
    assert result.data.export_successful
    assert ".json" in result.data.output_filepath


@pytest.mark.asyncio
async def test_csv_export():
    tool = DataExportTool()
    export_input = DataExportInput(
        data=[{"name": "Item 1", "value": 100}, {"name": "Item 2", "value": 200}],
        export_format=ExportFormat.CSV,
        output_filename="test_export"
    )
    result = await tool.execute(export_input=export_input)
    assert result.is_success()
    assert result.data.export_successful
    assert ".csv" in result.data.output_filepath


@pytest.mark.asyncio
async def test_html_export():
    tool = DataExportTool()
    export_input = DataExportInput(
        data={"summary": {"total": 10, "passed": 8}},
        export_format=ExportFormat.HTML,
        template=ExportTemplate.EXECUTIVE,
        title="Test Report",
        organization_name="Test Org"
    )
    result = await tool.execute(export_input=export_input)
    assert result.is_success()
    assert result.data.export_successful
    assert ".html" in result.data.output_filepath


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
