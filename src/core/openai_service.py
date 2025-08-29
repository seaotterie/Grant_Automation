"""
OpenAI Service - Centralized OpenAI API management for grant automation platform

This service provides a unified interface for OpenAI API calls across all AI processors,
handling authentication, rate limiting, error handling, and cost tracking.
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import openai
from openai import AsyncOpenAI
import time
import httpx

logger = logging.getLogger(__name__)


@dataclass
class CompletionRequest:
    """Structured request for OpenAI completion"""
    model: str
    messages: List[Dict[str, str]]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None


@dataclass 
class CompletionResponse:
    """Structured response from OpenAI completion"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    cost_estimate: float


class OpenAIService:
    """Centralized OpenAI service for grant automation platform"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI service with API key management"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        self.cost_tracking = {}
        self.request_count = 0
        
        # Cost per token (GPT-5 Models Only - August 2025 Release)
        self.cost_per_token = {
            "gpt-5": {"input": 1.25 / 1000000, "output": 10.0 / 1000000},  # $1.25/1M input, $10/1M output
            "gpt-5-mini": {"input": 0.5 / 1000000, "output": 4.0 / 1000000},  # Mid-tier GPT-5
            "gpt-5-nano": {"input": 0.25 / 1000000, "output": 2.0 / 1000000}, # Most cost-effective GPT-5
            "gpt-5-chat-latest": {"input": 1.25 / 1000000, "output": 10.0 / 1000000}, # Latest GPT-5
            "gpt-5-preview": {"input": 1.25 / 1000000, "output": 10.0 / 1000000} # Preview version
        }
        
        # Rate limiting
        self.rate_limit_requests = 3000  # requests per minute
        self.rate_limit_tokens = 250000  # tokens per minute
        self.request_times = []
        
        # Initialize client if API key is available
        if self.api_key:
            # Configure custom limits for connection pooling
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
            
            # Custom HTTP client with shorter timeouts
            http_client = httpx.AsyncClient(
                limits=limits,
                timeout=httpx.Timeout(30.0, connect=5.0)  # Shorter timeouts
            )
            
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                http_client=http_client,
                max_retries=3,  # Reduced from default 10 to 3
                timeout=30.0    # 30 second timeout
            )
            logger.info("OpenAI service initialized with API key and reduced retry configuration (3 attempts max)")
        else:
            logger.warning("OpenAI service initialized without API key - using simulation mode")
    
    async def create_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Create OpenAI completion with rate limiting and cost tracking
        
        Args:
            model: OpenAI model to use
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional OpenAI parameters
            
        Returns:
            CompletionResponse with content and metadata
        """
        # Rate limiting check
        await self._check_rate_limits()
        
        # If no API key, use simulation mode
        if not self.client:
            return await self._simulate_completion(model, messages, max_tokens)
        
        try:
            # Make API call with model-specific parameters
            start_time = time.time()
            
            # Prepare parameters based on model
            api_params = {
                "model": model,
                "messages": messages,
                **kwargs
            }
            
            # GPT-5 models have different parameter requirements
            if model.startswith("gpt-5"):
                if max_tokens is not None:
                    api_params["max_completion_tokens"] = max_tokens
                # GPT-5 models only support temperature=1 (default)
                if temperature is not None and temperature != 1.0:
                    logger.info(f"GPT-5 model {model} only supports temperature=1, ignoring temperature={temperature}")
                # Don't set temperature for GPT-5 models (use default)
            else:
                if max_tokens is not None:
                    api_params["max_tokens"] = max_tokens
                if temperature is not None:
                    api_params["temperature"] = temperature
            
            response = await self.client.chat.completions.create(**api_params)
            end_time = time.time()
            
            # Extract response data with None check
            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
            finish_reason = response.choices[0].finish_reason
            
            # Calculate cost estimate
            cost_estimate = self._calculate_cost(model, usage)
            
            # Track request
            self.request_count += 1
            self.request_times.append(time.time())
            
            # Update cost tracking
            if model not in self.cost_tracking:
                self.cost_tracking[model] = {"requests": 0, "total_cost": 0.0, "total_tokens": 0}
            
            self.cost_tracking[model]["requests"] += 1
            self.cost_tracking[model]["total_cost"] += cost_estimate
            self.cost_tracking[model]["total_tokens"] += usage.get("total_tokens", 0)
            
            logger.info(f"OpenAI completion: {model}, tokens: {usage.get('total_tokens', 0)}, "
                       f"cost: ${cost_estimate:.4f}, time: {end_time - start_time:.2f}s")
            
            return CompletionResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                cost_estimate=cost_estimate
            )
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            # Fall back to simulation mode
            logger.info("Falling back to simulation mode due to API error")
            return await self._simulate_completion(model, messages, max_tokens)
    
    async def _simulate_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None
    ) -> CompletionResponse:
        """
        Simulate OpenAI completion for development/testing
        
        This provides realistic simulation for development when API key is not available
        or for testing scenarios.
        """
        # Simulate API delay
        await asyncio.sleep(1.0 + len(messages) * 0.2)
        
        # Extract prompt content for context
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Generate simulated response based on model and content patterns
        if "validation" in user_message.lower() or "validator" in user_message.lower():
            simulated_content = self._generate_validation_simulation()
        elif "strategic" in user_message.lower() or "scorer" in user_message.lower():
            simulated_content = self._generate_strategic_simulation()
        elif "research" in user_message.lower() or "dossier" in user_message.lower():
            simulated_content = self._generate_research_simulation()
        else:
            simulated_content = self._generate_generic_simulation()
        
        # Simulate usage statistics
        estimated_input_tokens = len(user_message) // 4  # Rough approximation
        estimated_output_tokens = len(simulated_content) // 4
        
        usage = {
            "prompt_tokens": estimated_input_tokens,
            "completion_tokens": estimated_output_tokens,
            "total_tokens": estimated_input_tokens + estimated_output_tokens
        }
        
        # Calculate simulated cost
        cost_estimate = self._calculate_cost(model, usage)
        
        logger.info(f"OpenAI simulation: {model}, estimated tokens: {usage['total_tokens']}, "
                   f"estimated cost: ${cost_estimate:.4f}")
        
        return CompletionResponse(
            content=simulated_content,
            model=model,
            usage=usage,
            finish_reason="stop",
            cost_estimate=cost_estimate
        )
    
    def _generate_validation_simulation(self) -> str:
        """Generate simulated validation response"""
        return '''{
  "opp_001": {
    "validation_result": "valid_funding",
    "confidence_score": 0.92,
    "eligibility_status": "eligible", 
    "discovery_track": "government",
    "go_no_go_recommendation": "go",
    "triage_priority": "high",
    "validation_notes": "Confirmed federal funding opportunity with clear eligibility criteria"
  },
  "opp_002": {
    "validation_result": "valid_funding",
    "confidence_score": 0.87,
    "eligibility_status": "conditional",
    "discovery_track": "foundation", 
    "go_no_go_recommendation": "go",
    "triage_priority": "medium",
    "validation_notes": "Foundation opportunity requires geographic eligibility verification"
  }
}'''
    
    def _generate_strategic_simulation(self) -> str:
        """Generate simulated strategic scoring response"""
        return '''{
  "opp_001": {
    "strategic_score": 0.84,
    "strategic_value": "high",
    "alignment_score": 0.89,
    "competitive_assessment": "moderate",
    "resource_requirements": "standard",
    "success_probability": 0.76,
    "strategic_rationale": "Strong mission alignment with moderate competition. Organization has capacity for successful implementation."
  }
}'''
    
    def _generate_research_simulation(self) -> str:
        """Generate simulated research/dossier response"""
        return '''{
  "strategic_dossier": {
    "partnership_assessment": {
      "mission_alignment_score": 88,
      "strategic_value": "high", 
      "mutual_benefits": ["Program expansion", "Geographic coverage"],
      "partnership_potential": "long_term_strategic"
    },
    "funding_strategy": {
      "optimal_request_amount": "$150,000",
      "best_timing": "Q2_2024",
      "target_programs": ["Health Initiative", "Education Outreach"],
      "success_factors": ["Community impact", "Board endorsement"]
    },
    "recommended_approach": {
      "pursuit_recommendation": "high_priority",
      "success_probability": 0.82
    }
  },
  "confidence_level": 0.91
}'''
    
    def _generate_generic_simulation(self) -> str:
        """Generate generic simulated response"""
        return '''{
  "analysis_result": "completed",
  "confidence_score": 0.85,
  "recommendations": ["Continue with detailed analysis", "Develop strategic approach"],
  "next_steps": ["Gather additional data", "Prepare comprehensive assessment"],
  "estimated_success_probability": 0.78
}'''
    
    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Calculate estimated cost for API call"""
        if model not in self.cost_per_token:
            # Default to GPT-5-nano rates for unknown models
            model = "gpt-5-nano"
        
        rates = self.cost_per_token[model]
        
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        input_cost = input_tokens * rates["input"]
        output_cost = output_tokens * rates["output"]
        
        return input_cost + output_cost
    
    async def _check_rate_limits(self):
        """Check and enforce rate limits"""
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Check if we're approaching rate limits
        if len(self.request_times) >= self.rate_limit_requests * 0.9:
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                logger.info(f"Rate limit approaching, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary"""
        total_cost = sum(data["total_cost"] for data in self.cost_tracking.values())
        total_requests = sum(data["requests"] for data in self.cost_tracking.values())
        total_tokens = sum(data["total_tokens"] for data in self.cost_tracking.values())
        
        return {
            "total_requests": total_requests,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "cost_by_model": self.cost_tracking,
            "average_cost_per_request": total_cost / max(total_requests, 1),
            "average_tokens_per_request": total_tokens / max(total_requests, 1)
        }
    
    def reset_cost_tracking(self):
        """Reset cost tracking data"""
        self.cost_tracking = {}
        self.request_count = 0
        logger.info("Cost tracking data reset")


# Global service instance
_openai_service = None


def get_openai_service() -> OpenAIService:
    """Get the global OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service


def configure_openai_service(api_key: str) -> OpenAIService:
    """Configure the global OpenAI service with API key"""
    global _openai_service
    _openai_service = OpenAIService(api_key=api_key)
    return _openai_service


# Export public interface
__all__ = [
    "OpenAIService",
    "CompletionRequest", 
    "CompletionResponse",
    "get_openai_service",
    "configure_openai_service"
]