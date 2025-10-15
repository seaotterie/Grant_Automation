// LLM Client Configuration for Form 990 Analysis Tool
// Integrates with existing Catalynx OpenAI configuration

// Primary client - matches existing Catalynx GPT-5 configuration
client<llm> OpenAI {
    provider openai
    options {
        // Use GPT-5 models as per Catalynx requirements
        model gpt-5
        api_key env.OPENAI_API_KEY

        // Performance settings optimized for financial analysis
        max_tokens 3000
        temperature 0.1  // Low temperature for consistent analytical output

        // Cost optimization
        stream false

        // Reliability settings
        max_retries 3
        timeout 60000  // 60 seconds for complex analysis
    }
}

// Lite client for simple extractions and validations
client<llm> OpenAILite {
    provider openai
    options {
        // Use lighter model for simple tasks
        model gpt-5-turbo  // Following Catalynx GPT-5 requirement
        api_key env.OPENAI_API_KEY

        // Optimized for speed
        max_tokens 1500
        temperature 0.1

        // Fast processing
        stream false
        timeout 30000  // 30 seconds
    }
}

// Analysis client for complex financial computations
client<llm> OpenAIAnalysis {
    provider openai
    options {
        // Heavy model for complex financial analysis
        model gpt-5  // Matches Catalynx AI_RESEARCH_MODEL
        api_key env.OPENAI_API_KEY

        // Enhanced reasoning for complex financial analysis
        max_tokens 4000
        temperature 0.2

        // Allow longer processing for complex analysis
        timeout 120000  // 120 seconds for deep analysis
    }
}

// Fallback client for high availability
client<llm> OpenAIFallback {
    provider openai
    options {
        model gpt-3.5-turbo  // Only fallback that's not GPT-5
        api_key env.OPENAI_API_KEY

        // Basic functionality
        max_tokens 2000
        temperature 0.1

        // Quick fallback
        timeout 45000
    }
}