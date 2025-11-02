import re
import json
import os
from typing import Dict, List, Any, Tuple
from google import genai
from google.genai import types


class RiskDetector:
    """Detects risky clauses in legal documents using AI-powered legal analysis"""
    
    def __init__(self):
        # Initialize Gemini client for AI-powered risk analysis
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.use_ai = True
        else:
            self.client = None
            self.use_ai = False
            print("Warning: GEMINI_API_KEY not found, falling back to pattern-based analysis")
        self.risk_patterns = {
            'auto_renew': {
                'patterns': [
                    r'auto(?:matic)?(?:ally)?\s*renew',
                    r'renews?\s*(?:automatically|unless)',
                    r'automatic\s*(?:extension|renewal)',
                    r'shall\s*continue\s*unless\s*terminated'
                ],
                'score': 3,
                'rationale': "Auto-renewal clauses can trap parties in unwanted contract extensions."
            },
            'unilateral_change': {
                'patterns': [
                    r'(?:provider|company|we)\s*(?:may|can|shall)\s*modify.*without\s*(?:notice|consent)',
                    r'unilateral(?:ly)?\s*(?:change|modify|alter)',
                    r'at\s*(?:our|company\'s)\s*(?:sole\s*)?discretion',
                    r'right\s*to\s*(?:change|modify).*without\s*(?:notice|consent)'
                ],
                'score': 4,
                'rationale': "Unilateral modification rights create power imbalances and unpredictability."
            },
            'short_notice': {
                'patterns': [
                    r'(?:notice|notification)\s*(?:period\s*)?(?:of\s*)?(?:less\s*than\s*)?(\d+)\s*days?',
                    r'(\d+)\s*days?\s*(?:prior\s*)?notice',
                    r'terminate.*(?:with|upon)\s*(\d+)\s*days?\s*notice'
                ],
                'score': 2,
                'rationale': "Short notice periods may not provide adequate time to respond or find alternatives.",
                'threshold_check': True
            },
            'high_penalty': {
                'patterns': [
                    r'(?:penalty|fee|charge).*(\d+(?:\.\d+)?)%',
                    r'liquidated\s*damages.*(\d+(?:\.\d+)?)%',
                    r'late\s*(?:payment\s*)?(?:fee|charge).*(\d+(?:\.\d+)?)%'
                ],
                'score': 3,
                'rationale': "High penalty percentages can result in disproportionate financial consequences.",
                'threshold_check': True
            },
            'exclusive_jurisdiction': {
                'patterns': [
                    r'exclusive\s*jurisdiction',
                    r'binding\s*arbitration',
                    r'waive.*right.*jury\s*trial',
                    r'disputes\s*shall\s*be\s*resolved\s*(?:exclusively\s*)?in'
                ],
                'score': 2,
                'rationale': "Exclusive jurisdiction clauses may limit legal options and increase costs."
            },
            'liability_limitation': {
                'patterns': [
                    r'(?:limit|exclude|disclaim).*liability',
                    r'in\s*no\s*event.*liable',
                    r'maximum\s*liability.*(?:shall\s*not\s*exceed|limited\s*to)',
                    r'consequential\s*damages.*(?:excluded|disclaimed)'
                ],
                'score': 3,
                'rationale': "Liability limitations may prevent fair compensation for damages."
            },
            'broad_termination': {
                'patterns': [
                    r'terminate.*(?:for\s*any\s*reason|at\s*any\s*time)',
                    r'(?:immediate|without\s*cause)\s*termination',
                    r'terminate.*without.*(?:notice|cause|reason)'
                ],
                'score': 3,
                'rationale': "Broad termination rights create uncertainty and potential for abuse."
            }
        }
    
    def analyze_document(self, document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze all clauses in the document for risks"""
        risky_clauses = []
        
        print(f"Analyzing {len(document_data['clauses'])} clauses...")
        
        for i, clause in enumerate(document_data['clauses']):
            risk_analysis = self._analyze_clause(clause)
            print(f"Clause {i+1} '{clause['title'][:50]}...' - Score: {risk_analysis['score']}, Tags: {risk_analysis['tags']}")
            
            if risk_analysis['score'] >= 1:  # Temporarily lower threshold for debugging
                clause_with_risk = clause.copy()
                clause_with_risk['risk_analysis'] = risk_analysis
                risky_clauses.append(clause_with_risk)
        
        print(f"Found {len(risky_clauses)} risky clauses")
        
        # Sort by risk score (highest first)
        risky_clauses.sort(key=lambda x: x['risk_analysis']['score'], reverse=True)
        
        return risky_clauses
    
    def _analyze_clause(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single clause for risks using AI when available, fallback to pattern matching"""
        
        if self.use_ai:
            return self._ai_analyze_clause(clause)
        else:
            return self._pattern_analyze_clause(clause)
    
    def _ai_analyze_clause(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to analyze clause for legal risks and disadvantages"""
        try:
            system_prompt = """You are an expert legal analyst specializing in contract risk assessment. 
            Analyze the provided contract clause and identify all potential legal risks, disadvantages, 
            privacy concerns, and unfair terms.
            
            Focus on:
            1. Legal disadvantages to one party
            2. Privacy and data protection risks  
            3. Unfair termination conditions
            4. Excessive penalties or liability limitations
            5. Jurisdictional disadvantages
            6. Automatic renewals or binding terms
            7. Unilateral change rights
            8. Vague or ambiguous language that could be exploited
            9. Financial risks and fee structures
            10. Dispute resolution limitations
            
            Respond with JSON in this exact format:
            {
                "risk_score": <integer from 0-5>,
                "risk_tags": ["tag1", "tag2"],
                "risk_summary": "Brief summary of main risks",
                "legal_disadvantages": "Specific legal disadvantages identified",
                "privacy_concerns": "Data privacy and protection issues",
                "unfair_terms": "Terms that create imbalance between parties",
                "recommendations": "How to address these risks"
            }"""
            
            user_prompt = f"""Analyze this contract clause for legal risks and disadvantages:

**CLAUSE TITLE:** {clause['title']}

**CLAUSE TEXT:**
{clause['text']}

**ANALYSIS REQUEST:**
Provide a comprehensive legal risk assessment focusing on actual legal disadvantages, 
privacy risks, and unfair terms rather than just sentence patterns. Consider how this 
clause could be used against one party and what legal protections it removes."""

            if not self.client:
                return self._pattern_analyze_clause(clause)
                
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.3
                ),
            )
            
            if response.text:
                ai_analysis = json.loads(response.text)
                
                # Convert AI analysis to our expected format
                return {
                    'score': ai_analysis.get('risk_score', 0),
                    'tags': ai_analysis.get('risk_tags', []),
                    'rationale': ai_analysis.get('risk_summary', ''),
                    'legal_disadvantages': ai_analysis.get('legal_disadvantages', ''),
                    'privacy_concerns': ai_analysis.get('privacy_concerns', ''),
                    'unfair_terms': ai_analysis.get('unfair_terms', ''),
                    'recommendations': ai_analysis.get('recommendations', '')
                }
                
        except Exception as e:
            print(f"AI analysis failed for clause '{clause['title']}': {str(e)}")
            return self._pattern_analyze_clause(clause)
        
        # Fallback in case no response
        return self._pattern_analyze_clause(clause)
    
    def _pattern_analyze_clause(self, clause: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback pattern-based analysis when AI is not available"""
        text = clause['text'].lower()
        title = clause.get('title', '').lower()
        
        tags = []
        total_score = 0
        rationales = []
        
        # Add some basic risk patterns for testing - check for common problematic terms
        basic_risk_keywords = [
            'terminate', 'cancel', 'penalty', 'fee', 'breach', 'default', 
            'liable', 'damages', 'exclusive', 'binding', 'waive', 'disclaim',
            'modify', 'change', 'alter', 'update', 'revise'
        ]
        
        # Check for basic risk indicators first
        basic_risk_found = any(keyword in text for keyword in basic_risk_keywords)
        if basic_risk_found:
            tags.append('general_risk')
            total_score += 1
            rationales.append("Contains terms that may indicate contractual risk")
        
        for risk_type, config in self.risk_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    tags.append(risk_type)
                    score_to_add = config['score']
                    
                    # Special handling for threshold-based risks
                    if config.get('threshold_check'):
                        if risk_type == 'short_notice':
                            days = self._extract_numbers_from_match(match)
                            if days and min(days) < 30:
                                score_to_add += 1  # Extra penalty for very short notice
                        elif risk_type == 'high_penalty':
                            percentages = self._extract_percentages_from_match(match)
                            if percentages and max(percentages) > 10:
                                score_to_add += 1  # Extra penalty for high percentages
                    
                    total_score += score_to_add
                    rationales.append(config['rationale'])
                    break  # Only count each risk type once per clause
        
        # Remove duplicates while preserving order
        seen_tags = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen_tags:
                unique_tags.append(tag)
                seen_tags.add(tag)
        
        # Remove duplicate rationales
        unique_rationales = list(dict.fromkeys(rationales))
        
        return {
            'tags': unique_tags,
            'score': min(total_score, 10),  # Cap at 10
            'rationale': ' '.join(unique_rationales) if unique_rationales else 'Potential risk identified through pattern matching.',
            'legal_disadvantages': '',
            'privacy_concerns': '',
            'unfair_terms': '',
            'recommendations': ''
        }
    
    def _extract_numbers_from_match(self, match) -> List[int]:
        """Extract numbers from a regex match"""
        numbers = []
        for group in match.groups():
            if group:
                try:
                    numbers.append(int(float(group)))
                except (ValueError, TypeError):
                    continue
        return numbers
    
    def _extract_percentages_from_match(self, match) -> List[float]:
        """Extract percentages from a regex match"""
        percentages = []
        for group in match.groups():
            if group:
                try:
                    percentages.append(float(group))
                except (ValueError, TypeError):
                    continue
        return percentages
    
    def get_risk_summary(self, risky_clauses: List[Dict]) -> Dict[str, Any]:
        """Generate a summary of risks found"""
        if not risky_clauses:
            return {'total_score': 0, 'risk_distribution': {}, 'avg_score': 0}
        
        total_score = sum(clause['risk_analysis']['score'] for clause in risky_clauses)
        risk_distribution = {}
        
        for clause in risky_clauses:
            for tag in clause['risk_analysis']['tags']:
                risk_distribution[tag] = risk_distribution.get(tag, 0) + 1
        
        return {
            'total_score': total_score,
            'risk_distribution': risk_distribution,
            'avg_score': total_score / len(risky_clauses),
            'highest_risk_clause': max(risky_clauses, key=lambda x: x['risk_analysis']['score'])
        }
