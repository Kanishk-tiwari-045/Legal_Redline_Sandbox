import os
import sys
import tempfile
import asyncio
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
from auth import verify_token, get_user_by_username, User
from job_queue import job_queue, Job

security = HTTPBearer()

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
            
            # Analyze risks
            risky_clauses = self.risk_detector.analyze_document(document_data)
            
            job_queue.update_progress(job.job_id, 90)
            
            return {
                'document': document_data,
                'risky_clauses': risky_clauses,
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(file_path)
            except Exception:
                pass

class ClauseService:
    def __init__(self):
        try:
            self.clause_rewriter = ClauseRewriter()
        except Exception:
            self.clause_rewriter = None
        self.diff_generator = DiffGenerator()
        
    async def rewrite_clause_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for clause rewriting"""
        if not self.clause_rewriter:
            raise ValueError("ClauseRewriter not configured (missing GEMINI_API_KEY)")
            
        clause = job.data.get("clause")
        controls = job.data.get("controls", {})
        
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
        return result

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
        html_diff = await loop.run_in_executor(
            None,
            self.diff_generator.generate_html_diff,
            original,
            rewritten
        )
        
        job_queue.update_progress(job.job_id, 90)
        
        return {"html_diff": html_diff}

class PrivacyService:
    def __init__(self):
        try:
            # Only initialize if Google Cloud project ID is available
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
            if project_id:
                self.privacy_processor = PrivacyProcessor(project_id)
            else:
                self.privacy_processor = None
        except Exception:
            self.privacy_processor = None
            
    async def redact_async(self, job: Job) -> Dict[str, Any]:
        """Async wrapper for privacy redaction"""
        if not self.privacy_processor:
            return {"error": "Privacy processor not configured (missing GOOGLE_CLOUD_PROJECT_ID)"}
            
        text_to_redact = job.data.get("text", "")
        
        job_queue.update_progress(job.job_id, 20)
        
        loop = asyncio.get_event_loop()
        redacted_text = await loop.run_in_executor(
            None,
            self.privacy_processor.redact_text,
            text_to_redact
        )
        
        job_queue.update_progress(job.job_id, 90)
        
        return {"redacted_text": redacted_text}

# Service instances
document_service = DocumentService()
clause_service = ClauseService()
chat_service = ChatService()
explainer_service = ExplainerService()
export_service = ExportService()
diff_service = DiffService()
privacy_service = PrivacyService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temp location and return path"""
    suffix = os.path.splitext(upload_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await upload_file.read()
        tmp.write(contents)
        return tmp.name