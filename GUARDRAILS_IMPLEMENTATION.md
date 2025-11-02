# Guardrails Implementation Summary

## Overview
Basic guardrails have been added to the Legal Redline Sandbox project to improve security, prevent abuse, and ensure data quality.

## Files Created/Modified

### 1. New Files Created

#### `/utils/guardrails.py` (NEW)
Comprehensive guardrails module with the following components:

**InputValidator**
- Text input validation (max length, suspicious content detection)
- File path validation (prevents path traversal, validates extensions)
- Numeric parameter validation (range checking)
- Text sanitization (removes harmful content)

**RateLimiter**
- Request rate limiting (configurable per time window)
- Quota tracking per identifier (user/IP)
- Automatic cleanup of old requests

**ContentFilter**
- Forbidden content detection
- PII detection (SSN, credit cards, emails, phones)
- Legal context validation

**APIGuardrails**
- API key validation
- Token estimation and limit checking
- Retry configuration

**Decorators**
- `@require_validation` - Automatic input validation
- `@rate_limit` - Automatic rate limiting

#### `/utils/GUARDRAILS_README.md` (NEW)
Comprehensive documentation including:
- Feature descriptions
- Usage examples
- Configuration options
- Integration guides
- Best practices

#### `/backend/guardrails/input_validation.py` (UPDATED)
Backend-specific validation functions that use the core guardrails:
- `validate_document_upload()` - Validates file uploads
- `validate_clause_rewrite_request()` - Validates rewrite requests
- `validate_chat_request()` - Validates chat messages

### 2. Files Modified

#### `/utils/chatbot.py`
**Added:**
- Input validation for prompts (max 10,000 chars)
- Text sanitization for user inputs
- Rate limiting (50 requests/60 seconds)
- Token limit checking before API calls
- Validation for both general and document-context responses

**Impact:**
- Prevents malicious input injection
- Controls API usage costs
- Ensures prompts don't exceed token limits

#### `/utils/pdf_processor.py`
**Added:**
- File path validation
- File size limits (max 50MB)
- Page count limits (max 500 pages)
- Legal content validation
- PII detection warnings
- Existence and permission checks

**Impact:**
- Prevents processing of malicious files
- Limits resource usage
- Warns about potential privacy issues

#### `/utils/clause_rewriter.py`
**Added:**
- Clause text validation (max 50,000 chars)
- Numeric parameter validation
  - notice_days: 1-365
  - late_fee_percent: 0-100
- Rate limiting (30 requests/60 seconds)
- Error handling with detailed messages

**Impact:**
- Prevents invalid rewrite requests
- Ensures reasonable parameter values
- Controls API usage

#### `/utils/risk_detector.py`
**Added:**
- Document structure validation
- Clause count limits (max 200)
- Clause text validation
- Forbidden content detection
- Rate limiting (20 requests/60 seconds)
- Graceful handling of invalid clauses

**Impact:**
- Prevents processing of malformed documents
- Controls resource usage on large documents
- Detects potentially harmful content

## Security Features Implemented

### 1. Input Validation
✅ Length limits on all text inputs
✅ Detection of code injection attempts (script tags, eval, etc.)
✅ File extension whitelisting
✅ Path traversal prevention
✅ Numeric range validation

### 2. Rate Limiting
✅ Per-user request limits
✅ Configurable time windows
✅ Automatic quota tracking
✅ Applied to all expensive operations:
  - Chatbot responses
  - Clause rewrites
  - Risk analysis
  - Document processing

### 3. Content Filtering
✅ PII detection (SSN, credit cards, emails, phones)
✅ Forbidden term detection
✅ Legal context validation
✅ HTML/script tag removal

### 4. Resource Management
✅ File size limits (50MB)
✅ Page count limits (500 pages)
✅ Clause count limits (200 clauses)
✅ Token limits (100,000 tokens)
✅ Text length limits (1MB)

## Configuration

All limits are configurable through class constants:

```python
# Input Validation
InputValidator.MAX_TEXT_LENGTH = 1_000_000
InputValidator.MAX_PROMPT_LENGTH = 10_000
InputValidator.MAX_FILENAME_LENGTH = 255
InputValidator.MAX_CLAUSE_LENGTH = 50_000
InputValidator.ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.doc', '.docx'}

# Rate Limiting
RateLimiter(max_requests=100, time_window=60)

# API Guardrails
APIGuardrails.MAX_TOKENS = 100_000
APIGuardrails.MAX_RETRIES = 3
```

## Usage Examples

### Basic Input Validation
```python
from utils.guardrails import InputValidator

is_valid, error = InputValidator.validate_text_input(user_text)
if not is_valid:
    return {"error": error}
```

### Rate Limiting
```python
from utils.guardrails import rate_limit

@rate_limit(max_requests=10, time_window=60)
def expensive_operation(user_id):
    # Limited to 10 calls per minute per user
    pass
```

### Content Filtering
```python
from utils.guardrails import ContentFilter

pii = ContentFilter.detect_pii(document_text)
if pii:
    print(f"Warning: PII detected: {pii}")
```

## Testing

Run the guardrails test suite:

```bash
# Test core guardrails
python -m utils.guardrails

# Test backend validation
python -m backend.guardrails.input_validation
```

## Next Steps (Optional Enhancements)

1. **Logging & Monitoring**
   - Add structured logging for security events
   - Track rate limit violations
   - Monitor PII detection incidents

2. **Advanced Rate Limiting**
   - Redis-based distributed rate limiting
   - Different limits for different user tiers
   - Burst allowance

3. **Enhanced Content Filtering**
   - ML-based content classification
   - Custom legal term validation
   - Context-aware PII redaction

4. **API Integration**
   - Integrate with external security services
   - Virus scanning for uploaded files
   - Advanced threat detection

5. **Audit Trail**
   - Log all validation failures
   - Track document processing history
   - User activity monitoring

## Benefits

✅ **Security**: Prevents injection attacks and malicious inputs
✅ **Cost Control**: Rate limiting prevents API abuse
✅ **Privacy**: Detects and warns about PII
✅ **Reliability**: Validates data before processing
✅ **Scalability**: Limits resource usage per request
✅ **Compliance**: Helps meet data protection requirements

## Maintenance

- Review and update `SUSPICIOUS_PATTERNS` regularly
- Monitor rate limit thresholds and adjust as needed
- Update `PII_PATTERNS` for new regulations
- Test guardrails with real-world scenarios

## Documentation

- Main documentation: `/utils/GUARDRAILS_README.md`
- API documentation: Docstrings in `/utils/guardrails.py`
- Backend integration: `/backend/guardrails/input_validation.py`

---

**Implementation Date**: November 2, 2025
**Status**: ✅ Complete - Basic guardrails implemented and integrated
**Test Coverage**: Manual testing scripts included
