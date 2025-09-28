// Code Generation Configuration
// Generates Python types from BAML schemas

generator lang_python {
    output_type python/pydantic
    output_dir "../app/generated"
    version "0.60.0"

    options {
        // Generate Pydantic v2 models
        pydantic_version "2"

        // Include validation and serialization helpers
        include_helpers true

        // Generate async-compatible code
        async_mode true
    }
}

// Optional: Generate TypeScript types for frontend integration
generator lang_typescript {
    output_type typescript
    output_dir "../frontend/types"
    version "0.60.0"

    options {
        // Generate Zod schemas for validation
        include_zod true

        // Export types as ES modules
        module_type "esm"
    }
}

// Optional: Generate OpenAPI schema for documentation
generator openapi {
    output_type openapi
    output_dir "../docs"
    version "0.60.0"

    options {
        // Include examples in schema
        include_examples true

        // Generate complete API documentation
        include_servers true
    }
}