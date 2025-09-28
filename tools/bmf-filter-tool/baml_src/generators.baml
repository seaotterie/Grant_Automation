// BAML Code Generation Configuration
// Following 12-Factor Agents pattern for structured outputs

generator lang_python {
    output_type python/pydantic
    output_dir "../app/generated"
    version "0.60.0"

    // Type-safe Python generation
    python_version "3.8"
    pydantic_version "v2"

    // Follow 12-factor naming conventions
    class_name_format "PascalCase"
    field_name_format "snake_case"

    // Integration with existing Catalynx patterns
    generate_docs true
    generate_examples true

    // Performance optimizations
    async_support true
    validation_strict true
}