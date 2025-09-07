#!/usr/bin/env python3
"""
Complete OCR Document Processing Application
Supports both Google Document AI and Google Vision API
All functionality in one file
"""

import os
import json
import argparse
import base64
import requests
from datetime import datetime
from typing import List, Sequence, Dict, Any, Optional

# For Document AI (service account method)
try:
    from google.api_core.client_options import ClientOptions 
    from google.cloud import translate_v2 as translate
    from google.cloud import documentai_v1 as documentai
    from google.oauth2 import service_account
    DOCUMENT_AI_AVAILABLE = True
except ImportError:
    DOCUMENT_AI_AVAILABLE = False
    print("Warning: Google Cloud libraries not installed. Only Vision API will work.")

class DocumentOCRProcessor:
    """Document AI processor using service account authentication"""
    
    def __init__(self, credentials_path: str, processor_id: str, location: str = "us"):
        if not DOCUMENT_AI_AVAILABLE:
            raise ImportError("Google Cloud libraries not installed")
            
        self.credentials_path = credentials_path
        self.processor_id = processor_id
        self.location = location
        self.project_id = self._get_project_id_from_credentials()
        
        # Initialize clients with credentials
        self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
        self.translate_client = translate.Client(credentials=self.credentials)
        
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        self.documentai_client = documentai.DocumentProcessorServiceClient(
            client_options=opts,
            credentials=self.credentials
        )

    def _get_project_id_from_credentials(self) -> str:
        """Extract project ID from credentials file"""
        with open(self.credentials_path, 'r') as f:
            creds = json.load(f)
        return creds.get('project_id', '')

    def translate_text(self, text: str, target_language: str = 'en') -> str:
        """Translate text from Marathi to English"""
        try:
            result = self.translate_client.translate(
                text, 
                target_language=target_language, 
                source_language='mr'
            )
            return result['translatedText']
        except Exception as e:
            print(f"Translation failed: {str(e)}")
            return text

    def process_document(self, file_path: str) -> documentai.Document:
        """Process document (PDF or image) using Document AI"""
        # Determine MIME type based on file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        mime_type = "application/pdf"  # default
        
        if file_extension in ['.jpg', '.jpeg']:
            mime_type = 'image/jpeg'
        elif file_extension == '.png':
            mime_type = 'image/png'
        elif file_extension == '.tiff':
            mime_type = 'image/tiff'
        elif file_extension == '.bmp':
            mime_type = 'image/bmp'
        
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()

            raw_document = documentai.RawDocument(
                content=file_content,
                mime_type=mime_type,
            )

            processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"
            
            request = documentai.ProcessRequest(
                name=processor_name,
                raw_document=raw_document
            )

            result = self.documentai_client.process_document(request=request)
            return result.document

        except Exception as e:
            print(f"Document processing failed: {str(e)}")
            raise

    @staticmethod
    def text_anchor_to_text(text_anchor: documentai.Document.TextAnchor, text: str) -> str:
        """Extract text from text anchor"""
        response = ""
        for segment in text_anchor.text_segments:
            start_index = int(segment.start_index)
            end_index = int(segment.end_index)
            response += text[start_index:end_index]
        return response.strip().replace("\n", " ")

    def get_table_data(self, rows: Sequence[documentai.Document.Page.Table.TableRow], text: str) -> List[List[str]]:
        """Extract table data from document"""
        return [
            [
                self.text_anchor_to_text(cell.layout.text_anchor, text)
                for cell in row.cells
            ]
            for row in rows
        ]

    def extract_document_data(self, document: documentai.Document, translate_content: bool = False) -> Dict[str, Any]:
        """Extract all data from document and return as JSON structure"""
        text = document.text
        result = {
            "document_text": text,
            "pages": [],
            "tables": [],
            "form_fields": [],
            "entities": []
        }
        
        # Extract pages and tables
        for page_num, page in enumerate(document.pages, 1):
            page_data = {
                "page_number": page_num,
                "dimensions": {
                    "width": page.dimension.width,
                    "height": page.dimension.height
                },
                "tables": [],
                "form_fields": [],
                "paragraphs": []
            }
            
            # Extract tables
            for table_num, table in enumerate(page.tables, 1):
                try:
                    headers = self.get_table_data(table.header_rows, text)
                    rows = self.get_table_data(table.body_rows, text)

                    if translate_content:
                        headers = [[self.translate_text(cell) for cell in header_row] for header_row in headers]
                        rows = [[self.translate_text(cell) for cell in row] for row in rows]

                    table_data = {
                        "table_number": table_num,
                        "headers": headers,
                        "rows": rows
                    }
                    
                    page_data["tables"].append(table_data)
                    result["tables"].append({
                        "page_number": page_num,
                        "table_number": table_num,
                        "headers": headers,
                        "rows": rows
                    })
                    
                except Exception as e:
                    print(f"Error processing table {table_num} on page {page_num}: {str(e)}")
                    continue
            
            # Extract paragraphs
            for paragraph in page.paragraphs:
                paragraph_text = self.text_anchor_to_text(paragraph.layout.text_anchor, text)
                if translate_content:
                    paragraph_text = self.translate_text(paragraph_text)
                
                page_data["paragraphs"].append({
                    "text": paragraph_text,
                    "confidence": paragraph.layout.confidence
                })
            
            result["pages"].append(page_data)
            
        # Extract form fields if available
        if hasattr(document, 'entities'):
            for entity in document.entities:
                entity_text = self.text_anchor_to_text(entity.text_anchor, text) if entity.text_anchor else ""
                if translate_content:
                    entity_text = self.translate_text(entity_text)
                
                result["entities"].append({
                    "type": entity.type_,
                    "text": entity_text,
                    "confidence": entity.confidence
                })
        
        # Extract form fields if available (alternative approach)
        if hasattr(document, 'form_fields'):
            for field in document.form_fields:
                field_name = self.text_anchor_to_text(field.field_name.text_anchor, text) if field.field_name.text_anchor else ""
                field_value = self.text_anchor_to_text(field.field_value.text_anchor, text) if field.field_value.text_anchor else ""
                
                if translate_content:
                    field_name = self.translate_text(field_name)
                    field_value = self.translate_text(field_value)
                
                result["form_fields"].append({
                    "field_name": field_name,
                    "field_value": field_value,
                    "confidence": field.field_name.confidence
                })
            
        return result


class VisionOCRProcessor:
    """Vision API processor using API key authentication"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://vision.googleapis.com/v1/images:annotate"
        
    def process_document_with_vision_api(self, file_path: str) -> Dict[str, Any]:
        """Process document using Google Vision API with API key"""
        
        # Read and encode the file
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Encode file content to base64
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        # Prepare the request payload
        payload = {
            "requests": [
                {
                    "image": {
                        "content": encoded_content
                    },
                    "features": [
                        {
                            "type": "DOCUMENT_TEXT_DETECTION",
                            "maxResults": 1
                        },
                        {
                            "type": "TEXT_DETECTION", 
                            "maxResults": 50
                        }
                    ]
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add API key to URL
        url_with_key = f"{self.base_url}?key={self.api_key}"
        
        try:
            print(f"Sending request to Google Vision API...")
            response = requests.post(url_with_key, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                print(f"Error: {response.status_code}")
                print(f"Response: {response.text}")
                return {}
                
        except Exception as e:
            print(f"Request failed: {e}")
            return {}
    
    def extract_text_from_vision_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from Vision API response"""
        
        if 'responses' not in response or not response['responses']:
            return {'error': 'No response data'}
        
        vision_response = response['responses'][0]
        
        result = {
            'document_text': '',
            'text_annotations': [],
            'full_text_annotation': {},
            'confidence_scores': [],
            'pages': []
        }
        
        # Extract full text from document text detection
        if 'fullTextAnnotation' in vision_response:
            full_text = vision_response['fullTextAnnotation']
            result['document_text'] = full_text.get('text', '')
            result['full_text_annotation'] = full_text
            
            # Extract pages and blocks
            pages = full_text.get('pages', [])
            
            for page_num, page in enumerate(pages, 1):
                page_info = {
                    'page_number': page_num,
                    'dimensions': {
                        'width': page.get('width', 0),
                        'height': page.get('height', 0)
                    },
                    'blocks': [],
                    'paragraphs': []
                }
                
                # Extract blocks
                blocks = page.get('blocks', [])
                for block in blocks:
                    block_text = ''
                    paragraphs = block.get('paragraphs', [])
                    
                    for paragraph in paragraphs:
                        paragraph_text = ''
                        words = paragraph.get('words', [])
                        
                        for word in words:
                            symbols = word.get('symbols', [])
                            word_text = ''.join([symbol.get('text', '') for symbol in symbols])
                            paragraph_text += word_text + ' '
                        
                        page_info['paragraphs'].append({
                            'text': paragraph_text.strip(),
                            'confidence': paragraph.get('confidence', 0)
                        })
                        
                        block_text += paragraph_text
                    
                    page_info['blocks'].append({
                        'text': block_text.strip(),
                        'confidence': block.get('confidence', 0)
                    })
                
                result['pages'].append(page_info)
        
        # Extract individual text annotations
        if 'textAnnotations' in vision_response:
            text_annotations = vision_response['textAnnotations']
            result['text_annotations'] = text_annotations
            
            # If no full text, use the first text annotation as main text
            if not result['document_text'] and text_annotations:
                result['document_text'] = text_annotations[0].get('description', '')
        
        return result


# Utility Functions
def ensure_directory_exists(directory_path: str) -> None:
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def save_json(data: dict, file_path: str) -> None:
    """Save data as JSON file"""
    ensure_directory_exists(os.path.dirname(file_path))
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_output_filename(input_filename: str, output_dir: str = 'output', method: str = '') -> str:
    """Generate output filename with timestamp"""
    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    method_suffix = f"_{method}" if method else ""
    output_filename = f"{base_name}{method_suffix}_{timestamp}.json"
    return os.path.join(output_dir, output_filename)

def is_supported_file(file_path: str) -> bool:
    """Check if file is a supported type (PDF or image)"""
    supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    file_extension = os.path.splitext(file_path)[1].lower()
    return file_extension in supported_extensions

def create_test_image(filename: str = "test_document.png") -> None:
    """Create a test image for OCR testing"""
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (800, 600), color='white')
        d = ImageDraw.Draw(img)
        d.text((50, 50), 'This is a test document\nfor OCR processing\nwith Google Document AI\n\nProject: oCR_DOCUMENT_ai\nTest Date: 2025', fill='black')
        img.save(filename)
        print(f"Created test image: {filename}")
    except ImportError:
        print("Pillow not installed. Cannot create test image.")
        print("Install with: pip install Pillow")


def main():
    parser = argparse.ArgumentParser(description='Complete OCR Document Processing Application')
    parser.add_argument('file_path', nargs='?', help='Path to the PDF or image file to process')
    parser.add_argument('--method', choices=['documentai', 'vision'], default='documentai', 
                       help='Processing method: documentai (service account) or vision (API key)')
    parser.add_argument('--credentials', default='service.json', 
                       help='Path to service account JSON file (for documentai method)')
    parser.add_argument('--api-key', default='AIzaSyCl7r3oputW_Cu0DMoNz2rxgXZ3QmDvO0E', 
                       help='Google API key (for vision method)')
    parser.add_argument('--processor-id', default='9e650faad3c59279', 
                       help='Document AI processor ID (for documentai method)')
    parser.add_argument('--location', default='us', help='Google Cloud location')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--translate', action='store_true', help='Translate text to English (documentai only)')
    parser.add_argument('--create-test', action='store_true', help='Create a test image file')
    
    args = parser.parse_args()
    
    # Create test image if requested
    if args.create_test:
        create_test_image()
        return
    
    # Validate file path
    if not args.file_path:
        print("Error: Please provide a file path or use --create-test to create a test image")
        return
        
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        return
    
    if not is_supported_file(args.file_path):
        print(f"Error: Unsupported file type. Please provide a PDF or image file.")
        return
    
    print(f"Processing document: {args.file_path}")
    print(f"Method: {args.method}")
    
    try:
        if args.method == 'documentai':
            # Document AI Method
            if not DOCUMENT_AI_AVAILABLE:
                print("Error: Google Cloud libraries not installed. Use --method vision instead.")
                print("Or install with: pip install google-cloud-documentai google-cloud-translate")
                return
                
            if not os.path.exists(args.credentials):
                print(f"Error: Credentials file not found: {args.credentials}")
                return
            
            # Initialize Document AI processor
            processor = DocumentOCRProcessor(
                credentials_path=args.credentials,
                processor_id=args.processor_id,
                location=args.location
            )
            
            print("Processing with Document AI...")
            document = processor.process_document(args.file_path)
            
            print("Extracting document data...")
            result_data = processor.extract_document_data(document, args.translate)
            
        else:
            # Vision API Method
            processor = VisionOCRProcessor(api_key=args.api_key)
            
            print("Processing with Vision API...")
            response = processor.process_document_with_vision_api(args.file_path)
            
            if not response:
                print("Error: No response from Vision API")
                return
            
            print("Extracting document data...")
            result_data = processor.extract_text_from_vision_response(response)
            
            if 'error' in result_data:
                print(f"Error: {result_data['error']}")
                return
        
        # Save results
        output_path = generate_output_filename(args.file_path, args.output_dir, args.method)
        save_json(result_data, output_path)
        
        print(f"✅ Results saved to: {output_path}")
        print("Document processing completed successfully!")
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"- Method used: {args.method}")
        print(f"- Extracted text length: {len(result_data.get('document_text', ''))}")
        print(f"- Number of pages: {len(result_data.get('pages', []))}")
        if args.method == 'documentai':
            print(f"- Number of tables: {len(result_data.get('tables', []))}")
            print(f"- Number of entities: {len(result_data.get('entities', []))}")
        else:
            print(f"- Number of text annotations: {len(result_data.get('text_annotations', []))}")
        
        # Print first 200 characters of extracted text
        text = result_data.get('document_text', '')
        if text:
            print(f"\n📝 Extracted text (first 200 chars):")
            print(text[:200] + ("..." if len(text) > 200 else ""))
        
    except Exception as e:
        print(f"❌ Error processing document: {str(e)}")
        
        if "billing" in str(e).lower():
            if args.method == 'documentai':
                print("\n💡 Solution: Enable billing for Document AI")
                print("Visit: https://console.developers.google.com/billing/enable?project=oauth-trial-449607")
            else:
                print("\n💡 Solution: Enable Vision API")
                print("Visit: https://console.developers.google.com/apis/api/vision.googleapis.com/overview?project=159280478946")
        
        print(f"\n🔄 Try the alternative method:")
        if args.method == 'documentai':
            print(f"python {__file__} {args.file_path} --method vision")
        else:
            print(f"python {__file__} {args.file_path} --method documentai")


# if __name__ == "__main__":
#     # print("🚀 Complete OCR Document Processing Application")
#     # print("=" * 50)
#     main()
