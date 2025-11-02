"""
Backend input validation - uses the comprehensive guardrails from utils
This module provides validation for backend API endpoints
"""

import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.guardrails import (
    InputValidator,
    RateLimiter,
    ContentFilter,
    APIGuardrails,
    rate_limit,
    require_validation
)

# Re-export for convenience
__all__ = [
    'InputValidator',
    'RateLimiter', 
    'ContentFilter',
    'APIGuardrails',
    'rate_limit',
    'require_validation',
    'validate_document_upload',
    'validate_clause_rewrite_request',
    'validate_chat_request'
]


def validate_document_upload(file_path: str, max_size_mb: int = 50) -> tuple[bool, str]:
    """
    Validate document upload request
    
    Args:
        file_path: Path to uploaded file
        max_size_mb: Maximum file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate file path
    is_valid, error = InputValidator.validate_file_path(file_path)
    if not is_valid:
        return False, error
    
    # Check file exists
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    # Check file size
    file_size = os.path.getsize(file_path)
    max_size = max_size_mb * 1024 * 1024
    if file_size > max_size:
        return False, f"File size ({file_size / (1024*1024):.2f}MB) exceeds limit ({max_size_mb}MB)"
    
    return True, ""


def validate_clause_rewrite_request(clause_text: str, controls: dict) -> tuple[bool, str]:
    """
    Validate clause rewrite request
    
    Args:
        clause_text: Text of the clause
        controls: Rewrite control parameters
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate clause text
    is_valid, error = InputValidator.validate_text_input(
        clause_text, 
        max_length=InputValidator.MAX_CLAUSE_LENGTH
    )
    if not is_valid:
        return False, f"Invalid clause text: {error}"
    
    # Validate controls
    if not isinstance(controls, dict):
        return False, "Controls must be a dictionary"
    
    # Validate numeric parameters
    if 'notice_days' in controls:
        is_valid, error = InputValidator.validate_numeric_parameter(
            controls['notice_days'], min_val=1, max_val=365
        )
        if not is_valid:
            return False, f"Invalid notice_days: {error}"
    
    if 'late_fee_percent' in controls:
        is_valid, error = InputValidator.validate_numeric_parameter(
            controls['late_fee_percent'], min_val=0, max_val=100
        )
        if not is_valid:
            return False, f"Invalid late_fee_percent: {error}"
    
    return True, ""


def validate_chat_request(message: str, chat_history: list = None) -> tuple[bool, str]:
    """
    Validate chat request
    
    Args:
        message: User message
        chat_history: Chat history list
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate message
    is_valid, error = InputValidator.validate_text_input(
        message,
        max_length=InputValidator.MAX_PROMPT_LENGTH
    )
    if not is_valid:
        return False, f"Invalid message: {error}"
    
    # Validate chat history
    if chat_history is not None:
        if not isinstance(chat_history, list):
            return False, "Chat history must be a list"
        
        if len(chat_history) > 100:
            return False, "Chat history too long (max 100 messages)"
        
        for msg in chat_history:
            if not isinstance(msg, dict):
                return False, "Chat history messages must be dictionaries"
            if 'role' not in msg or 'content' not in msg:
                return False, "Chat history messages must have 'role' and 'content'"
    
    return True, ""


if __name__ == "__main__":
    print("Backend Input Validation Module")
    print("=" * 50)
    
    # Test document validation
    print("\n1. Testing document upload validation...")
    is_valid, error = validate_document_upload("/tmp/test.pdf")
    print(f"Result: {is_valid}, Error: {error}")
    
    # Test clause rewrite validation
    print("\n2. Testing clause rewrite validation...")
    clause = "This agreement shall automatically renew unless terminated."
    controls = {"notice_days": 30, "late_fee_percent": 5.0}
    is_valid, error = validate_clause_rewrite_request(clause, controls)
    print(f"Result: {is_valid}, Error: {error}")
    
    # Test chat validation
    print("\n3. Testing chat request validation...")
    message = "What are the key risks in this contract?"
    is_valid, error = validate_chat_request(message)
    print(f"Result: {is_valid}, Error: {error}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
