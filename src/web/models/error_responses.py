"""
Standardized Error Response Models
Provides consistent error response format across all API endpoints with recovery guidance.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

from src.core.error_recovery import ErrorInfo, ErrorCategory, ErrorSeverity, RecoveryAction


class ErrorResponseType(str, Enum):
    """Types of error responses."""
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SYSTEM_ERROR = "system_error"
    API_ERROR = "api_error"


class RecoveryGuidance(BaseModel):
    """Recovery guidance for the user."""
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested user actions")
    retry_allowed: bool = Field(False, description="Whether retry is allowed")
    retry_delay_seconds: Optional[int] = Field(None, description="Suggested retry delay")
    documentation_link: Optional[str] = Field(None, description="Link to relevant documentation")
    support_contact: Optional[str] = Field(None, description="Support contact information")


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(None, description="Field name that caused the error")
    code: str = Field(..., description="Specific error code")
    message: str = Field(..., description="Human-readable error message")
    value: Optional[Any] = Field(None, description="Value that caused the error")


class StandardErrorResponse(BaseModel):
    """Standard error response format."""
    # Core Error Information
    success: bool = Field(False, description="Always false for error responses")
    error_type: ErrorResponseType = Field(..., description="Type of error")
    error_code: str = Field(..., description="Unique error code")
    message: str = Field(..., description="Human-readable error message")
    
    # Detailed Information
    details: List[ErrorDetail] = Field(default_factory=list, description="Detailed error information")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    # Recovery Information
    recovery_guidance: RecoveryGuidance = Field(default_factory=RecoveryGuidance)
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")


class ValidationErrorResponse(StandardErrorResponse):
    """Validation error response with field-specific details."""
    error_type: ErrorResponseType = Field(default=ErrorResponseType.VALIDATION_ERROR)
    
    @classmethod
    def from_validation_error(cls, validation_error: Exception, request_id: Optional[str] = None) -> "ValidationErrorResponse":
        """Create from validation error exception."""
        details = []
        
        # Extract field errors if available (Pydantic ValidationError)
        if hasattr(validation_error, 'errors'):
            for error in validation_error.errors():
                field_name = ".".join(str(loc) for loc in error.get("loc", []))
                details.append(ErrorDetail(
                    field=field_name if field_name else None,
                    code=error.get("type", "validation_error"),
                    message=error.get("msg", str(validation_error)),
                    value=error.get("input")
                ))
        else:
            details.append(ErrorDetail(
                code="validation_error",
                message=str(validation_error)
            ))
        
        return cls(
            error_code="VALIDATION_FAILED",
            message="Validation failed for one or more fields",
            details=details,
            recovery_guidance=RecoveryGuidance(
                suggested_actions=[
                    "Check the request format and ensure all required fields are provided",
                    "Verify that field values match the expected format and constraints",
                    "Review the API documentation for correct request structure"
                ],
                documentation_link="/api/docs"
            ),
            request_id=request_id
        )


class ProcessingErrorResponse(StandardErrorResponse):
    """Processing error response."""
    error_type: ErrorResponseType = Field(default=ErrorResponseType.PROCESSING_ERROR)
    
    @classmethod
    def from_error_info(cls, error_info: ErrorInfo, request_id: Optional[str] = None) -> "ProcessingErrorResponse":
        """Create from ErrorInfo object."""
        # Map error category to appropriate recovery guidance
        guidance = RecoveryGuidance()
        
        if error_info.category == ErrorCategory.RATE_LIMIT:
            guidance.suggested_actions = [
                "Wait before making another request",
                "Consider reducing the frequency of requests",
                "Contact support if rate limits seem incorrect"
            ]
            guidance.retry_allowed = True
            guidance.retry_delay_seconds = 60
        
        elif error_info.category == ErrorCategory.AUTHENTICATION:
            guidance.suggested_actions = [
                "Check your API key configuration in Settings",
                "Verify that your API key is valid and not expired",
                "Ensure proper authentication headers are included"
            ]
            guidance.documentation_link = "/api/docs/authentication"
        
        elif error_info.category == ErrorCategory.TIMEOUT:
            guidance.suggested_actions = [
                "Try the request again with a longer timeout",
                "Check your network connection",
                "Consider breaking large requests into smaller ones"
            ]
            guidance.retry_allowed = True
            guidance.retry_delay_seconds = 5
        
        elif error_info.category == ErrorCategory.NETWORK:
            guidance.suggested_actions = [
                "Check your internet connection",
                "Retry the request in a few moments",
                "Verify that external services are accessible"
            ]
            guidance.retry_allowed = True
            guidance.retry_delay_seconds = 10
        
        else:
            guidance.suggested_actions = [
                "Review the error details and adjust your request",
                "Check the system status page for known issues",
                "Contact support if the problem persists"
            ]
            guidance.retry_allowed = RecoveryAction.RETRY in error_info.recovery_actions
        
        return cls(
            error_code=error_info.error_id.upper(),
            message=error_info.user_message or error_info.message,
            details=[ErrorDetail(
                code=error_info.category.value,
                message=error_info.message
            )],
            context=error_info.context,
            recovery_guidance=guidance,
            request_id=request_id
        )


class AuthenticationErrorResponse(StandardErrorResponse):
    """Authentication error response."""
    error_type: ErrorResponseType = Field(default=ErrorResponseType.AUTHENTICATION_ERROR)
    
    def __init__(self, **kwargs):
        super().__init__(
            error_code="AUTHENTICATION_FAILED",
            message="Authentication failed. Please check your credentials.",
            recovery_guidance=RecoveryGuidance(
                suggested_actions=[
                    "Check your API key in the Settings tab",
                    "Ensure your API key is valid and not expired",
                    "Verify you have the necessary permissions"
                ],
                documentation_link="/api/docs/authentication"
            ),
            **kwargs
        )


class NotFoundErrorResponse(StandardErrorResponse):
    """Resource not found error response."""
    error_type: ErrorResponseType = Field(default=ErrorResponseType.NOT_FOUND_ERROR)
    
    @classmethod
    def for_resource(cls, resource_type: str, resource_id: str, request_id: Optional[str] = None) -> "NotFoundErrorResponse":
        """Create for a specific resource."""
        return cls(
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource_type.title()} with ID '{resource_id}' was not found.",
            details=[ErrorDetail(
                field="id",
                code="not_found",
                message=f"{resource_type} not found",
                value=resource_id
            )],
            recovery_guidance=RecoveryGuidance(
                suggested_actions=[
                    "Verify the resource ID is correct",
                    f"Check that the {resource_type} exists and is accessible",
                    "Review the list of available resources"
                ]
            ),
            request_id=request_id
        )


class RateLimitErrorResponse(StandardErrorResponse):
    """Rate limit exceeded error response."""
    error_type: ErrorResponseType = Field(default=ErrorResponseType.RATE_LIMIT_ERROR)
    
    def __init__(self, reset_time: Optional[datetime] = None, **kwargs):
        recovery_guidance = RecoveryGuidance(
            suggested_actions=[
                "Wait before making another request",
                "Consider reducing request frequency",
                "Implement exponential backoff in your client"
            ],
            retry_allowed=True,
            retry_delay_seconds=60
        )
        
        if reset_time:
            recovery_guidance.suggested_actions.append(
                f"Rate limit resets at {reset_time.isoformat()}"
            )
        
        super().__init__(
            error_code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded. Please wait before making another request.",
            recovery_guidance=recovery_guidance,
            **kwargs
        )


class SystemErrorResponse(StandardErrorResponse):
    """System error response."""
    error_type: ErrorResponseType = Field(default=ErrorResponseType.SYSTEM_ERROR)
    
    def __init__(self, **kwargs):
        super().__init__(
            error_code="SYSTEM_ERROR",
            message="A system error occurred. Please try again later.",
            recovery_guidance=RecoveryGuidance(
                suggested_actions=[
                    "Try the request again in a few moments",
                    "Check the system status page",
                    "Contact support if the problem persists"
                ],
                retry_allowed=True,
                retry_delay_seconds=30,
                support_contact="support@catalynx.com"
            ),
            **kwargs
        )


# Utility functions for creating error responses

def create_error_response(
    error: Exception,
    error_type: ErrorResponseType = ErrorResponseType.SYSTEM_ERROR,
    request_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> StandardErrorResponse:
    """Create appropriate error response based on exception type."""
    
    # Validation errors
    if hasattr(error, 'errors') and callable(error.errors):  # Pydantic ValidationError
        return ValidationErrorResponse.from_validation_error(error, request_id)
    
    # HTTP errors
    if hasattr(error, 'status_code'):
        if error.status_code == 404:
            return NotFoundErrorResponse(
                message=getattr(error, 'detail', 'Resource not found'),
                request_id=request_id
            )
        elif error.status_code == 401:
            return AuthenticationErrorResponse(request_id=request_id)
        elif error.status_code == 429:
            return RateLimitErrorResponse(request_id=request_id)
    
    # System errors
    return SystemErrorResponse(
        message=str(error),
        context=context,
        request_id=request_id
    )


def create_error_from_error_info(
    error_info: ErrorInfo,
    request_id: Optional[str] = None
) -> StandardErrorResponse:
    """Create error response from ErrorInfo object."""
    return ProcessingErrorResponse.from_error_info(error_info, request_id)


# Export classes and functions
__all__ = [
    "ErrorResponseType",
    "RecoveryGuidance", 
    "ErrorDetail",
    "StandardErrorResponse",
    "ValidationErrorResponse",
    "ProcessingErrorResponse",
    "AuthenticationErrorResponse",
    "NotFoundErrorResponse",
    "RateLimitErrorResponse",
    "SystemErrorResponse",
    "create_error_response",
    "create_error_from_error_info"
]