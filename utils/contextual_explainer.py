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
    
    # Fallback methods for when GCP services are unavailable
    def _fallback_legal_explanation(self, term: str) -> LegalExplanation:
        """Fallback explanation when RAG is unavailable"""
        return LegalExplanation(
            term=term,
            plain_english=f"The term '{term}' is a legal concept that may have specific implications in contracts.",
            legal_definition="Legal definition not available without RAG knowledge base.",
            real_world_impact="Real-world impact analysis requires access to case law database.",
            alternatives=[],
            risk_level="Medium",
            citations=[]
        )
    
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

# Utility function for easy integration
def create_contextual_explainer() -> ContextualExplainer:
    """Factory function to create a contextual explainer instance"""
    return ContextualExplainer()