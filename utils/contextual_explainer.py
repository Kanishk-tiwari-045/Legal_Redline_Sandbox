"""
Contextual Explanation Engine using Google Cloud RAG Services
Demystifies legal jargon and provides contextual analysis of contract clauses
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from google.cloud import aiplatform
from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud.aiplatform import gapic as aiplatform_gapic
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LegalExplanation:
    """Structure for legal term explanations"""
    term: str
    plain_english: str
    legal_definition: str
    real_world_impact: str
    alternatives: List[str]
    risk_level: str
    citations: List[str]

@dataclass
class ClauseAnalysis:
    """Structure for comprehensive clause analysis"""
    clause_text: str
    key_terms: List[str]
    plain_english_summary: str
    potential_impacts: List[str]
    risk_factors: List[str]
    alternative_language: List[str]
    historical_context: str
    negotiation_tips: List[str]

class ContextualExplainer:
    """
    Advanced Legal Document Explanation Engine using Google Cloud RAG
    """
    
    def __init__(self):
        """Initialize the explainer with Google Cloud credentials"""
        try:
            # Load environment variables
            self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
            self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
            self.discovery_location = os.getenv("DISCOVERY_ENGINE_LOCATION", "global")
            
            if not self.project_id:
                logger.warning("GOOGLE_CLOUD_PROJECT_ID environment variable not set - running in fallback mode")
                self.project_id = None
                self.discovery_client = None
                self.use_rag = False
            else:
                # Initialize Vertex AI
                try:
                    aiplatform.init(project=self.project_id, location=self.location)
                    
                    # Initialize Discovery Engine client for RAG
                    self.discovery_client = discoveryengine.SearchServiceClient()
                    self.use_rag = True
                    
                    logger.info(f"Contextual Explainer initialized for project: {self.project_id}")
                except Exception as cloud_error:
                    logger.warning(f"Could not initialize Google Cloud services: {cloud_error}")
                    self.discovery_client = None
                    self.use_rag = False
                    
                # Knowledge base configuration
                self.knowledge_bases = {
                    "legal_definitions": f"projects/{self.project_id}/locations/{self.discovery_location}/collections/default_collection/dataStores/legal-definitions"
                } if self.project_id else {}
            
            # Legal terminology patterns for automatic detection
            self.legal_terms_patterns = self._load_legal_patterns()
            
        except Exception as e:
            logger.error(f"Failed to initialize Contextual Explainer: {e}")
            # Fallback to basic mode without GCP services
            self.project_id = None
            self.discovery_client = None
            self.use_rag = False
    
    def _load_legal_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for detecting legal terminology"""
        return {
            "contract_terms": [
                r'\b(?:force majeure|liquidated damages|indemnification|jurisdiction|arbitration)\b',
                r'\b(?:breach|default|termination|renewal|assignment)\b',
                r'\b(?:warranty|guarantee|representation|covenant)\b',
                r'\b(?:liability|damages|penalty|remedy|cure)\b'
            ],
            "temporal_terms": [
                r'\b(?:notice period|grace period|cooling-off period)\b',
                r'\b(?:effective date|expiration|renewal date)\b',
                r'\b(?:immediately|forthwith|upon notice)\b'
            ],
            "financial_terms": [
                r'\b(?:late fee|penalty|interest|liquidated damages)\b',
                r'\b(?:payment terms|invoice|billing|settlement)\b',
                r'\b(?:escrow|deposit|retainer|advance)\b'
            ],
            "legal_entities": [
                r'\b(?:party|parties|entity|corporation|LLC|partnership)\b',
                r'\b(?:principal|agent|fiduciary|trustee)\b',
                r'\b(?:beneficiary|assignee|successor)\b'
            ]
        }
    
    def explain_legal_term(self, term: str, context: str = "") -> LegalExplanation:
        """
        Explain a legal term using RAG from legal knowledge base
        """
        try:
            # Check if RAG is available
            if not self.use_rag or not self.discovery_client:
                logger.info(f"RAG not available, using fallback explanation for term: {term}")
                return self._fallback_legal_explanation(term)
            
            # Search legal definitions knowledge base
            definition_query = f"Define {term} in contract law context: {context}"
            definition_results = self._search_knowledge_base(
                "legal_definitions", 
                definition_query,
                max_results=3
            )
            
            # Search for real-world examples and impacts
            impact_query = f"Real world implications of {term} in contracts examples impact"
            impact_results = self._search_knowledge_base(
                "contract_examples",
                impact_query,
                max_results=3
            )
            
            # If no results from RAG, fall back to basic explanation
            if not definition_results and not impact_results:
                logger.info(f"No RAG results found for term: {term}, using fallback")
                return self._fallback_legal_explanation(term)
            
            # Generate explanation using Vertex AI with retrieved context
            explanation = self._generate_term_explanation(
                term, 
                context, 
                definition_results, 
                impact_results
            )
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining term '{term}': {e}")
            return self._fallback_legal_explanation(term)
    
    def analyze_clause_impact(self, clause_text: str) -> ClauseAnalysis:
        """
        Analyze the real-world impact of a contract clause
        """
        try:
            # Extract key legal terms from the clause
            key_terms = self._extract_legal_terms(clause_text)
            
            # Search for similar clauses and their outcomes
            similar_clause_query = f"Similar contract clauses outcomes precedents: {clause_text[:200]}"
            similar_results = self._search_knowledge_base(
                "case_law",
                similar_clause_query,
                max_results=5
            )
            
            # Search for alternative language examples
            alternatives_query = f"Alternative contract language fair balanced: {' '.join(key_terms)}"
            alternatives_results = self._search_knowledge_base(
                "contract_examples",
                alternatives_query,
                max_results=3
            )
            
            # Generate comprehensive analysis
            analysis = self._generate_clause_analysis(
                clause_text,
                key_terms,
                similar_results,
                alternatives_results
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing clause: {e}")
            return self._fallback_clause_analysis(clause_text)
    
    def suggest_plain_english_alternatives(self, clause_text: str) -> List[str]:
        """
        Suggest plain English alternatives for complex legal language
        """
        try:
            # Search for plain English contract examples
            plain_english_query = f"Plain English contract language simple clear: {clause_text[:200]}"
            plain_results = self._search_knowledge_base(
                "contract_examples",
                plain_english_query,
                max_results=5
            )
            
            # Generate alternatives using Vertex AI
            alternatives = self._generate_plain_english_alternatives(
                clause_text,
                plain_results
            )
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Error generating alternatives: {e}")
            return self._fallback_alternatives(clause_text)
    
    def get_historical_context(self, clause_text: str) -> str:
        """
        Provide historical context for how similar clauses have been interpreted
        """
        try:
            # Search case law for historical interpretations
            historical_query = f"Court interpretations case law precedents: {clause_text[:200]}"
            historical_results = self._search_knowledge_base(
                "case_law",
                historical_query,
                max_results=5
            )
            
            # Generate historical context summary
            context = self._generate_historical_context(
                clause_text,
                historical_results
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting historical context: {e}")
            return self._fallback_historical_context(clause_text)
    
    def _search_knowledge_base(self, kb_type: str, query: str, max_results: int = 5) -> List[Dict]:
        """Search a specific knowledge base using Discovery Engine"""
        try:
            # Check if RAG is available
            if not self.use_rag or not self.discovery_client:
                logger.info(f"RAG not available for knowledge base search: {kb_type}")
                return []
                
            if not self.knowledge_bases or kb_type not in self.knowledge_bases:
                logger.warning(f"Knowledge base {kb_type} not configured or available")
                return []
            
            # Create search request
            request = discoveryengine.SearchRequest(
                serving_config=f"{self.knowledge_bases[kb_type]}/servingConfigs/default_config",
                query=query,
                page_size=max_results,
                query_expansion_spec=discoveryengine.SearchRequest.QueryExpansionSpec(
                    condition=discoveryengine.SearchRequest.QueryExpansionSpec.Condition.AUTO,
                ),
                spell_correction_spec=discoveryengine.SearchRequest.SpellCorrectionSpec(
                    mode=discoveryengine.SearchRequest.SpellCorrectionSpec.Mode.AUTO
                )
            )
            
            # Execute search
            response = self.discovery_client.search(request)
            
            # Extract results
            results = []
            for result in response.results:
                doc = result.document
                results.append({
                    "title": doc.derived_struct_data.get("title", ""),
                    "content": doc.derived_struct_data.get("extractive_answers", [{}])[0].get("content", ""),
                    "snippet": doc.derived_struct_data.get("snippet", ""),
                    "uri": doc.derived_struct_data.get("link", ""),
                    "relevance_score": getattr(result, 'relevance_score', 0.0)
                })
            
            logger.info(f"Found {len(results)} results from knowledge base {kb_type}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base {kb_type}: {e}")
            # Return empty results instead of crashing
            return []
            return []
    
    def _generate_term_explanation(self, term: str, context: str, 
                                 definition_results: List[Dict], 
                                 impact_results: List[Dict]) -> LegalExplanation:
        """Generate comprehensive term explanation using Vertex AI"""
        try:
            # Prepare context from search results
            definitions_context = "\n".join([
                f"- {result['content']}" for result in definition_results[:3]
            ])
            
            impacts_context = "\n".join([
                f"- {result['content']}" for result in impact_results[:3]
            ])
            
            # Create prompt for Vertex AI
            prompt = f"""
            As a legal expert, explain the term "{term}" in simple, accessible language.
            
            Context where the term appears: {context}
            
            Legal definitions found:
            {definitions_context}
            
            Real-world impacts found:
            {impacts_context}
            
            Provide a comprehensive explanation in JSON format:
            {{
                "plain_english": "Simple explanation anyone can understand",
                "legal_definition": "Precise legal definition",
                "real_world_impact": "What this means in practice",
                "alternatives": ["Alternative terms or phrases"],
                "risk_level": "Low/Medium/High",
                "key_points": ["Important things to know"]
            }}
            """
            
            # Call Vertex AI (using your existing Gemini setup as fallback)
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            
            result = json.loads(response.text)
            
            return LegalExplanation(
                term=term,
                plain_english=result.get("plain_english", ""),
                legal_definition=result.get("legal_definition", ""),
                real_world_impact=result.get("real_world_impact", ""),
                alternatives=result.get("alternatives", []),
                risk_level=result.get("risk_level", "Medium"),
                citations=[r["uri"] for r in definition_results + impact_results if r["uri"]]
            )
            
        except Exception as e:
            logger.error(f"Error generating explanation for {term}: {e}")
            return self._fallback_legal_explanation(term)
    
    def _generate_clause_analysis(self, clause_text: str, key_terms: List[str],
                                similar_results: List[Dict], 
                                alternatives_results: List[Dict]) -> ClauseAnalysis:
        """Generate comprehensive clause analysis"""
        try:
            similar_context = "\n".join([
                f"- {result['content']}" for result in similar_results[:3]
            ])
            
            alternatives_context = "\n".join([
                f"- {result['content']}" for result in alternatives_results[:3]
            ])
            
            prompt = f"""
            As a legal expert, analyze this contract clause in detail:
            
            CLAUSE: {clause_text}
            
            KEY TERMS IDENTIFIED: {', '.join(key_terms)}
            
            SIMILAR CASES/PRECEDENTS:
            {similar_context}
            
            ALTERNATIVE LANGUAGE EXAMPLES:
            {alternatives_context}
            
            Provide comprehensive analysis in JSON format:
            {{
                "plain_english_summary": "What this clause means in simple terms",
                "potential_impacts": ["List of potential consequences"],
                "risk_factors": ["Specific risks this clause creates"],
                "alternative_language": ["Better ways to write this clause"],
                "historical_context": "How courts have interpreted similar clauses",
                "negotiation_tips": ["Advice for negotiating this clause"]
            }}
            """
            
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            
            result = json.loads(response.text)
            
            return ClauseAnalysis(
                clause_text=clause_text,
                key_terms=key_terms,
                plain_english_summary=result.get("plain_english_summary", ""),
                potential_impacts=result.get("potential_impacts", []),
                risk_factors=result.get("risk_factors", []),
                alternative_language=result.get("alternative_language", []),
                historical_context=result.get("historical_context", ""),
                negotiation_tips=result.get("negotiation_tips", [])
            )
            
        except Exception as e:
            logger.error(f"Error generating clause analysis: {e}")
            return self._fallback_clause_analysis(clause_text)
    
    def _generate_plain_english_alternatives(self, clause_text: str, 
                                           plain_results: List[Dict]) -> List[str]:
        """Generate plain English alternatives"""
        try:
            context = "\n".join([
                f"- {result['content']}" for result in plain_results[:3]
            ])
            
            prompt = f"""
            Rewrite this legal clause in plain English while maintaining legal accuracy:
            
            ORIGINAL: {clause_text}
            
            PLAIN ENGLISH EXAMPLES:
            {context}
            
            Provide 3 alternative versions in JSON format:
            {{
                "alternatives": [
                    "Version 1: Most simplified",
                    "Version 2: Balanced simplification", 
                    "Version 3: Minimal changes"
                ]
            }}
            """
            
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.4
                )
            )
            
            result = json.loads(response.text)
            return result.get("alternatives", [])
            
        except Exception as e:
            logger.error(f"Error generating alternatives: {e}")
            return self._fallback_alternatives(clause_text)
    
    def _generate_historical_context(self, clause_text: str, 
                                   historical_results: List[Dict]) -> str:
        """Generate historical context summary"""
        try:
            context = "\n".join([
                f"- {result['content']}" for result in historical_results[:3]
            ])
            
            prompt = f"""
            Provide historical context for how courts have interpreted clauses like this:
            
            CLAUSE: {clause_text}
            
            RELEVANT CASES/PRECEDENTS:
            {context}
            
            Summarize the historical interpretation trends and key legal precedents.
            Focus on practical implications for someone reviewing this clause.
            """
            
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.3
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating historical context: {e}")
            return self._fallback_historical_context(clause_text)
    
    def _extract_legal_terms(self, text: str) -> List[str]:
        """Extract legal terms from text using pattern matching"""
        terms = []
        
        for category, patterns in self.legal_terms_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                terms.extend(matches)
        
        # Remove duplicates and return
        return list(set(terms))
    
    # Fallback methods for when GCP services are unavailable - use Gemini AI instead
    def _fallback_legal_explanation(self, term: str) -> LegalExplanation:
        """Fallback explanation using Gemini AI when RAG is unavailable"""
        try:
            # Try to use Gemini API for explanation
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                return self._gemini_explain_term(term)
            else:
                logger.warning("No GEMINI_API_KEY found, using basic fallback")
        except Exception as e:
            logger.error(f"Gemini fallback failed for term '{term}': {e}")
        
        # Basic fallback with built-in legal knowledge
        return self._basic_legal_knowledge(term)
    
    def _fallback_clause_analysis(self, clause_text: str) -> ClauseAnalysis:
        """Fallback analysis when RAG is unavailable"""
        key_terms = self._extract_legal_terms(clause_text)
        
        return ClauseAnalysis(
            clause_text=clause_text,
            key_terms=key_terms,
            plain_english_summary="Detailed analysis requires RAG knowledge base access.",
            potential_impacts=["Impact analysis unavailable without case law database"],
            risk_factors=["Risk assessment requires historical precedent data"],
            alternative_language=["Alternative suggestions require example database"],
            historical_context="Historical context requires case law database access.",
            negotiation_tips=["Negotiation advice requires precedent analysis"]
        )
    
    def _fallback_alternatives(self, clause_text: str) -> List[str]:
        """Fallback alternatives when RAG is unavailable"""
        return [
            "Plain English alternatives require access to contract example database",
            "Please configure Google Cloud RAG services for full functionality"
        ]
    
    def _fallback_historical_context(self, clause_text: str) -> str:
        """Fallback historical context when RAG is unavailable"""
        return "Historical context analysis requires access to case law database. Please configure Google Cloud Discovery Engine for full functionality."
    
    def _gemini_explain_term(self, term: str) -> LegalExplanation:
        """Use Gemini AI to explain legal terms when RAG is unavailable"""
        try:
            from google import genai
            from google.genai import types
            
            api_key = os.environ.get("GEMINI_API_KEY")
            client = genai.Client(api_key=api_key)
            model_name = "gemini-2.5-pro"
            
            system_prompt = """You are an expert legal analyst and contract attorney. 
Your role is to explain legal terms in plain English while providing accurate legal definitions.

CRITICAL REQUIREMENTS:
1. Provide clear, accurate legal definitions
2. Explain real-world implications in plain English
3. Suggest alternative terms when applicable
4. Assess risk levels objectively
5. Use professional, accessible language
6. Focus on contract law context

Always respond with valid JSON in this exact format:
{
    "term": "the term being explained",
    "plain_english": "Clear explanation in everyday language",
    "legal_definition": "Formal legal definition with context",
    "real_world_impact": "What this means in practice for the parties",
    "alternatives": ["alternative term 1", "alternative term 2", "alternative term 3"],
    "risk_level": "Low|Medium|High",
    "citations": ["general legal principle", "common usage"]
}"""
            
            user_prompt = f"""
Please explain the legal term "{term}" in the context of contract law.

Provide:
1. A plain English explanation that anyone can understand
2. The formal legal definition with contract law context  
3. Real-world impact - what this means for the parties involved
4. 2-3 alternative terms or phrases that could be used instead
5. Risk level assessment (Low/Medium/High) for typical contracts
6. General citations or references (no specific case law needed)

Term to explain: "{term}"

Focus on practical implications and make the explanation accessible to non-lawyers while maintaining legal accuracy."""
            
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Content(role="user", parts=[types.Part(text=user_prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.3,
                    max_output_tokens=1000
                ),
            )
            
            if not response.text:
                raise Exception("Empty response from Gemini API")
            
            # Parse the JSON response
            try:
                result = json.loads(response.text)
                
                return LegalExplanation(
                    term=result.get('term', term),
                    plain_english=result.get('plain_english', 'No explanation available'),
                    legal_definition=result.get('legal_definition', 'No definition available'),
                    real_world_impact=result.get('real_world_impact', 'No impact analysis available'),
                    alternatives=result.get('alternatives', []),
                    risk_level=result.get('risk_level', 'Medium'),
                    citations=result.get('citations', ['AI-generated explanation'])
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response for term '{term}': {e}")
                # Return structured response with the raw text
                return LegalExplanation(
                    term=term,
                    plain_english=response.text[:300] + "..." if len(response.text) > 300 else response.text,
                    legal_definition="AI explanation (JSON parsing failed)",
                    real_world_impact="See plain English explanation above",
                    alternatives=[],
                    risk_level="Medium",
                    citations=["AI-generated explanation with parsing error"]
                )
                
        except Exception as e:
            logger.error(f"Gemini API error for term '{term}': {e}")
            raise e  # Re-raise to trigger basic fallback
    
    def _basic_legal_knowledge(self, term: str) -> LegalExplanation:
        """Basic legal knowledge fallback for common terms"""
        term_lower = term.lower().strip()
        
        # Common legal terms with basic explanations
        basic_knowledge = {
            'force majeure': {
                'plain_english': 'Unforeseeable circumstances that prevent a party from fulfilling a contract, like natural disasters or wars.',
                'legal_definition': 'A clause that frees parties from liability when extraordinary circumstances beyond their control prevent them from fulfilling their obligations.',
                'real_world_impact': 'Allows parties to suspend or terminate contracts during major disruptions without penalty.',
                'alternatives': ['Act of God clause', 'Impossibility clause', 'Frustration of purpose'],
                'risk_level': 'Medium'
            },
            'liquidated damages': {
                'plain_english': 'A predetermined amount of money that must be paid if someone breaks the contract.',
                'legal_definition': 'A contractual provision that establishes a specific monetary penalty for breach, agreed upon in advance.',
                'real_world_impact': 'Provides certainty about consequences and avoids lengthy disputes over actual damages.',
                'alternatives': ['Penalty clause', 'Stipulated damages', 'Pre-estimated damages'],
                'risk_level': 'High'
            },
            'indemnification': {
                'plain_english': 'A promise to cover someone else\'s losses and legal costs if they get in trouble because of you.',
                'legal_definition': 'A contractual obligation where one party agrees to compensate another for harm, loss, or damage.',
                'real_world_impact': 'Shifts financial risk and legal responsibility from one party to another.',
                'alternatives': ['Hold harmless clause', 'Liability assumption', 'Defense obligation'],
                'risk_level': 'High'
            },
            'breach': {
                'plain_english': 'Breaking the terms of a contract by not doing what you promised to do.',
                'legal_definition': 'The failure of a party to perform any duty or obligation specified in a contract.',
                'real_world_impact': 'Can lead to lawsuits, financial penalties, and contract termination.',
                'alternatives': ['Default', 'Violation', 'Non-performance'],
                'risk_level': 'High'
            },
            'termination': {
                'plain_english': 'Ending a contract before its natural expiration date.',
                'legal_definition': 'The legal ending of a contract by agreement, breach, or operation of law.',
                'real_world_impact': 'Ends all future obligations but may trigger penalties or require final settlements.',
                'alternatives': ['Cancellation', 'Dissolution', 'Expiration'],
                'risk_level': 'Medium'
            },
            'warranty': {
                'plain_english': 'A promise that certain facts about a product or service are true.',
                'legal_definition': 'A contractual assurance that certain conditions or facts are or will remain true.',
                'real_world_impact': 'Creates liability if the promised conditions turn out to be false.',
                'alternatives': ['Guarantee', 'Representation', 'Assurance'],
                'risk_level': 'Medium'
            },
            'jurisdiction': {
                'plain_english': 'Which court system has the authority to resolve disputes about this contract.',
                'legal_definition': 'The legal authority of a court to hear and decide a case or controversy.',
                'real_world_impact': 'Determines where you must go to court and which laws will apply.',
                'alternatives': ['Venue clause', 'Forum selection', 'Governing law'],
                'risk_level': 'Low'
            },
            'arbitration': {
                'plain_english': 'Resolving disputes through a private judge instead of going to court.',
                'legal_definition': 'A method of dispute resolution where parties agree to submit their case to a neutral arbitrator.',
                'real_world_impact': 'Usually faster and more private than court, but limits appeal options.',
                'alternatives': ['Mediation', 'Alternative dispute resolution', 'Binding arbitration'],
                'risk_level': 'Medium'
            }
        }
        
        if term_lower in basic_knowledge:
            info = basic_knowledge[term_lower]
            return LegalExplanation(
                term=term,
                plain_english=info['plain_english'],
                legal_definition=info['legal_definition'],
                real_world_impact=info['real_world_impact'],
                alternatives=info['alternatives'],
                risk_level=info['risk_level'],
                citations=['Built-in legal knowledge base']
            )
        else:
            # Ultimate fallback for unknown terms
            return LegalExplanation(
                term=term,
                plain_english=f"'{term}' is a legal concept that may have specific implications in contracts. For a detailed explanation, please try again when AI services are available.",
                legal_definition="Detailed legal definition requires AI analysis or legal research.",
                real_world_impact="Impact analysis requires access to legal databases or AI services.",
                alternatives=[],
                risk_level="Medium",
                citations=["Basic fallback - detailed analysis unavailable"]
            )

# Utility function for easy integration
def create_contextual_explainer() -> ContextualExplainer:
    """Factory function to create a contextual explainer instance"""
    return ContextualExplainer()