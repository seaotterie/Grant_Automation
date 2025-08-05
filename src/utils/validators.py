"""
Data Validation Utilities
Common validation functions for grant research data.
"""
import re
from typing import Any, Optional, List, Union
from datetime import datetime


def validate_ein(ein: str) -> bool:
    """
    Validate EIN (Employer Identification Number) format.
    
    Args:
        ein: EIN string to validate
        
    Returns:
        True if valid EIN format, False otherwise
    """
    if not ein or not isinstance(ein, str):
        return False
    
    # Remove hyphens and spaces
    clean_ein = ein.replace('-', '').replace(' ', '')
    
    # Check if it's exactly 9 digits
    return bool(re.match(r'^\d{9}$', clean_ein))


def normalize_ein(ein: str) -> Optional[str]:
    """
    Normalize EIN to standard 9-digit format.
    
    Args:
        ein: EIN string to normalize
        
    Returns:
        Normalized 9-digit EIN or None if invalid
    """
    if not ein or not isinstance(ein, str):
        return None
    
    # Remove hyphens and spaces
    clean_ein = ein.replace('-', '').replace(' ', '')
    
    if validate_ein(clean_ein):
        return clean_ein
    
    return None


def validate_state_code(state: str) -> bool:
    """
    Validate US state code.
    
    Args:
        state: State code to validate
        
    Returns:
        True if valid state code, False otherwise
    """
    if not state or not isinstance(state, str):
        return False
    
    state = state.upper().strip()
    
    # List of valid US state codes
    valid_states = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        'DC', 'AS', 'GU', 'MP', 'PR', 'VI'  # Territories
    }
    
    return state in valid_states


def validate_ntee_code(ntee_code: str) -> bool:
    """
    Validate NTEE (National Taxonomy of Exempt Entities) code format.
    
    Args:
        ntee_code: NTEE code to validate
        
    Returns:
        True if valid NTEE code format, False otherwise
    """
    if not ntee_code or not isinstance(ntee_code, str):
        return False
    
    ntee_code = ntee_code.upper().strip()
    
    # NTEE codes are typically 1 letter + 2 digits (e.g., "P81")
    # Some may have additional suffixes
    return bool(re.match(r'^[A-Z]\d{2}[A-Z0-9]*$', ntee_code))


def validate_zip_code(zip_code: str) -> bool:
    """
    Validate US ZIP code format.
    
    Args:
        zip_code: ZIP code to validate
        
    Returns:
        True if valid ZIP code format, False otherwise
    """
    if not zip_code or not isinstance(zip_code, str):
        return False
    
    zip_code = zip_code.strip()
    
    # 5-digit or 9-digit (ZIP+4) format
    return bool(re.match(r'^\d{5}(-\d{4})?$', zip_code))


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL format, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    return bool(email_pattern.match(email))


def validate_year(year: Union[int, str]) -> bool:
    """
    Validate year value.
    
    Args:
        year: Year to validate
        
    Returns:
        True if valid year, False otherwise
    """
    try:
        year_int = int(year)
        current_year = datetime.now().year
        # Valid range: 1950 to current year + 1
        return 1950 <= year_int <= current_year + 1
    except (ValueError, TypeError):
        return False


def validate_financial_amount(amount: Union[int, float, str]) -> bool:
    """
    Validate financial amount.
    
    Args:
        amount: Financial amount to validate
        
    Returns:
        True if valid financial amount, False otherwise
    """
    try:
        amount_float = float(amount)
        # Financial amounts should be non-negative and reasonable
        return 0 <= amount_float <= 1e12  # Up to 1 trillion
    except (ValueError, TypeError):
        return False


def validate_percentage(percentage: Union[int, float, str]) -> bool:
    """
    Validate percentage value (0-100).
    
    Args:
        percentage: Percentage to validate
        
    Returns:
        True if valid percentage, False otherwise
    """
    try:
        pct_float = float(percentage)
        return 0 <= pct_float <= 100
    except (ValueError, TypeError):
        return False


def validate_ratio(ratio: Union[int, float, str]) -> bool:
    """
    Validate ratio value (0-1).
    
    Args:
        ratio: Ratio to validate
        
    Returns:
        True if valid ratio, False otherwise
    """
    try:
        ratio_float = float(ratio)
        return 0 <= ratio_float <= 1
    except (ValueError, TypeError):
        return False


def validate_phone_number(phone: str) -> bool:
    """
    Validate US phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid phone number format, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common formatting characters
    clean_phone = re.sub(r'[^\d]', '', phone)
    
    # Should be 10 digits (US format)
    return len(clean_phone) == 10 and clean_phone.isdigit()


def validate_organization_name(name: str) -> bool:
    """
    Validate organization name.
    
    Args:
        name: Organization name to validate
        
    Returns:
        True if valid organization name, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    # Should not be empty and should be reasonable length
    return 2 <= len(name) <= 200


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    Sanitize string input by removing unwanted characters and limiting length.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove control characters and excessive whitespace
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip()
    
    return sanitized


def validate_data_completeness(data: dict, required_fields: List[str]) -> List[str]:
    """
    Validate that required fields are present and non-empty in data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of missing or empty fields
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(f"Missing field: {field}")
        elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(f"Empty field: {field}")
    
    return missing_fields


def validate_organization_profile(profile_data: dict) -> List[str]:
    """
    Comprehensive validation of organization profile data.
    
    Args:
        profile_data: Organization profile dictionary
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Required fields
    required_fields = ['ein', 'name', 'state']
    errors.extend(validate_data_completeness(profile_data, required_fields))
    
    # EIN validation
    if 'ein' in profile_data:
        if not validate_ein(profile_data['ein']):
            errors.append("Invalid EIN format")
    
    # State validation
    if 'state' in profile_data:
        if not validate_state_code(profile_data['state']):
            errors.append("Invalid state code")
    
    # NTEE code validation
    if 'ntee_code' in profile_data and profile_data['ntee_code']:
        if not validate_ntee_code(profile_data['ntee_code']):
            errors.append("Invalid NTEE code format")
    
    # ZIP code validation
    if 'zip_code' in profile_data and profile_data['zip_code']:
        if not validate_zip_code(profile_data['zip_code']):
            errors.append("Invalid ZIP code format")
    
    # Website validation
    if 'website' in profile_data and profile_data['website']:
        if not validate_url(profile_data['website']):
            errors.append("Invalid website URL")
    
    # Financial data validation
    financial_fields = ['revenue', 'assets', 'expenses', 'net_assets', 'program_expenses']
    for field in financial_fields:
        if field in profile_data and profile_data[field] is not None:
            if not validate_financial_amount(profile_data[field]):
                errors.append(f"Invalid financial amount for {field}")
    
    # Ratio validation
    ratio_fields = ['program_expense_ratio', 'fundraising_efficiency', 'administrative_ratio']
    for field in ratio_fields:
        if field in profile_data and profile_data[field] is not None:
            if not validate_ratio(profile_data[field]):
                errors.append(f"Invalid ratio for {field} (must be between 0 and 1)")
    
    # Year validation
    if 'most_recent_filing_year' in profile_data and profile_data['most_recent_filing_year']:
        if not validate_year(profile_data['most_recent_filing_year']):
            errors.append("Invalid filing year")
    
    return errors


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


def validate_or_raise(validator_func: callable, value: Any, field_name: str = None) -> None:
    """
    Validate value with validator function and raise ValidationError if invalid.
    
    Args:
        validator_func: Validation function
        value: Value to validate
        field_name: Optional field name for error message
        
    Raises:
        ValidationError: If validation fails
    """
    if not validator_func(value):
        field_part = f" for field '{field_name}'" if field_name else ""
        raise ValidationError(f"Invalid value{field_part}: {value}", field_name, value)