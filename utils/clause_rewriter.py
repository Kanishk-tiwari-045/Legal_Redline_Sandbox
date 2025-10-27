import json
import os
from typing import Dict, Any
from google import genai
from google.genai import types

class ClauseRewriter:
    """Generates AI-powered clause rewrites using Gemini"""
    
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-pro"
    
    def suggest_rewrite(self, clause: Dict[str, Any], controls: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a rewritten version of the clause with AI"""
        
        try:
            # Build the prompt with context and constraints
            system_prompt = """You are an expert contract analyst and legal writer. 
Your task is to rewrite problematic contract clauses to make them more fair and balanced.

CRITICAL REQUIREMENTS:
1. NEVER include code, programming syntax, or technical errors in your output
2. Output ONLY clean, professional legal text
3. Use proper contract language and formatting
4. Ensure all text is grammatically correct and legally sound

Guidelines:
- Maintain the original intent and legal effect where possible
- Make language clearer and more straightforward
- Reduce unfair advantages for one party
- Consider the user's specified parameters
- Provide clear rationale for changes
- Suggest fallback negotiation positions

Always respond with valid JSON in this exact format:
{
    "rewrite": "The rewritten clause text - MUST be clean legal text only",
    "rationale": "Explanation of why changes were made",
    "fallback_levels": [
        "Most customer-favorable version",
        "Balanced compromise version", 
        "Minimal change version"
    ],
    "risk_reduction": "How this reduces risk",
    "citation": "Reference to original clause"
}"""

            user_prompt = f"""
Please rewrite the following contract clause according to the specified controls:

**ORIGINAL CLAUSE:**
Title: {clause['title']}
Text: {clause['text']}
Page: {clause['page']}
Current Risk Score: {clause['risk_analysis']['score']}
Risk Factors: {', '.join(clause['risk_analysis']['tags'])}

**REWRITE CONTROLS:**
- Notice Period: {controls.get('notice_days', 30)} days
- Late Fee Percentage: {controls.get('late_fee_percent', 5.0)}%
- Jurisdiction Neutral: {controls.get('jurisdiction_neutral', True)}
- Favor Customer: {controls.get('favor_customer', True)}

**CRITICAL REQUIREMENTS:**
1. OUTPUT ONLY CLEAN LEGAL TEXT - NO CODE OR TECHNICAL ERRORS
2. Keep the rewrite roughly the same length as the original
3. Use plain, professional contract language
4. Apply the specified numerical parameters where relevant
5. Make the clause more balanced and fair
6. Provide three fallback negotiation positions in plain text
7. Ensure all text is grammatically correct and legally sound

**EXAMPLE GOOD OUTPUT:**
"This Agreement shall continue for an initial term of one (1) year. Either party may choose not to renew by providing sixty (60) days written notice prior to the expiration date."

**AVOID:** Any programming code, syntax errors, or technical formatting issues."""

            # Make API call to Gemini with retry logic for rate limits
            max_retries = 2
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries + 1):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[
                            types.Content(role="user", parts=[types.Part(text=user_prompt)])
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            temperature=0.3,  # Lower temperature for more consistent legal writing
                            max_output_tokens=2000
                        ),
                    )
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries:
                        # Rate limit hit, wait and retry
                        import time
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        # Either not a rate limit error, or we've exhausted retries
                        raise e
            
            if not response.text:
                raise Exception("Empty response from Gemini API")
            
            # Parse the JSON response
            try:
                result = json.loads(response.text)
                
                # Validate required fields
                required_fields = ['rewrite', 'rationale', 'fallback_levels', 'risk_reduction', 'citation']
                for field in required_fields:
                    if field not in result:
                        result[field] = f"[{field} not provided]"
                
                # Add metadata
                result['original_clause_id'] = clause['clause_id']
                result['controls_used'] = controls
                result['api_model'] = self.model_name
                
                return result
                
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                return {
                    'rewrite': f"Error parsing AI response. Raw response: {response.text[:500]}...",
                    'rationale': f"JSON parsing failed: {str(e)}",
                    'fallback_levels': ["Unable to generate fallback options"],
                    'risk_reduction': "Unable to assess risk reduction",
                    'citation': f"Original: {clause['title']}, Page {clause['page']}",
                    'original_clause_id': clause['clause_id'],
                    'controls_used': controls,
                    'api_model': self.model_name,
                    'error': True
                }
            
        except Exception as e:
            # Handle API errors gracefully
            return {
                'rewrite': f"Unable to generate rewrite due to API error: {str(e)}",
                'rationale': "API request failed. Please check your internet connection and API key.",
                'fallback_levels': ["Unable to generate options due to API error"],
                'risk_reduction': "Unable to assess - API error occurred",
                'citation': f"Original: {clause['title']}, Page {clause['page']}",
                'original_clause_id': clause['clause_id'],
                'controls_used': controls,
                'api_model': self.model_name,
                'error': True,
                'error_details': str(e)
            }
    
    def batch_rewrite(self, clauses: list, controls: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Rewrite multiple clauses at once"""
        results = {}
        
        for clause in clauses:
            try:
                results[clause['clause_id']] = self.suggest_rewrite(clause, controls)
            except Exception as e:
                results[clause['clause_id']] = {
                    'error': True,
                    'error_message': str(e),
                    'original_clause_id': clause['clause_id']
                }
        
        return results
    
    def validate_rewrite(self, original: str, rewrite: str) -> Dict[str, Any]:
        """Validate that a rewrite maintains essential legal meaning"""
        
        # Basic validation checks
        validation_results = {
            'length_similar': abs(len(original.split()) - len(rewrite.split())) <= len(original.split()) * 0.5,
            'key_terms_preserved': self._check_key_terms_preserved(original, rewrite),
            'readability_improved': len(rewrite.split()) > 0,  # Basic check
            'valid': True
        }
        
        validation_results['valid'] = all([
            validation_results['length_similar'],
            validation_results['key_terms_preserved'],
            validation_results['readability_improved']
        ])
        
        return validation_results
    
    def _check_key_terms_preserved(self, original: str, rewrite: str) -> bool:
        """Check if key legal terms are preserved"""
        # Key legal terms that should typically be preserved
        key_terms = [
            'terminate', 'termination', 'notice', 'liability', 'damages',
            'breach', 'default', 'agreement', 'contract', 'party', 'parties'
        ]
        
        original_lower = original.lower()
        rewrite_lower = rewrite.lower()
        
        preserved_count = 0
        total_found = 0
        
        for term in key_terms:
            if term in original_lower:
                total_found += 1
                if term in rewrite_lower:
                    preserved_count += 1
        
        # If no key terms found, consider it preserved
        if total_found == 0:
            return True
        
        # At least 70% of key terms should be preserved
        return (preserved_count / total_found) >= 0.7
