// LLM Client Configuration for Deep Intelligence Tool
// Integrates with existing Catalynx OpenAI configuration

// Primary client - GPT-5 for deep intelligence analysis
client<llm> GPT4o {
    provider openai
    options {
        // Use GPT-5 as per Catalynx requirements
        model gpt-5
        api_key env.OPENAI_API_KEY

        // Performance settings optimized for deep intelligence
        max_tokens 4000
        temperature 0.2  // Balanced for analytical depth + strategic insights

        // Cost optimization
        stream false

        // Reliability settings
        max_retries 3
        timeout 120000  // 120 seconds for deep analysis
    }
}

// ESSENTIALS tier client - optimized for $0.05 AI cost
client<llm> EssentialsClient {
    provider openai
    options {
        // GPT-5 for ESSENTIALS tier
        model gpt-5
        api_key env.OPENAI_API_KEY

        // Optimized for $0.05 cost target
        max_tokens 2500  // Reduced for cost control
        temperature 0.2

        stream false
        timeout 90000  // 90 seconds
    }
}

// PREMIUM tier client - optimized for $0.10 AI cost
client<llm> PremiumClient {
    provider openai
    options {
        // GPT-5 for PREMIUM tier
        model gpt-5
        api_key env.OPENAI_API_KEY

        // Enhanced for strategic consulting
        max_tokens 5000  // Higher for comprehensive dossier
        temperature 0.3  // Slightly higher for strategic creativity

        stream false
        timeout 180000  // 180 seconds for comprehensive analysis
    }
}
