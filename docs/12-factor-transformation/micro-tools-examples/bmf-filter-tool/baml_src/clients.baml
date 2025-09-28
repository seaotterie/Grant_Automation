// LLM Client Configuration for BMF Filter Tool

client<llm> OpenAI {
    provider openai
    options {
        model gpt-4
        api_key env.OPENAI_API_KEY
        temperature 0.1  // Low temperature for consistent structured extraction
        max_tokens 1000
    }
}

client<llm> OpenAILite {
    provider openai
    options {
        model gpt-3.5-turbo
        api_key env.OPENAI_API_KEY
        temperature 0.1
        max_tokens 800
    }
}

// Alternative client for development/testing
client<llm> MockLLM {
    provider openai
    options {
        model gpt-3.5-turbo
        api_key "mock-key"
        base_url "http://localhost:8080/v1"  // For local testing
    }
}