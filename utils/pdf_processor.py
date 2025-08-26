import fitz  # PyMuPDF
import re
from typing import Dict, List, Any

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
