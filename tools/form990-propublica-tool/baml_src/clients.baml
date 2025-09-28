// BAML Client Configuration for Form 990 ProPublica Tool
// 12-Factor Factor 4: Structured input/output contracts

client<llm> ProPublicaEnrichmentLLM {
    provider baml-openai-chat
    options {
        model gpt-4o-mini
        temperature 0.1
        max_tokens 2000
    }
}

client<llm> ProPublicaAnalysisLLM {
    provider baml-openai-chat
    options {
        model gpt-4o
        temperature 0.2
        max_tokens 4000
    }
}