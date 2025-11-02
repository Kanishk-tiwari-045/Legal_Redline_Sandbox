import os
import sys
import tempfile
import asyncio
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, UploadFile

# Ensure root path is on sys.path so we can import the existing utils package
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.pdf_processor import PDFProcessor
from utils.risk_detector import RiskDetector
from utils.clause_rewriter import ClauseRewriter
from utils.diff_generator import DiffGenerator
from utils.export_manager import ExportManager
from utils.chatbot import Chatbot
from utils.contextual_explainer import ContextualExplainer
try:
    from utils.privacy_processor import PrivacyProcessor
except ImportError:
    PrivacyProcessor = None
from job_queue import job_queue, Job

class DocumentService:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.risk_detector = RiskDetector()
        
    async def process_document_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for document processing"""
        file_path = job.data.get("file_path")
        force_ocr = job.data.get("force_ocr", False)
        
        job_queue.update_progress(job.job_id, 10)
        
        try:
            # Process document
            suffix = os.path.splitext(file_path)[1].lower()
            if suffix == '.pdf':
                document_data = self.pdf_processor.smart_process_pdf(file_path, force_ocr=force_ocr)
            else:
                document_data = self.pdf_processor.process_with_ocr(file_path, method='auto')
            
            job_queue.update_progress(job.job_id, 60)
            
            # Return document data immediately, start risk analysis streaming
            result = {
                'document': document_data,
                'risky_clauses': [],
                'streaming_complete': False
            }
            
            # Start streaming risk analysis in background
            asyncio.create_task(self._stream_risk_analysis(job.job_id, document_data))
            
            job_queue.update_progress(job.job_id, 70)
            
            return result
        finally:
            # Clean up temp file
            try:
                os.unlink(file_path)
            except Exception:
                pass

    async def _stream_risk_analysis(self, job_id: str, document_data: Dict[str, Any]):
        """Stream risk analysis results as each clause is processed"""
        try:
            risky_clauses = []
            total_clauses = len(document_data['clauses'])
            
            for i, clause in enumerate(document_data['clauses']):
                # Analyze this clause
                risk_analysis = self.risk_detector._analyze_clause(clause)
                
                if risk_analysis['score'] >= 1:
                    clause_with_risk = clause.copy()
                    clause_with_risk['risk_analysis'] = risk_analysis
                    risky_clauses.append(clause_with_risk)
                    
                    # Update job with partial results
                    partial_result = {
                        'document': document_data,
                        'risky_clauses': risky_clauses,
                        'streaming_complete': False,
                        'processed_clauses': i + 1,
                        'total_clauses': total_clauses
                    }
                    job_queue.update_job_result(job_id, partial_result)
                
                # Update progress
                progress = 70 + int((i + 1) / total_clauses * 20)  # 70-90%
                job_queue.update_progress(job_id, progress)
            
            # Sort by risk score and finalize
            risky_clauses.sort(key=lambda x: x['risk_analysis']['score'], reverse=True)
            
            final_result = {
                'document': document_data,
                'risky_clauses': risky_clauses,
                'streaming_complete': True,
                'processed_clauses': total_clauses,
                'total_clauses': total_clauses
            }
            
            # Mark job as completed
            job_queue.complete_job(job_id, final_result)
            
        except Exception as e:
            job_queue.fail_job(job_id, str(e))

class ClauseService:
    def __init__(self):
        try:
            self.clause_rewriter = ClauseRewriter()
        except Exception:
            self.clause_rewriter = None
        self.diff_generator = DiffGenerator()
        
    async def rewrite_clause_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for clause rewriting"""
        try:
            if not self.clause_rewriter:
                return {
                    'rewrite': 'Unable to generate rewrite: GEMINI_API_KEY not configured',
                    'rationale': 'The Gemini API key is not set in environment variables. Please configure GEMINI_API_KEY to enable clause rewriting.',
                    'fallback_levels': ['API key configuration required'],
                    'risk_reduction': 'Cannot assess - API not available',
                    'citation': 'Configuration error',
                    'error': True,
                    'error_details': 'GEMINI_API_KEY environment variable missing'
                }
            
            clause = job.data.get("clause")
            controls = job.data.get("controls", {})
            
            if not clause:
                return {
                    'rewrite': 'Unable to generate rewrite: No clause provided',
                    'rationale': 'The clause data is missing or invalid',
                    'fallback_levels': ['Valid clause data required'],
                    'risk_reduction': 'Cannot assess - no clause data',
                    'citation': 'Invalid input',
                    'error': True,
                    'error_details': 'Missing clause data in request'
                }
            
            job_queue.update_progress(job.job_id, 20)
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self.clause_rewriter.suggest_rewrite, 
                clause, 
                controls
            )
            
            job_queue.update_progress(job.job_id, 90)
            
            # Ensure the result has the expected structure
            if isinstance(result, dict) and 'rewrite' in result:
                return result
            else:
                return {
                    'rewrite': 'Unable to generate valid rewrite response',
                    'rationale': 'The AI service returned an unexpected response format',
                    'fallback_levels': ['Please try again with a different clause'],
                    'risk_reduction': 'Cannot assess - invalid response',
                    'citation': 'API response error',
                    'error': True,
                    'error_details': f'Unexpected response format: {str(result)}'
                }
                
        except Exception as e:
            error_str = str(e)
            
            # Handle specific API errors with user-friendly messages
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                return {
                    'rewrite': 'Rate limit exceeded - Please try again in a few minutes',
                    'rationale': 'The AI service is currently experiencing high demand. Please wait a few minutes before trying again.',
                    'fallback_levels': [
                        'Wait 2-3 minutes and retry',
                        'Try during off-peak hours',
                        'Contact support if problem persists'
                    ],
                    'risk_reduction': 'Cannot assess - API rate limited',
                    'citation': f"Original: {job.data.get('clause', {}).get('title', 'Unknown')}",
                    'error': True,
                    'error_type': 'rate_limit',
                    'error_details': 'API rate limit exceeded (429)'
                }
            elif "401" in error_str or "PERMISSION_DENIED" in error_str:
                return {
                    'rewrite': 'API authentication failed - Please check configuration',
                    'rationale': 'The API key may be invalid or expired. Please check the server configuration.',
                    'fallback_levels': [
                        'Verify API key is valid',
                        'Check API key permissions',
                        'Contact administrator'
                    ],
                    'risk_reduction': 'Cannot assess - authentication error',
                    'citation': f"Original: {job.data.get('clause', {}).get('title', 'Unknown')}",
                    'error': True,
                    'error_type': 'auth_error',
                    'error_details': 'API authentication failed'
                }
            else:
                return {
                    'rewrite': f'Service temporarily unavailable: {str(e)[:100]}...',
                    'rationale': 'An unexpected error occurred. This is usually temporary - please try again in a few minutes.',
                    'fallback_levels': [
                        'Try again in 2-3 minutes',
                        'Check internet connection',
                        'Contact support if problem continues'
                    ],
                    'risk_reduction': 'Cannot assess - service error',
                    'citation': f"Original: {job.data.get('clause', {}).get('title', 'Unknown')}",
                    'error': True,
                    'error_type': 'service_error',
                    'error_details': str(e)
                }

class ChatService:
    def __init__(self):
        self.chatbot = Chatbot()
        
    async def chat_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for chat responses"""
        chat_type = job.data.get("type", "general")
        prompt = job.data.get("prompt", "")
        history = job.data.get("history", [])
        document_text = job.data.get("document_text", "")
        
        job_queue.update_progress(job.job_id, 20)
        
        loop = asyncio.get_event_loop()
        
        if chat_type == "document":
            response = await loop.run_in_executor(
                None,
                self.chatbot.get_document_context_response,
                prompt,
                document_text,
                history
            )
        else:
            response = await loop.run_in_executor(
                None,
                self.chatbot.get_general_response,
                prompt,
                history
            )
        
        job_queue.update_progress(job.job_id, 90)
        return {"response": response}

class ExplainerService:
    def __init__(self):
        self.contextual_explainer = ContextualExplainer()
        
    async def explain_term_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for term explanation"""
        term = job.data.get("term", "")
        context = job.data.get("context", "")
        
        job_queue.update_progress(job.job_id, 20)
        
        loop = asyncio.get_event_loop()
        explanation = await loop.run_in_executor(
            None,
            self.contextual_explainer.explain_legal_term,
            term,
            context
        )
        
        job_queue.update_progress(job.job_id, 90)
        
        try:
            result = {
                'plain_english': explanation.plain_english,
                'legal_definition': explanation.legal_definition,
                'real_world_impact': explanation.real_world_impact,
                'risk_level': getattr(explanation, 'risk_level', None),
                'alternatives': getattr(explanation, 'alternatives', [])
            }
        except Exception:
            result = {'error': 'Unable to produce explanation'}
            
        return result
    
    async def analyze_clause_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for clause impact analysis"""
        clause_text = job.data.get("clause_text", "")
        
        job_queue.update_progress(job.job_id, 20)
        
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(
            None,
            self.contextual_explainer.analyze_clause_impact,
            clause_text
        )
        
        job_queue.update_progress(job.job_id, 90)
        
        try:
            result = {
                'plain_english_summary': analysis.plain_english_summary,
                'potential_impacts': analysis.potential_impacts,
                'risk_factors': analysis.risk_factors,
                'negotiation_tips': analysis.negotiation_tips,
                'alternative_language': getattr(analysis, 'alternative_language', []),
                'historical_context': getattr(analysis, 'historical_context', '')
            }
        except Exception:
            result = {'error': 'Unable to analyze clause'}
            
        return result
    
    async def translate_plain_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for plain English translation"""
        legal_text = job.data.get("legal_text", "")
        
        job_queue.update_progress(job.job_id, 20)
        
        loop = asyncio.get_event_loop()
        alternatives = await loop.run_in_executor(
            None,
            self.contextual_explainer.suggest_plain_english_alternatives,
            legal_text
        )
        
        job_queue.update_progress(job.job_id, 90)
        
        return {"alternatives": alternatives}
    
    async def historical_context_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for historical context"""
        clause_text = job.data.get("clause_text", "")
        
        job_queue.update_progress(job.job_id, 20)
        
        loop = asyncio.get_event_loop()
        context = await loop.run_in_executor(
            None,
            self.contextual_explainer.get_historical_context,
            clause_text
        )
        
        job_queue.update_progress(job.job_id, 90)
        
        return {"historical_context": context}

class ExportService:
    def __init__(self):
        self.export_manager = ExportManager()
        self.diff_generator = DiffGenerator()
        
    async def export_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for report export"""
        report_data = job.data.get("report_data", {})
        export_format = job.data.get("format", "html")
        options = job.data.get("options", {})
        
        job_queue.update_progress(job.job_id, 20)
        
        loop = asyncio.get_event_loop()
        
        if export_format == "html":
            result = await loop.run_in_executor(
                None,
                self.export_manager.generate_html_report,
                report_data,
                options
            )
            job_queue.update_progress(job.job_id, 90)
            return {"content": result, "format": "html"}
        else:
            result = await loop.run_in_executor(
                None,
                self.export_manager.generate_pdf_report,
                report_data,
                options
            )
            job_queue.update_progress(job.job_id, 90)
            
            # Save to temp file and return download info
            import base64
            encoded_pdf = base64.b64encode(result).decode('utf-8')
            return {"content": encoded_pdf, "format": "pdf"}

class DiffService:
    def __init__(self):
        self.diff_generator = DiffGenerator()
        
    async def generate_diff_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for diff generation"""
        original = job.data.get("original", "")
        rewritten = job.data.get("rewritten", "")
        
        job_queue.update_progress(job.job_id, 20)
        
        loop = asyncio.get_event_loop()
        structured_diff = await loop.run_in_executor(
            None,
            self.diff_generator.generate_structured_diff,
            original,
            rewritten
        )
        
        job_queue.update_progress(job.job_id, 90)
        
        return structured_diff

class PrivacyService:
    def __init__(self):
        try:
            # Only initialize if Google Cloud project ID is available
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
            dp_sigma = float(os.getenv('DP_SIGMA', '0.2'))
            if project_id:
                self.privacy_processor = PrivacyProcessor(project_id, dp_sigma)
            else:
                self.privacy_processor = None
        except Exception:
            self.privacy_processor = None
            
    async def redact_async(self, job: Job, info_types: list = None, redaction_level: str = "high"):
        """Asynchronous AES + Gaussian DP privacy redaction"""
        if not self.privacy_processor:
            return {"error": "Privacy processor not configured (missing GOOGLE_CLOUD_PROJECT_ID)"}

        text_to_process = job.data.get("text", "")
        job_queue.update_progress(job.job_id, 10)

        loop = asyncio.get_event_loop()

        # Run secure AES + DP redaction asynchronously
        encrypted_result = await loop.run_in_executor(
            None,
            self.privacy_processor.process_text_securely,
            text_to_process
        )

        job_queue.update_progress(job.job_id, 70)

        # Decrypt to get final redacted version for output
        redacted_text = await loop.run_in_executor(
            None,
            self.privacy_processor.decrypt_and_show,
            encrypted_result
        )

        job_queue.update_progress(job.job_id, 95)

        return {"redacted_text": redacted_text}

# Service instances
document_service = DocumentService()
clause_service = ClauseService()
chat_service = ChatService()
explainer_service = ExplainerService()
export_service = ExportService()
diff_service = DiffService()
privacy_service = PrivacyService()

async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temp location and return path"""
    suffix = os.path.splitext(upload_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await upload_file.read()
        tmp.write(contents)
        return tmp.name