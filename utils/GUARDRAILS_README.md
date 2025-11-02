# Guardrails Module

This module provides comprehensive security and validation guardrails for the Legal Redline Sandbox application.

## Features

### 1. Input Validation (`InputValidator`)

Validates and sanitizes all user inputs to prevent security vulnerabilities and ensure data quality.

**Key Functions:**
- `validate_text_input(text, max_length)` - Validates text for length and suspicious content
- `validate_file_path(file_path)` - Validates file paths for security issues
- `validate_numeric_parameter(value, min_val, max_val)` - Validates numeric inputs
- `sanitize_text(text)` - Removes potentially harmful content from text

**Example:**
```python
from utils.guardrails import InputValidator

# Validate user input
is_valid, error = InputValidator.validate_text_input(user_text)
if not is_valid:
    print(f"Validation error: {error}")

# Sanitize text
clean_text = InputValidator.sanitize_text(user_input)
```

### 2. Rate Limiting (`RateLimiter`)

Prevents abuse and manages API costs by limiting request rates per user/identifier.

**Key Functions:**
- `is_allowed(identifier)` - Check if request is allowed
- `get_remaining_quota(identifier)` - Get remaining quota

**Decorator Usage:**
```python
from utils.guardrails import rate_limit

@rate_limit(max_requests=10, time_window=60)
def expensive_api_call(user_id: str):
    # This function is limited to 10 calls per minute per user
    pass
```

### 3. Content Filtering (`ContentFilter`)

Filters and validates content for appropriateness and legal context.

**Key Functions:**
- `check_forbidden_content(text)` - Check for forbidden terms
- `detect_pii(text)` - Detect personally identifiable information
- `validate_legal_context(text)` - Validate text appears to be legal content

**Example:**
```python
from utils.guardrails import ContentFilter

# Check for PII
pii_found = ContentFilter.detect_pii(document_text)
if pii_found:
    print(f"Warning: PII detected: {pii_found}")

# Validate legal context
is_legal, msg = ContentFilter.validate_legal_context(text)
```

### 4. API Guardrails (`APIGuardrails`)

Protects AI API calls with validation and rate limiting.

**Key Functions:**
- `validate_api_key(api_key)` - Validate API key format
- `estimate_tokens(text)` - Estimate token count
- `check_token_limit(text)` - Check if text exceeds token limit

**Example:**
```python
from utils.guardrails import APIGuardrails

# Check token limit before API call
is_within_limit, msg = APIGuardrails.check_token_limit(prompt)
if not is_within_limit:
    raise ValueError(msg)
```

## Configuration

### Maximum Limits

```python
# Input Validation
MAX_TEXT_LENGTH = 1_000_000  # ~1MB of text
MAX_PROMPT_LENGTH = 10_000
MAX_FILENAME_LENGTH = 255
MAX_CLAUSE_LENGTH = 50_000

# Rate Limiting
DEFAULT_MAX_REQUESTS = 100
DEFAULT_TIME_WINDOW = 60  # seconds

# API Guardrails
MAX_TOKENS = 100_000
MAX_RETRIES = 3
```

### Allowed File Types

Only the following file types are permitted:
- `.pdf`
- `.txt`
- `.doc`
- `.docx`

## Security Features

### 1. Injection Prevention

The module detects and blocks:
- Script tags (`<script>`)
- JavaScript protocol handlers
- Event handlers (`onclick`, etc.)
- Iframes
- Code evaluation attempts
- Template literal injection

### 2. Path Traversal Prevention

File path validation prevents:
- Directory traversal (`../../../`)
- Access to system files (`/etc/`, `/root/`)
- Excessively long filenames

### 3. PII Detection

Automatically detects:
- Social Security Numbers
- Credit Card Numbers
- Email Addresses
- Phone Numbers

## Integration Examples

### Protecting API Endpoints

```python
from utils.guardrails import InputValidator, rate_limit, ContentFilter

@rate_limit(max_requests=50, time_window=60)
def process_document(document_text: str, user_id: str):
    # Validate input
    is_valid, error = InputValidator.validate_text_input(document_text)
    if not is_valid:
        raise ValueError(f"Invalid input: {error}")
    
    # Check for legal content
    is_legal, msg = ContentFilter.validate_legal_context(document_text)
    if not is_legal:
        raise ValueError(f"Not legal content: {msg}")
    
    # Check for PII
    pii = ContentFilter.detect_pii(document_text)
    if pii:
        print(f"Warning: PII detected: {pii}")
    
    # Process document...
```

### Protecting File Uploads

```python
from utils.guardrails import InputValidator

def handle_file_upload(file_path: str):
    # Validate file path
    is_valid, error = InputValidator.validate_file_path(file_path)
    if not is_valid:
        raise ValueError(f"Invalid file: {error}")
    
    # Check file size
    if os.path.getsize(file_path) > 50 * 1024 * 1024:  # 50MB
        raise ValueError("File too large")
    
    # Process file...
```

### Protecting AI Prompts

```python
from utils.guardrails import InputValidator, APIGuardrails

def generate_ai_response(user_prompt: str, context: str):
    # Validate and sanitize prompt
    is_valid, error = InputValidator.validate_text_input(user_prompt, max_length=10000)
    if not is_valid:
        raise ValueError(f"Invalid prompt: {error}")
    
    user_prompt = InputValidator.sanitize_text(user_prompt)
    
    # Build full prompt
    full_prompt = f"{context}\n\nUser: {user_prompt}\nAssistant:"
    
    # Check token limit
    is_within_limit, msg = APIGuardrails.check_token_limit(full_prompt)
    if not is_within_limit:
        raise ValueError(msg)
    
    # Call AI API...
```

## Testing

Run the test suite:

```bash
python -m utils.guardrails
```

This will test:
- Text validation (valid and suspicious)
- File path validation (valid and invalid)
- Content filtering
- PII detection

## Best Practices

1. **Always validate user inputs** before processing
2. **Use rate limiting** on expensive operations (AI calls, document processing)
3. **Sanitize text** before displaying to users or storing
4. **Check for PII** when handling sensitive documents
5. **Validate file paths** before file operations
6. **Check token limits** before AI API calls
7. **Log security events** for monitoring and auditing

## Customization

You can customize limits by modifying the class constants:

```python
from utils.guardrails import InputValidator

# Customize max text length
InputValidator.MAX_TEXT_LENGTH = 500_000

# Add custom file extensions
InputValidator.ALLOWED_EXTENSIONS.add('.rtf')

# Add custom suspicious patterns
InputValidator.SUSPICIOUS_PATTERNS.append(r'custom_pattern')
```

## Error Handling

All validation functions return `(is_valid, error_message)` tuples:

```python
is_valid, error = InputValidator.validate_text_input(text)
if not is_valid:
    # Handle error
    log_error(error)
    return {"error": error}
```

Decorator-based functions raise exceptions:

```python
@rate_limit(max_requests=10, time_window=60)
def protected_function(user_id):
    # Will raise PermissionError if rate limit exceeded
    pass

try:
    protected_function(user_id)
except PermissionError as e:
    return {"error": str(e)}
```

## Dependencies

- Python 3.7+
- Standard library only (no external dependencies)

## License

This module is part of the Legal Redline Sandbox project.
