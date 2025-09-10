import streamlit as st
import json
import base64
import tempfile
import os
from io import BytesIO
from utils.pdf_processor import PDFProcessor
from utils.risk_detector import RiskDetector
from utils.clause_rewriter import ClauseRewriter
from utils.diff_generator import DiffGenerator
from utils.export_manager import ExportManager
from utils.chatbot import Chatbot
from utils.privacy_processor import PrivacyProcessor

# Page configuration
st.set_page_config(
    page_title="Legal Redline Sandbox - Debug",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Debug function to show session state
def debug_session_state():
    """Display session state for debugging"""
    if st.checkbox("🐛 Debug Mode - Show Session State"):
        st.write("**Current Session State:**")
        for key, value in st.session_state.items():
            if key == 'processed_document' and value:
                st.write(f"- {key}: Document with {len(value.get('clauses', []))} clauses")
            elif key == 'risky_clauses' and value:
                st.write(f"- {key}: {len(value)} risky clauses")
            elif isinstance(value, (str, int, float, bool)) or value is None:
                st.write(f"- {key}: {value}")
            else:
                st.write(f"- {key}: {type(value)} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")

# Initialize session state with all necessary variables
def init_session_state():
    """Initialize all session state variables with debugging"""
    print("🔧 Initializing session state...")
    
    # Core document data
    if 'processed_document' not in st.session_state:
        st.session_state.processed_document = None
        print("✅ Initialized processed_document")
    if 'risky_clauses' not in st.session_state:
        st.session_state.risky_clauses = []
        print("✅ Initialized risky_clauses")
    if 'selected_clause' not in st.session_state:
        st.session_state.selected_clause = None
    if 'rewrite_history' not in st.session_state:
        st.session_state.rewrite_history = {}
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'doc_chat_history' not in st.session_state:
        st.session_state.doc_chat_history = []
    if 'redacted_text' not in st.session_state:
        st.session_state.redacted_text = None
    
    # Store OCR configuration in session state
    if 'ocr_method' not in st.session_state:
        st.session_state.ocr_method = "Auto (Smart Detection)"
    if 'force_ocr' not in st.session_state:
        st.session_state.force_ocr = False
    if 'ocr_credentials_path' not in st.session_state:
        st.session_state.ocr_credentials_path = None
    if 'ocr_processor_id' not in st.session_state:
        st.session_state.ocr_processor_id = None
    if 'ocr_api_key' not in st.session_state:
        st.session_state.ocr_api_key = None
    
    # Document processing state
    if 'document_processed' not in st.session_state:
        st.session_state.document_processed = False
    if 'processing_method_used' not in st.session_state:
        st.session_state.processing_method_used = None
    if 'document_filename' not in st.session_state:
        st.session_state.document_filename = None
        
    # Add a session initialization flag
    if 'session_initialized' not in st.session_state:
        st.session_state.session_initialized = True
        print("✅ Session state fully initialized")

@st.cache_resource
def get_processors():
    """Initialize processors once and cache them"""
    try:
        print("🔧 Initializing processors...")
        pdf_processor = PDFProcessor()
        risk_detector = RiskDetector()
        clause_rewriter = ClauseRewriter()
        diff_generator = DiffGenerator()
        export_manager = ExportManager()
        chatbot = Chatbot()
        print("✅ All processors initialized successfully")
        return pdf_processor, risk_detector, clause_rewriter, diff_generator, export_manager, chatbot
    except Exception as e:
        print(f"❌ Error initializing processors: {str(e)}")
        st.error(f"Error initializing processors: {str(e)}")
        st.info("Some features may not work. Please check your environment variables.")
        return None, None, None, None, None, None

def main():
    # Initialize session state first
    init_session_state()
    
    # Get processors
    processors = get_processors()
    if processors[0] is None:  # Error in initialization
        st.error("Failed to initialize processors. Please check your configuration.")
        return
        
    pdf_processor, risk_detector, clause_rewriter, diff_generator, export_manager, chatbot = processors
    
    # Header
    st.title("⚖️ Legal Redline Sandbox - Debug Mode")
    st.markdown("### AI-Powered Contract Analysis and Clause Rewriting Tool")
    
    # Debug section
    debug_session_state()
    
    # Legal disclaimer
    st.error("⚠️ **IMPORTANT DISCLAIM" + "ER**: This tool is for informational purposes only and does not constitute legal advice. Always consult with a qualified attorney for legal matters.")

    # Privacy and Security Note
    st.success("🔒 **Privacy & Security:** Your documents are processed securely and are not stored on our servers. All processing is done in memory and is deleted after you close the session.")
    st.markdown("---")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page:",
            ["📄 Document Upload", "🔒 Privacy & Security", "🔍 Risk Analysis", "✏️ Redline Sandbox", "📊 Export Report", "💬 Chatbot"],
            key="main_navigation"
        )
        
        # OCR Status section
        st.markdown("---")
        st.subheader("🔧 Current Settings")
        
        # Show current OCR configuration
        st.write(f"**OCR Method:** {st.session_state.ocr_method}")
        if st.session_state.force_ocr:
            st.write("**Force OCR:** ✅ Enabled")
        else:
            st.write("**Force OCR:** ❌ Disabled")
            
        # Show credentials status
        if st.session_state.ocr_credentials_path:
            st.write("**Credentials:** ✅ Configured")
        elif st.session_state.ocr_api_key:
            st.write("**API Key:** ✅ Configured")
        else:
            st.write("**Credentials:** ❌ Not Set")
            
        # Document status
        if st.session_state.processed_document:
            st.write("**Document:** ✅ Processed")
            st.write(f"**Clauses:** {len(st.session_state.processed_document.get('clauses', []))}")
            st.write(f"**Risky Clauses:** {len(st.session_state.risky_clauses)}")
        else:
            st.write("**Document:** ❌ None")
            
        # Reset button
        st.markdown("---")
        if st.button("🔄 Reset All", help="Clear all data and settings"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Page routing
    if page == "📄 Document Upload":
        show_upload_page(pdf_processor, risk_detector)
    elif page == "🔍 Risk Analysis":
        show_risk_analysis_page()
    elif page == "✏️ Redline Sandbox":
        show_redline_sandbox_page(clause_rewriter, diff_generator)
    elif page == "📊 Export Report":
        show_export_page(export_manager)
    elif page == "🔒 Privacy & Security":
        show_privacy_page()
    elif page == "💬 Chatbot":
        show_chatbot_page(chatbot)

def show_upload_page(pdf_processor, risk_detector):
    st.header("📄 Document Upload & Processing")
    
    # Debug info
    st.info(f"🔍 Current document state: {st.session_state.processed_document is not None}")
    
    # OCR Configuration section
    with st.expander("⚙️ OCR Configuration (Advanced)", expanded=False):
        st.markdown("Configure OCR settings for scanned documents or images:")
        
        col1, col2 = st.columns(2)
        with col1:
            # Use session state directly in the selectbox
            try:
                current_index = ["Auto (Smart Detection)", "Document AI", "Vision API", "Disabled"].index(st.session_state.ocr_method)
            except ValueError:
                current_index = 0
                st.session_state.ocr_method = "Auto (Smart Detection)"
                
            ocr_method = st.selectbox(
                "OCR Method:", 
                ["Auto (Smart Detection)", "Document AI", "Vision API", "Disabled"],
                index=current_index,
                help="Choose OCR processing method",
                key="ocr_method_select"
            )
            # Update session state immediately
            st.session_state.ocr_method = ocr_method
            
        with col2:
            force_ocr = st.checkbox(
                "Force OCR", 
                value=st.session_state.force_ocr,
                help="Force OCR even for regular PDFs",
                key="force_ocr_checkbox"
            )
            # Update session state immediately
            st.session_state.force_ocr = force_ocr
        
        # OCR credentials configuration
        if st.session_state.ocr_method in ["Auto (Smart Detection)", "Document AI"]:
            credentials_file = st.file_uploader(
                "Document AI Service Account JSON (Optional):",
                type=['json'],
                help="Upload your Google Cloud service account credentials for Document AI",
                key="credentials_uploader"
            )
            
            processor_id = st.text_input(
                "Processor ID (Optional):",
                value=st.session_state.ocr_processor_id or "",
                placeholder="e.g., 9e650faad3c59279",
                help="Your Document AI processor ID",
                key="processor_id_input"
            )
            # Update session state immediately
            st.session_state.ocr_processor_id = processor_id if processor_id else None
        
        if st.session_state.ocr_method in ["Auto (Smart Detection)", "Vision API"]:
            api_key = st.text_input(
                "Vision API Key (Optional):",
                type="password",
                value=st.session_state.ocr_api_key or "",
                placeholder="Your Google Cloud API key",
                help="API key for Google Vision API",
                key="api_key_input"
            )
            # Update session state immediately
            st.session_state.ocr_api_key = api_key if api_key else None
    
    uploaded_file = st.file_uploader(
        "Upload your contract (PDF, images, or scanned documents)",
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
        help="Upload a document for analysis",
        key="main_file_uploader"
    )
    
    if uploaded_file is not None:
        st.info(f"📁 Processing file: {uploaded_file.name}")
        
        with st.spinner("Processing document..."):
            try:
                # Store filename for reference
                st.session_state.document_filename = uploaded_file.name
                
                # Determine file extension and save temporarily
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                print(f"📁 Processing file: {uploaded_file.name} ({file_extension})")
                print(f"🔧 OCR Method: {st.session_state.ocr_method}")
                
                # Configure OCR settings if provided
                ocr_configured = False
                if 'credentials_file' in locals() and credentials_file is not None:
                    # Save credentials temporarily
                    credentials_content = credentials_file.read().decode('utf-8')
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as cred_file:
                        cred_file.write(credentials_content)
                        credentials_path = cred_file.name
                    
                    # Store in session state for future use
                    st.session_state.ocr_credentials_path = credentials_path
                    
                    pdf_processor.configure_ocr(
                        credentials_path=credentials_path,
                        processor_id=st.session_state.ocr_processor_id,
                        api_key=st.session_state.ocr_api_key
                    )
                    ocr_configured = True
                    print("✅ OCR configured with credentials file")
                elif st.session_state.ocr_api_key:
                    pdf_processor.configure_ocr(api_key=st.session_state.ocr_api_key)
                    ocr_configured = True
                    print("✅ OCR configured with API key")
                elif st.session_state.ocr_credentials_path and os.path.exists(st.session_state.ocr_credentials_path):
                    # Use previously uploaded credentials from session state
                    pdf_processor.configure_ocr(
                        credentials_path=st.session_state.ocr_credentials_path,
                        processor_id=st.session_state.ocr_processor_id,
                        api_key=st.session_state.ocr_api_key
                    )
                    ocr_configured = True
                    print("✅ OCR configured with cached credentials")
                
                # Process the document based on settings
                processing_method = "regular"  # Default
                document_data = None
                
                if st.session_state.ocr_method == "Disabled":
                    # Only use regular PDF processing
                    if file_extension == '.pdf':
                        document_data = pdf_processor.process_pdf(tmp_file_path)
                        processing_method = "regular_pdf"
                        print("📄 Processed with regular PDF extraction")
                    else:
                        st.error("❌ OCR is disabled but you uploaded an image file. Please enable OCR or upload a PDF.")
                        return
                        
                elif st.session_state.ocr_method == "Auto (Smart Detection)":
                    # Use smart processing - OCR if needed
                    if file_extension == '.pdf':
                        document_data = pdf_processor.smart_process_pdf(tmp_file_path, force_ocr=st.session_state.force_ocr)
                        processing_method = document_data.get('processing_method', 'smart')
                        print(f"🧠 Smart processing result: {processing_method}")
                    else:
                        # Image file - must use OCR
                        document_data = pdf_processor.process_with_ocr(tmp_file_path, method='auto')
                        processing_method = document_data.get('processing_method', 'ocr_auto')
                        print("🖼️ Image processed with auto OCR")
                        
                elif st.session_state.ocr_method == "Document AI":
                    # Force Document AI OCR
                    document_data = pdf_processor.process_with_ocr(tmp_file_path, method='documentai')
                    processing_method = "ocr_documentai"
                    print("🤖 Processed with Document AI")
                    
                elif st.session_state.ocr_method == "Vision API":
                    # Force Vision API OCR
                    document_data = pdf_processor.process_with_ocr(tmp_file_path, method='vision')
                    processing_method = "ocr_vision"
                    print("👁️ Processed with Vision API")
                
                # Clean up temporary files
                os.unlink(tmp_file_path)
                if ocr_configured and 'credentials_path' in locals():
                    try:
                        os.unlink(credentials_path)
                    except:
                        pass
                
                # Validate document data
                if not document_data or 'clauses' not in document_data:
                    st.error("❌ Failed to extract document data properly")
                    return
                
                # Store in session state with explicit validation
                st.session_state.processed_document = document_data
                st.session_state.document_processed = True
                st.session_state.processing_method_used = processing_method
                
                print(f"✅ Document stored in session state with {len(document_data.get('clauses', []))} clauses")
                
                # Display summary
                st.success("✅ Document processed successfully!")
                
                # Show processing method info
                processing_info = f"📊 **Processing Method:** {processing_method.replace('_', ' ').title()}"
                if 'ocr_metadata' in document_data:
                    ocr_meta = document_data['ocr_metadata']
                    if ocr_meta.get('confidence_scores'):
                        avg_confidence = sum(ocr_meta['confidence_scores']) / len(ocr_meta['confidence_scores'])
                        processing_info += f" | **OCR Confidence:** {avg_confidence:.1%}"
                    if ocr_meta.get('tables_detected', 0) > 0:
                        processing_info += f" | **Tables Detected:** {ocr_meta['tables_detected']}"
                
                st.info(processing_info)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Pages", document_data.get('total_pages', 0))
                with col2:
                    st.metric("Total Clauses", len(document_data.get('clauses', [])))
                with col3:
                    st.metric("Word Count", document_data.get('word_count', 0))
                with col4:
                    method_emoji = {
                        'regular_pdf': '📄',
                        'ocr_documentai': '🤖',
                        'ocr_vision': '👁️',
                        'smart': '🧠'
                    }
                    st.metric(
                        "Method", 
                        f"{method_emoji.get(processing_method, '📊')} {processing_method.replace('_', ' ').title()}"
                    )
                
                # Show preview of clauses
                st.subheader("Document Preview")
                clauses = document_data.get('clauses', [])
                for i, clause in enumerate(clauses[:3]):  # Show first 3 clauses
                    with st.expander(f"Clause {i+1}: {clause.get('title', 'Untitled')}"):
                        st.write(f"**Page:** {clause.get('page', 'Unknown')}")
                        text = clause.get('text', '')
                        preview_text = text[:200] + "..." if len(text) > 200 else text
                        st.write(f"**Text:** {preview_text}")
                
                # Automatically run risk analysis
                with st.spinner("Analyzing risks..."):
                    try:
                        risky_clauses = risk_detector.analyze_document(document_data)
                        st.session_state.risky_clauses = risky_clauses
                        print(f"✅ Risk analysis completed: {len(risky_clauses)} risky clauses found")
                        
                        st.info(f"🎯 Found {len(risky_clauses)} potentially risky clauses. Navigate to Risk Analysis to review them.")
                    except Exception as risk_error:
                        st.warning(f"⚠️ Risk analysis failed: {str(risk_error)}")
                        st.session_state.risky_clauses = []
                        print(f"⚠️ Risk analysis error: {str(risk_error)}")
                
            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
                print(f"❌ Processing error: {str(e)}")
    else:
        st.info("👆 Please upload a PDF contract to begin analysis")
        
        # Show current document status
        if st.session_state.processed_document:
            st.success(f"📋 Previously processed document is still available: {st.session_state.document_filename or 'Unknown'}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 View Current Document"):
                    st.json(st.session_state.processed_document, expanded=False)
            with col2:
                if st.button("🗑️ Clear Current Document"):
                    st.session_state.processed_document = None
                    st.session_state.risky_clauses = []
                    st.session_state.document_processed = False
                    st.session_state.document_filename = None
                    st.rerun()

def show_risk_analysis_page():
    st.header("🔍 Risk Analysis")
    
    # Debug current state
    st.info(f"🔍 Document state: {st.session_state.processed_document is not None}")
    st.info(f"🔍 Risky clauses: {len(st.session_state.risky_clauses)}")
    
    if st.session_state.processed_document is None:
        st.warning("⚠️ Please upload a document first in the Document Upload page.")
        return
    
    if not st.session_state.risky_clauses:
        st.info("No risky clauses detected in the document.")
        return
    
    # Risk overview
    st.subheader("Risk Overview")
    
    # Calculate risk distribution
    risk_counts = {}
    total_score = 0
    for clause in st.session_state.risky_clauses:
        if 'risk_analysis' in clause:
            for tag in clause['risk_analysis'].get('tags', []):
                risk_counts[tag] = risk_counts.get(tag, 0) + 1
            total_score += clause['risk_analysis'].get('score', 0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("High-Risk Clauses", len(st.session_state.risky_clauses))
    with col2:
        st.metric("Total Risk Score", total_score)
    with col3:
        avg_score = total_score / len(st.session_state.risky_clauses) if st.session_state.risky_clauses else 0
        st.metric("Average Risk Score", f"{avg_score:.1f}")
    
    # Risk breakdown
    risk_labels = {
        'auto_renew': 'Auto-Renewal',
        'unilateral_change': 'Unilateral Changes',
        'short_notice': 'Short Notice Period',
        'high_penalty': 'High Penalties',
        'exclusive_jurisdiction': 'Exclusive Jurisdiction',
        'liability_limitation': 'Liability Limitations',
        'broad_termination': 'Broad Termination Rights'
    }
    
    if risk_counts:
        st.subheader("Risk Categories")
        
        for tag, count in risk_counts.items():
            label = risk_labels.get(tag, tag.replace('_', ' ').title())
            st.write(f"• **{label}**: {count} clause(s)")
    
    # Detailed clause list
    st.subheader("Risky Clauses Details")
    
    for i, clause in enumerate(st.session_state.risky_clauses):
        risk_analysis = clause.get('risk_analysis', {})
        risk_score = risk_analysis.get('score', 0)
        risk_color = "🔴" if risk_score >= 4 else "🟡" if risk_score >= 2 else "🟢"
        
        with st.expander(f"{risk_color} {clause.get('title', 'Untitled')} (Risk Score: {risk_score})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Original Text:**")
                st.write(clause.get('text', 'No text available'))
                st.write(f"**Page:** {clause.get('page', 'Unknown')}")
            
            with col2:
                st.write("**Risk Factors:**")
                for tag in risk_analysis.get('tags', []):
                    label = risk_labels.get(tag, tag.replace('_', ' ').title())
                    st.write(f"• {label}")
                
                st.write("**Rationale:**")
                st.write(risk_analysis.get('rationale', 'No rationale provided'))
                
                if st.button(f"Edit in Sandbox", key=f"edit_{i}"):
                    st.session_state.selected_clause = clause

def show_redline_sandbox_page(clause_rewriter, diff_generator):
    st.header("✏️ Redline Sandbox")
    
    # Debug current state
    st.info(f"🔍 Document state: {st.session_state.processed_document is not None}")
    st.info(f"🔍 Risky clauses: {len(st.session_state.risky_clauses)}")
    
    if st.session_state.processed_document is None:
        st.warning("⚠️ Please upload a document first in the Document Upload page.")
        return
    
    if not st.session_state.risky_clauses:
        st.info("No risky clauses detected. Please run risk analysis first.")
        return
    
    # Clause selection
    st.subheader("Select Clause to Edit")
    
    clause_options = [
        f"{i+1}. {clause.get('title', 'Untitled')} (Risk: {clause.get('risk_analysis', {}).get('score', 0)})"
        for i, clause in enumerate(st.session_state.risky_clauses)
    ]
    
    selected_idx = st.selectbox(
        "Choose a clause to rewrite:",
        range(len(clause_options)),
        format_func=lambda x: clause_options[x],
        index=0 if st.session_state.selected_clause is None else next(
            (i for i, c in enumerate(st.session_state.risky_clauses) 
             if c.get('clause_id') == st.session_state.selected_clause.get('clause_id')), 0
        )
    )
    
    current_clause = st.session_state.risky_clauses[selected_idx]
    st.session_state.selected_clause = current_clause
    
    # Main editing interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Original Clause")
        st.info(f"**Page:** {current_clause.get('page', 'Unknown')}")
        st.text_area(
            "Original Text:",
            current_clause.get('text', ''),
            height=300,
            disabled=True,
            key="original_text"
        )
        
        # Risk information
        risk_analysis = current_clause.get('risk_analysis', {})
        st.subheader("⚠️ Risk Analysis")
        st.write(f"**Risk Score:** {risk_analysis.get('score', 0)}")
        st.write("**Risk Factors:**")
        for tag in risk_analysis.get('tags', []):
            st.write(f"• {tag.replace('_', ' ').title()}")
    
    with col2:
        st.subheader("✏️ AI-Generated Rewrite")
        
        # What-if controls
        st.subheader("🎛️ What-If Controls")
        
        col2a, col2b = st.columns(2)
        with col2a:
            notice_days = st.slider("Notice Period (days)", 0, 90, 30, key="notice_days")
        with col2b:
            late_fee_percent = st.slider("Late Fee (%)", 0.0, 25.0, 5.0, step=0.5, key="late_fee")
        
        col2c, col2d = st.columns(2)
        with col2c:
            jurisdiction_neutral = st.checkbox("Jurisdiction Neutral", value=True, key="jurisdiction")
        with col2d:
            favor_customer = st.checkbox("Favor Customer", value=True, key="customer_favor")
        
        # Generate rewrite button
        if st.button("🤖 Generate Rewrite", type="primary"):
            with st.spinner("Generating AI rewrite..."):
                try:
                    controls = {
                        'notice_days': notice_days,
                        'late_fee_percent': late_fee_percent,
                        'jurisdiction_neutral': jurisdiction_neutral,
                        'favor_customer': favor_customer
                    }
                    
                    rewrite_result = clause_rewriter.suggest_rewrite(current_clause, controls)
                    
                    # Store in history
                    clause_id = current_clause.get('clause_id', f"clause_{selected_idx}")
                    if clause_id not in st.session_state.rewrite_history:
                        st.session_state.rewrite_history[clause_id] = []
                    st.session_state.rewrite_history[clause_id].append({
                        'controls': controls,
                        'result': rewrite_result
                    })
                    
                    st.success("✅ Rewrite generated successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating rewrite: {str(e)}")
        
        # Display latest rewrite if available
        clause_id = current_clause.get('clause_id', f"clause_{selected_idx}")
        if clause_id in st.session_state.rewrite_history and st.session_state.rewrite_history[clause_id]:
            latest_rewrite = st.session_state.rewrite_history[clause_id][-1]['result']
            
            st.text_area(
                "Rewritten Text:",
                latest_rewrite.get('rewrite', ''),
                height=200,
                key="rewritten_text"
            )
            
            # Show rationale
            with st.expander("📝 Rationale & Explanation"):
                st.write(latest_rewrite.get('rationale', ''))
                
                if 'fallback_levels' in latest_rewrite:
                    st.write("**Alternative Approaches:**")
                    for i, fallback in enumerate(latest_rewrite['fallback_levels']):
                        st.write(f"{i+1}. {fallback}")
            
            # Show diff
            st.subheader("📊 Side-by-Side Comparison")
            try:
                diff_html = diff_generator.generate_html_diff(
                    current_clause.get('text', ''), 
                    latest_rewrite.get('rewrite', '')
                )
                st.html(diff_html)
            except Exception as e:
                st.error(f"❌ Error generating diff: {str(e)}")

def show_export_page(export_manager):
    st.header("📊 Export Report")
    
    # Debug current state
    st.info(f"🔍 Document state: {st.session_state.processed_document is not None}")
    st.info(f"🔍 Rewrite history: {len(st.session_state.rewrite_history)} clauses")
    
    if st.session_state.processed_document is None:
        st.warning("⚠️ Please upload a document first.")
        return
    
    if not st.session_state.rewrite_history:
        st.info("💡 No rewrites generated yet. Use the Redline Sandbox to create rewrites first.")
        return
    
    st.subheader("Report Summary")
    
    # Summary statistics
    total_rewrites = sum(len(rewrites) for rewrites in st.session_state.rewrite_history.values())
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Clauses Analyzed", len(st.session_state.risky_clauses))
    with col2:
        st.metric("Clauses Rewritten", len(st.session_state.rewrite_history))
    with col3:
        st.metric("Total Rewrites Generated", total_rewrites)
    
    # Export options
    st.subheader("Export Options")
    
    export_format = st.selectbox("Select Export Format:", ["HTML Report", "PDF Report"])
    include_original = st.checkbox("Include Original Clauses", value=True)
    include_rationale = st.checkbox("Include AI Rationale", value=True)
    include_diff = st.checkbox("Include Side-by-Side Comparison", value=True)
    
    if st.button("📥 Generate Export", type="primary"):
        with st.spinner("Generating export..."):
            try:
                export_options = {
                    'format': export_format.lower().split()[0],  # 'html' or 'pdf'
                    'include_original': include_original,
                    'include_rationale': include_rationale,
                    'include_diff': include_diff
                }
                
                report_data = {
                    'document': st.session_state.processed_document,
                    'risky_clauses': st.session_state.risky_clauses,
                    'rewrite_history': st.session_state.rewrite_history
                }
                
                if export_options['format'] == 'html':
                    report_content = export_manager.generate_html_report(report_data, export_options)
                    
                    # Display preview
                    st.subheader("📋 Report Preview")
                    st.html(report_content)
                    
                    # Download button
                    st.download_button(
                        label="💾 Download HTML Report",
                        data=report_content,
                        file_name="legal_redline_report.html",
                        mime="text/html"
                    )
                    
                else:  # PDF format
                    pdf_content = export_manager.generate_pdf_report(report_data, export_options)
                    
                    st.download_button(
                        label="💾 Download PDF Report",
                        data=pdf_content,
                        file_name="legal_redline_report.pdf",
                        mime="application/pdf"
                    )
                
                st.success("✅ Report generated successfully!")
                
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
    
    # Show preview of rewrites
    if st.session_state.rewrite_history:
        st.subheader("📝 Current Rewrites")
        
        for clause_id, rewrites in st.session_state.rewrite_history.items():
            # Find the clause
            clause = next((c for c in st.session_state.risky_clauses if c.get('clause_id') == clause_id), None)
            if clause:
                latest_rewrite = rewrites[-1]['result']
                
                with st.expander(f"✏️ {clause.get('title', 'Untitled')} ({len(rewrites)} version(s))"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Original:**")
                        text = clause.get('text', '')
                        preview_text = text[:200] + "..." if len(text) > 200 else text
                        st.write(preview_text)
                    
                    with col2:
                        st.write("**Latest Rewrite:**")
                        rewrite_text = latest_rewrite.get('rewrite', '')
                        preview_rewrite = rewrite_text[:200] + "..." if len(rewrite_text) > 200 else rewrite_text
                        st.write(preview_rewrite)

def show_chatbot_page(chatbot):
    st.header("💬 Chatbot")

    tab1, tab2 = st.tabs(["🤖 General Assistant", "📄 Document-specific Q&A"])

    with tab1:
        st.subheader("General Legal Assistant")
        
        # Chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # User input
        with st.form(key='general_chat_form', clear_on_submit=True):
            user_input = st.text_input("Ask a general legal question:", key="general_chat_input")
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # Get bot response
            with st.spinner("Thinking..."):
                try:
                    bot_response = chatbot.get_general_response(user_input, st.session_state.chat_history)
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
                except Exception as e:
                    st.error(f"❌ Error getting response: {str(e)}")
                    st.session_state.chat_history.append({"role": "assistant", "content": "Sorry, I encountered an error. Please try again."})
            
            st.rerun()

    with tab2:
        st.subheader("Document-Specific Q&A")
        
        if st.session_state.processed_document is None:
            st.warning("⚠️ Please upload a document first in the Document Upload page.")
            return

        # Chat history
        for msg in st.session_state.doc_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # User input
        with st.form(key='doc_chat_form', clear_on_submit=True):
            doc_user_input = st.text_input("Ask a question about the uploaded document:", key="doc_chat_input")
            doc_submit_button = st.form_submit_button(label='Send')

        if doc_submit_button and doc_user_input:
            # Add user message to history
            st.session_state.doc_chat_history.append({"role": "user", "content": doc_user_input})
            
            # Get bot response
            with st.spinner("Analyzing document and thinking..."):
                try:
                    document_text = "\n".join([c.get('text', '') for c in st.session_state.processed_document.get('clauses', [])])
                    bot_response = chatbot.get_document_context_response(doc_user_input, document_text, st.session_state.doc_chat_history)
                    st.session_state.doc_chat_history.append({"role": "assistant", "content": bot_response})
                except Exception as e:
                    st.error(f"❌ Error getting response: {str(e)}")
                    st.session_state.doc_chat_history.append({"role": "assistant", "content": "Sorry, I encountered an error analyzing the document. Please try again."})
            
            st.rerun()

def show_privacy_page():
    st.header("🔒 Privacy & Security - Data Redaction")

    if st.session_state.processed_document is None:
        st.warning("⚠️ Please upload a document first in the Document Upload page.")
        return

    st.info("This page uses Google Cloud DLP to find and redact sensitive information from your document.")

    # Get the full text of the document
    full_text = "\n".join([c.get('text', '') for c in st.session_state.processed_document.get('clauses', [])])

    # Redaction button
    if st.button("🔍 Scan and Redact Document"):
        with st.spinner("Redacting sensitive information..."):
            try:
                # You need to set your Google Cloud Project ID in your environment variables
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
                if not project_id:
                    st.error("❌ GOOGLE_CLOUD_PROJECT_ID environment variable not set.")
                    return

                privacy_processor = PrivacyProcessor(project_id)
                redacted_text = privacy_processor.redact_text(full_text)
                st.session_state.redacted_text = redacted_text
                st.success("✅ Redaction complete!")
            except Exception as e:
                st.error(f"❌ Error during redaction: {str(e)}")

    # Display the redacted text
    if st.session_state.redacted_text:
        st.subheader("Redacted Document Text")
        st.text_area("Redacted Text", st.session_state.redacted_text, height=400)

if __name__ == "__main__":
    main()
