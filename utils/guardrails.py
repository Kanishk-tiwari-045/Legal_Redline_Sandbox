"""
Guardrails module for input validation, security, and content filtering
Provides protective measures for AI-powered legal document processing
"""

import re
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from functools import wraps
from collections import defaultdict, deque


class InputValidator:
    """Validates and sanitizes user inputs"""
    
    # Maximum lengths for different input types
    MAX_TEXT_LENGTH = 1_000_000  # ~1MB of text
    MAX_PROMPT_LENGTH = 10_000
    MAX_FILENAME_LENGTH = 255
    MAX_CLAUSE_LENGTH = 50_000
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.doc', '.docx'}
    
    # Suspicious patterns that could indicate injection attacks
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'<iframe[^>]*>',  # Iframes
        r'eval\s*\(',  # Eval calls
        r'exec\s*\(',  # Exec calls
        r'\$\{.*?\}',  # Template literals (potential code injection)
        r'`.*?`',  # Backticks (template strings)
    ]
    
    @staticmethod
    def validate_text_input(text: str, max_length: int = None) -> Tuple[bool, str]:
        """
        Validate text input for length and suspicious content
        
        Args:
            text: Input text to validate
            max_length: Maximum allowed length (default: MAX_TEXT_LENGTH)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(text, str):
            return False, "Input must be a string"
        
        if not text or not text.strip():
            return False, "Input cannot be empty"
        
        max_len = max_length or InputValidator.MAX_TEXT_LENGTH
        if len(text) > max_len:
            return False, f"Input exceeds maximum length of {max_len} characters"
        
        # Check for suspicious patterns
        for pattern in InputValidator.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "Input contains potentially unsafe content"
        
        return True, ""
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        Validate file path for security issues
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(file_path, str):
            return False, "File path must be a string"
        
        if not file_path or not file_path.strip():
            return False, "File path cannot be empty"
        
        # Check for path traversal attempts
        if '..' in file_path or file_path.startswith('/etc/') or file_path.startswith('/root/'):
            return False, "Invalid file path: potential security risk"
        
        # Check filename length
        filename = os.path.basename(file_path)
        if len(filename) > InputValidator.MAX_FILENAME_LENGTH:
            return False, f"Filename exceeds maximum length of {InputValidator.MAX_FILENAME_LENGTH}"
        
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        if ext not in InputValidator.ALLOWED_EXTENSIONS:
            return False, f"File type '{ext}' not allowed. Allowed types: {', '.join(InputValidator.ALLOWED_EXTENSIONS)}"
        
        return True, ""
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text by removing potentially harmful content
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove HTML/script tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove potential code execution patterns
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def validate_numeric_parameter(value: Any, min_val: float = None, max_val: float = None) -> Tuple[bool, str]:
        """
        Validate numeric parameters
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            return False, "Value must be a number"
        
        if min_val is not None and num_value < min_val:
            return False, f"Value must be at least {min_val}"
        
        if max_val is not None and num_value > max_val:
            return False, f"Value must be at most {max_val}"
        
        return True, ""


class RateLimiter:
    """Rate limiting to prevent abuse and manage API costs"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(deque)
    
    def is_allowed(self, identifier: str) -> Tuple[bool, str]:
        """
        Check if request is allowed
        
        Args:
            identifier: Unique identifier (e.g., user_id, IP address)
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        now = time.time()
        user_requests = self.requests[identifier]
        
        # Remove old requests outside the time window
        while user_requests and user_requests[0] < now - self.time_window:
            user_requests.popleft()
        
        # Check if limit exceeded
        if len(user_requests) >= self.max_requests:
            return False, f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.time_window} seconds."
        
        # Add current request
        user_requests.append(now)
        return True, ""
    
    def get_remaining_quota(self, identifier: str) -> int:
        """Get remaining quota for identifier"""
        now = time.time()
        user_requests = self.requests[identifier]
        
        # Clean old requests
        while user_requests and user_requests[0] < now - self.time_window:
            user_requests.popleft()
        
        return max(0, self.max_requests - len(user_requests))


class ContentFilter:
    """Filters and validates content for appropriateness"""
    
    # Patterns that should not appear in legal documents
    FORBIDDEN_TERMS = [
        r'\b(hack|exploit|bypass|circumvent)\s+(security|system)\b',
        r'\b(illegal|unlawful)\s+(activity|action|purpose)\b',
        r'\bmalware\b',
        r'\bransomware\b',
    ]
    
    # Patterns indicating PII that should be warned about
    PII_PATTERNS = {
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    }
    
    @staticmethod
    def check_forbidden_content(text: str) -> Tuple[bool, List[str]]:
        """
        Check if text contains forbidden content
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (has_forbidden_content, list_of_issues)
        """
        issues = []
        
        for pattern in ContentFilter.FORBIDDEN_TERMS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Text contains forbidden term matching pattern: {pattern}")
        
        return len(issues) > 0, issues
    
    @staticmethod
    def detect_pii(text: str) -> Dict[str, int]:
        """
        Detect potential PII in text
        
        Args:
            text: Text to scan
            
        Returns:
            Dictionary with PII types and counts
        """
        pii_found = {}
        
        for pii_type, pattern in ContentFilter.PII_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                pii_found[pii_type] = len(matches)
        
        return pii_found
    
    @staticmethod
    def validate_legal_context(text: str) -> Tuple[bool, str]:
        """
        Validate that text appears to be legal/contract content
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check minimum length
        if len(text.strip()) < 50:
            return False, "Text too short to be a valid legal document"
        
        # Check for common legal terms (at least one should be present)
        legal_terms = [
            'agreement', 'contract', 'party', 'parties', 'clause', 'section',
            'terms', 'conditions', 'hereby', 'whereas', 'herein', 'therefore',
            'shall', 'liability', 'indemnify', 'terminate', 'jurisdiction'
        ]
        
        text_lower = text.lower()
        found_terms = sum(1 for term in legal_terms if term in text_lower)
        
        if found_terms < 2:
            return False, "Text does not appear to contain legal content"
        
        return True, ""


class APIGuardrails:
    """Guardrails for AI API calls"""
    
    MAX_TOKENS = 100_000  # Maximum tokens per request
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, str]:
        """
        Validate API key format
        
        Args:
            api_key: API key to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not api_key or not isinstance(api_key, str):
            return False, "API key must be a non-empty string"
        
        if len(api_key) < 20:
            return False, "API key appears to be invalid (too short)"
        
        if api_key.startswith('sk-') or api_key.startswith('AIza'):
            return True, ""
        
        # Generic validation for other formats
        if len(api_key) >= 20 and re.match(r'^[A-Za-z0-9_-]+$', api_key):
            return True, ""
        
        return False, "API key format appears invalid"
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count (rough approximation)
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    @staticmethod
    def check_token_limit(text: str) -> Tuple[bool, str]:
        """
        Check if text exceeds token limit
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_within_limit, message)
        """
        estimated_tokens = APIGuardrails.estimate_tokens(text)
        
        if estimated_tokens > APIGuardrails.MAX_TOKENS:
            return False, f"Text exceeds maximum token limit ({estimated_tokens} > {APIGuardrails.MAX_TOKENS})"
        
        return True, ""


def require_validation(validator_func):
    """
    Decorator to add input validation to functions
    
    Usage:
        @require_validation(InputValidator.validate_text_input)
        def process_text(text: str):
            # Function implementation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate first argument
            if args:
                is_valid, error = validator_func(args[0])
                if not is_valid:
                    raise ValueError(f"Validation failed: {error}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_requests: int = 100, time_window: int = 60):
    """
    Decorator to add rate limiting to functions
    
    Usage:
        @rate_limit(max_requests=10, time_window=60)
        def api_call(user_id: str):
            # Function implementation
    """
    limiter = RateLimiter(max_requests, time_window)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use first argument as identifier
            identifier = args[0] if args else "default"
            is_allowed, error = limiter.is_allowed(str(identifier))
            if not is_allowed:
                raise PermissionError(error)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Singleton instances for global use
global_rate_limiter = RateLimiter(max_requests=100, time_window=60)
input_validator = InputValidator()
content_filter = ContentFilter()
api_guardrails = APIGuardrails()


if __name__ == "__main__":
    # Test the guardrails
    print("Testing Input Validation...")
    
    # Test text validation
    valid_text = "This is a valid contract agreement between parties."
    is_valid, error = InputValidator.validate_text_input(valid_text)
    print(f"Valid text: {is_valid}, Error: {error}")
    
    # Test suspicious content
    suspicious_text = "<script>alert('xss')</script>"
    is_valid, error = InputValidator.validate_text_input(suspicious_text)
    print(f"Suspicious text: {is_valid}, Error: {error}")
    
    # Test file path validation
    valid_path = "/home/user/document.pdf"
    is_valid, error = InputValidator.validate_file_path(valid_path)
    print(f"Valid path: {is_valid}, Error: {error}")
    
    invalid_path = "../../../etc/passwd"
    is_valid, error = InputValidator.validate_file_path(invalid_path)
    print(f"Invalid path: {is_valid}, Error: {error}")
    
    # Test content filtering
    legal_text = "This agreement shall govern the terms and conditions between the parties."
    is_valid, msg = ContentFilter.validate_legal_context(legal_text)
    print(f"Legal context: {is_valid}, Message: {msg}")
    
    # Test PII detection
    text_with_pii = "Contact me at john@example.com or 555-123-4567"
    pii = ContentFilter.detect_pii(text_with_pii)
    print(f"PII detected: {pii}")
    
    print("\nGuardrails module ready!")
