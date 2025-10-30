import fitz  # PyMuPDF
import re
import os
from typing import Dict, List, Any

# Import OCR processors
try:
    from .Ocr import DocumentOCRProcessor, VisionOCRProcessor, is_supported_file
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: OCR functionality not available. Install Google Cloud libraries for OCR support.")

class PDFProcessor:
    """Handles PDF processing and text extraction"""
    
    def __init__(self):
        self.clause_patterns = [
            r'^\d+\.\s*',  # "1. " or "1."
            r'^[A-Z][A-Z\s]+:?',  # "TERMINATION:" or "TERMINATION"
            r'^\([a-z]\)',  # "(a)"
            r'^\([0-9]+\)',  # "(1)"
            r'^Article\s+\d+',  # "Article 1"
            r'^Section\s+\d+',  # "Section 1"
            r'^\d+\s+[A-Z][A-Za-z\s]+',  # "1 TERMINATION" style headers
        ]
        
        # OCR configuration
        self.ocr_credentials_path = None
        self.ocr_processor_id = None
        self.ocr_api_key = None
        self.ocr_enabled = OCR_AVAILABLE
    
    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process PDF and extract structured data"""
        try:
            doc = fitz.open(file_path)
            
            # Extract text from all pages
            full_text = ""
            page_texts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text("text")
                page_texts.append({
                    'page_number': page_num + 1,
                    'text': page_text
                })
                full_text += page_text + "\n"
            
            # Extract clauses
            clauses = self._extract_clauses(page_texts)
            
            # Calculate statistics
            word_count = len(full_text.split())
            
            document_data = {
                'total_pages': len(doc),
                'word_count': word_count,
                'full_text': full_text,
                'page_texts': page_texts,
                'clauses': clauses
            }
            
            doc.close()
            return document_data
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def _extract_clauses(self, page_texts: List[Dict]) -> List[Dict]:
        """Extract individual clauses from the document"""
        clauses = []
        clause_counter = 1
        
        # Combine all text first, then process
        full_text = ""
        page_map = {}  # Track which text belongs to which page
        
        for page_data in page_texts:
            page_num = page_data['page_number']
            text = page_data['text']
            start_pos = len(full_text)
            full_text += text + "\n\n"
            end_pos = len(full_text)
            page_map[(start_pos, end_pos)] = page_num
        
        # Split by patterns that indicate new clauses/sections
        # Look for numbered sections, headers, etc.
        section_splits = re.split(r'(\n\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][A-Z\s]{3,}:?)\s*[^\n]*\n)', full_text, flags=re.MULTILINE)
        
        current_section = ""
        current_title = ""
        
        for i, section in enumerate(section_splits):
            section = section.strip()
            if not section:
                continue
            
            # Check if this looks like a section header
            is_header = bool(re.match(r'^\s*(?:\d+\.|\d+\s+[A-Z]|[A-Z][A-Z\s]{3,}:?)\s*', section))
            
            if is_header and current_section:
                # Save the previous section if it's substantial
                if len(current_section.split()) >= 20:
                    # Find which page this belongs to
                    page_num = self._find_page_for_text_position(len(full_text) - len(current_section), page_map)
                    
                    clause = {
                        'clause_id': f"clause_{clause_counter}",
                        'title': current_title or self._extract_clause_title(current_section[:100]),
                        'text': current_section.strip(),
                        'page': page_num,
                        'word_count': len(current_section.split())
                    }
                    clauses.append(clause)
                    clause_counter += 1
                
                # Start new section
                current_section = section
                current_title = self._extract_clause_title(section)
            else:
                # Accumulate content
                if current_section:
                    current_section += "\n" + section
                else:
                    current_section = section
                    if not current_title:
                        current_title = self._extract_clause_title(section[:100])
        
        # Don't forget the last section
        if current_section and len(current_section.split()) >= 20:
            page_num = self._find_page_for_text_position(len(full_text) - len(current_section), page_map)
            clause = {
                'clause_id': f"clause_{clause_counter}",
                'title': current_title or self._extract_clause_title(current_section[:100]),
                'text': current_section.strip(),
                'page': page_num,
                'word_count': len(current_section.split())
            }
            clauses.append(clause)
            clause_counter += 1
        
        # Fallback: if we don't have enough clauses, just break the document into chunks
        if len(clauses) < 2:
            print("Fallback: Creating clauses from text chunks")
            clauses = []
            clause_counter = 1
            
            # Simple approach: split by double newlines and take substantial chunks
            all_text = " ".join([page['text'] for page in page_texts])
            chunks = [chunk.strip() for chunk in all_text.split('\n\n') if chunk.strip()]
            
            # Group small chunks together to form meaningful clauses
            current_chunk = ""
            for chunk in chunks:
                if len(current_chunk.split()) < 30:
                    current_chunk += " " + chunk if current_chunk else chunk
                else:
                    # Save current chunk and start new one
                    if len(current_chunk.split()) >= 15:
                        clause = {
                            'clause_id': f"clause_{clause_counter}",
                            'title': self._extract_clause_title(current_chunk[:100]),
                            'text': current_chunk.strip(),
                            'page': 1,  # Default to page 1 for fallback
                            'word_count': len(current_chunk.split())
                        }
                        clauses.append(clause)
                        clause_counter += 1
                    current_chunk = chunk
            
            # Add the last chunk
            if current_chunk and len(current_chunk.split()) >= 15:
                clause = {
                    'clause_id': f"clause_{clause_counter}",
                    'title': self._extract_clause_title(current_chunk[:100]),
                    'text': current_chunk.strip(),
                    'page': 1,
                    'word_count': len(current_chunk.split())
                }
                clauses.append(clause)
        
        print(f"Extracted {len(clauses)} clauses")
        for clause in clauses:
            print(f"- Clause: '{clause['title'][:50]}...' ({clause['word_count']} words)")
        
        return clauses
    
    def _find_page_for_text_position(self, position: int, page_map: dict) -> int:
        """Find which page a text position belongs to"""
        for (start, end), page_num in page_map.items():
            if start <= position < end:
                return page_num
        return 1  # Default to page 1
    
    def _extract_clause_title(self, text: str) -> str:
        """Extract a title from the clause text"""
        lines = text.split('\n')
        first_line = lines[0].strip()
        
        # If first line is short and looks like a title
        if len(first_line.split()) <= 8:
            return first_line
        
        # Try to extract from common patterns
        for pattern in self.clause_patterns:
            match = re.match(pattern, first_line)
            if match:
                # Get text after the pattern
                remainder = first_line[match.end():].strip()
                if remainder:
                    return remainder[:50] + ("..." if len(remainder) > 50 else "")
        
        # Default: use first few words
        words = first_line.split()
        if len(words) > 8:
            return " ".join(words[:8]) + "..."
        return first_line
    
    def configure_ocr(self, credentials_path: str = None, processor_id: str = None, api_key: str = None):
        """Configure OCR settings"""
        self.ocr_credentials_path = credentials_path
        self.ocr_processor_id = processor_id
        self.ocr_api_key = api_key
    
    def process_with_ocr(self, file_path: str, method: str = 'auto', translate: bool = False) -> Dict[str, Any]:
        """Process document using OCR (for scanned PDFs, images, or when regular PDF extraction fails)"""
        
        if not self.ocr_enabled:
            raise Exception("OCR functionality not available. Install Google Cloud libraries.")
        
        if not is_supported_file(file_path):
            raise Exception(f"Unsupported file type for OCR: {file_path}")
        
        # Determine OCR method
        if method == 'auto':
            method = 'documentai' if self.ocr_credentials_path else 'vision'
        
        print(f"Processing with OCR using {method} method...")
        
        try:
            if method == 'documentai':
                return self._process_with_document_ai(file_path, translate)
            elif method == 'vision':
                return self._process_with_vision_api(file_path)
            else:
                raise Exception(f"Unknown OCR method: {method}")
                
        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")
    
    def _process_with_document_ai(self, file_path: str, translate: bool = False) -> Dict[str, Any]:
        """Process document using Google Document AI"""
        
        if not self.ocr_credentials_path:
            raise Exception("Document AI credentials not configured")
        
        # Default processor ID if not set
        processor_id = self.ocr_processor_id or '9e650faad3c59279'
        
        # Initialize Document AI processor
        processor = DocumentOCRProcessor(
            credentials_path=self.ocr_credentials_path,
            processor_id=processor_id,
            location='us'
        )
        
        # Process document
        document = processor.process_document(file_path)
        ocr_result = processor.extract_document_data(document, translate)
        
        # Convert OCR result to our format
        return self._convert_ocr_to_standard_format(ocr_result, 'documentai')
    
    def _process_with_vision_api(self, file_path: str) -> Dict[str, Any]:
        """Process document using Google Vision API"""
        
        if not self.ocr_api_key:
            # Use default API key
            api_key = 'AIzaSyCl7r3oputW_Cu0DMoNz2rxgXZ3QmDvO0E'
        else:
            api_key = self.ocr_api_key
        
        # Initialize Vision API processor
        processor = VisionOCRProcessor(api_key=api_key)
        
        # Process document
        response = processor.process_document_with_vision_api(file_path)
        if not response:
            raise Exception("No response from Vision API")
        
        ocr_result = processor.extract_text_from_vision_response(response)
        if 'error' in ocr_result:
            raise Exception(f"Vision API error: {ocr_result['error']}")
        
        # Convert OCR result to our format
        return self._convert_ocr_to_standard_format(ocr_result, 'vision')
    
    def _convert_ocr_to_standard_format(self, ocr_result: Dict[str, Any], method: str) -> Dict[str, Any]:
        """Convert OCR result to standard document format used by the legal app"""
        
        # Extract text content
        full_text = ocr_result.get('document_text', '')
        
        # Convert pages to our format
        page_texts = []
        pages = ocr_result.get('pages', [])
        
        if not pages and full_text:
            # Fallback: create single page
            page_texts = [{
                'page_number': 1,
                'text': full_text
            }]
        else:
            for i, page in enumerate(pages):
                page_text = ""
                
                # Extract text from paragraphs (Document AI format)
                if 'paragraphs' in page:
                    page_text = "\n".join([p.get('text', '') for p in page['paragraphs']])
                # Extract text from blocks (Vision API format)
                elif 'blocks' in page:
                    page_text = "\n".join([b.get('text', '') for b in page['blocks']])
                
                page_texts.append({
                    'page_number': page.get('page_number', i + 1),
                    'text': page_text or full_text  # Fallback to full text if page text is empty
                })
        
        # Extract clauses using our existing method
        clauses = self._extract_clauses(page_texts)
        
        # Calculate statistics
        word_count = len(full_text.split())
        
        # Create standard document format
        document_data = {
            'total_pages': len(page_texts),
            'word_count': word_count,
            'full_text': full_text,
            'page_texts': page_texts,
            'clauses': clauses,
            'processing_method': f'ocr_{method}',
            'ocr_metadata': {
                'confidence_scores': self._extract_confidence_scores(ocr_result),
                'method': method,
                'tables_detected': len(ocr_result.get('tables', [])),
                'entities_detected': len(ocr_result.get('entities', []))
            }
        }
        
        return document_data
    
    def _extract_confidence_scores(self, ocr_result: Dict[str, Any]) -> List[float]:
        """Extract confidence scores from OCR result"""
        confidence_scores = []
        
        # Extract from pages/paragraphs
        for page in ocr_result.get('pages', []):
            for paragraph in page.get('paragraphs', []):
                if 'confidence' in paragraph:
                    confidence_scores.append(float(paragraph['confidence']))
        
        return confidence_scores
    
    def is_scanned_pdf(self, file_path: str) -> bool:
        """Check if PDF is scanned (has little to no extractable text)"""
        try:
            doc = fitz.open(file_path)
            total_text_length = 0
            total_pages = len(doc)
            
            for page_num in range(min(3, total_pages)):  # Check first 3 pages
                page = doc[page_num]
                page_text = page.get_text("text").strip()
                total_text_length += len(page_text)
            
            doc.close()
            
            # If there's very little text per page, it's likely scanned
            avg_text_per_page = total_text_length / min(3, total_pages)
            return avg_text_per_page < 100  # Less than 100 characters per page suggests scanned
            
        except Exception:
            return False
    
    def smart_process_pdf(self, file_path: str, force_ocr: bool = False) -> Dict[str, Any]:
        """Intelligently process PDF - use OCR if needed, otherwise use regular extraction"""
        
        if force_ocr and self.ocr_enabled:
            print("Force OCR mode enabled")
            return self.process_with_ocr(file_path)
        
        try:
            # Try regular PDF processing first
            document_data = self.process_pdf(file_path)
            
            # Check if we got meaningful text
            if document_data['word_count'] < 50 or len(document_data['clauses']) < 1:
                print("Regular PDF extraction yielded little text, trying OCR...")
                
                if self.ocr_enabled:
                    return self.process_with_ocr(file_path)
                else:
                    print("OCR not available, returning basic extraction")
                    return document_data
            
            print(f"Regular PDF processing successful: {document_data['word_count']} words, {len(document_data['clauses'])} clauses")
            document_data['processing_method'] = 'regular_pdf'
            return document_data
            
        except Exception as e:
            print(f"Regular PDF processing failed: {str(e)}")
            
            if self.ocr_enabled:
                print("Falling back to OCR processing...")
                return self.process_with_ocr(file_path)
            else:
                raise Exception(f"PDF processing failed and OCR not available: {str(e)}")
