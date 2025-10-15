// BAML Schema for Data Export Tool (minimal - no AI calls needed)

enum ExportFormat {
  pdf
  excel
  csv
  json
  html
}

enum ExportTemplate {
  executive
  detailed
  technical
  summary
  custom
}

class DataExportInput {
  data map<string, any>
  export_format ExportFormat
  template ExportTemplate
  output_filename string
  title string?
  organization_name string?
}

class DataExportOutput {
  export_successful bool
  output_filepath string
  output_format ExportFormat
  records_exported int
  file_size_bytes int
  processing_time_seconds float
}
