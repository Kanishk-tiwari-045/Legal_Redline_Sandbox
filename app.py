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

# Page configuration
st.set_page_config(
    page_title="Legal Redline Sandbox",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processed_document' not in st.session_state:
    st.session_state.processed_document = None
if 'risky_clauses' not in st.session_state:
    st.session_state.risky_clauses = []
if 'selected_clause' not in st.session_state:
    st.session_state.selected_clause = None
if 'rewrite_history' not in st.session_state:
    st.session_state.rewrite_history = {}

# Initialize processors
pdf_processor = PDFProcessor()
risk_detector = RiskDetector()
clause_rewriter = ClauseRewriter()
diff_generator = DiffGenerator()
export_manager = ExportManager()

def main():
    # Header
    st.title("⚖️ Legal Redline Sandbox")
    st.markdown("### AI-Powered Contract Analysis and Clause Rewriting Tool")
    
    # Legal disclaimer
    st.error("⚠️ **IMPORTANT DISCLAIMER**: This tool is for informational purposes only and does not constitute legal advice. Always consult with a qualified attorney for legal matters.")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page:",
            ["📄 Document Upload", "🔍 Risk Analysis", "✏️ Redline Sandbox", "📊 Export Report"]
        )
    
    if page == "📄 Document Upload":
        show_upload_page()
    elif page == "🔍 Risk Analysis":
        show_risk_analysis_page()
    elif page == "✏️ Redline Sandbox":
        show_redline_sandbox_page()
    elif page == "📊 Export Report":
        show_export_page()

def show_upload_page():
    st.header("📄 Document Upload & Processing")
    
    uploaded_file = st.file_uploader(
        "Upload your contract (PDF format)",
        type=['pdf'],
        help="Upload a PDF contract for analysis"
    )
    
    if uploaded_file is not None:
        with st.spinner("Processing document..."):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_file_path = tmp_file.name
                
                # Process the PDF
                document_data = pdf_processor.process_pdf(tmp_file_path)
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
                # Store in session state
                st.session_state.processed_document = document_data
                
                # Display summary
                st.success("✅ Document processed successfully!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Pages", document_data['total_pages'])
                with col2:
                    st.metric("Total Clauses", len(document_data['clauses']))
                with col3:
                    st.metric("Word Count", document_data['word_count'])
                
                # Show preview of clauses
                st.subheader("Document Preview")
                for i, clause in enumerate(document_data['clauses'][:3]):  # Show first 3 clauses
                    with st.expander(f"Clause {i+1}: {clause['title']}"):
                        st.write(f"**Page:** {clause['page']}")
                        st.write(f"**Text:** {clause['text'][:200]}...")
                
                # Automatically run risk analysis
                with st.spinner("Analyzing risks..."):
                    risky_clauses = risk_detector.analyze_document(document_data)
                    st.session_state.risky_clauses = risky_clauses
                
                st.info(f"🎯 Found {len(risky_clauses)} potentially risky clauses. Navigate to Risk Analysis to review them.")
                
            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
    else:
        st.info("👆 Please upload a PDF contract to begin analysis")

def show_risk_analysis_page():
    st.header("🔍 Risk Analysis")
    
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
        for tag in clause['risk_analysis']['tags']:
            risk_counts[tag] = risk_counts.get(tag, 0) + 1
        total_score += clause['risk_analysis']['score']
    
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
        risk_score = clause['risk_analysis']['score']
        risk_color = "🔴" if risk_score >= 4 else "🟡" if risk_score >= 2 else "🟢"
        
        with st.expander(f"{risk_color} {clause['title']} (Risk Score: {risk_score})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Original Text:**")
                st.write(clause['text'])
                st.write(f"**Page:** {clause['page']}")
            
            with col2:
                st.write("**Risk Factors:**")
                for tag in clause['risk_analysis']['tags']:
                    label = risk_labels.get(tag, tag.replace('_', ' ').title())
                    st.write(f"• {label}")
                
                st.write("**Rationale:**")
                st.write(clause['risk_analysis']['rationale'])
                
                if st.button(f"Edit in Sandbox", key=f"edit_{i}"):
                    st.session_state.selected_clause = clause
                    st.rerun()

def show_redline_sandbox_page():
    st.header("✏️ Redline Sandbox")
    
    if st.session_state.processed_document is None:
        st.warning("⚠️ Please upload a document first in the Document Upload page.")
        return
    
    if not st.session_state.risky_clauses:
        st.info("No risky clauses detected. Please run risk analysis first.")
        return
    
    # Clause selection
    st.subheader("Select Clause to Edit")
    
    clause_options = [
        f"{i+1}. {clause['title']} (Risk: {clause['risk_analysis']['score']})"
        for i, clause in enumerate(st.session_state.risky_clauses)
    ]
    
    selected_idx = st.selectbox(
        "Choose a clause to rewrite:",
        range(len(clause_options)),
        format_func=lambda x: clause_options[x],
        index=0 if st.session_state.selected_clause is None else next(
            (i for i, c in enumerate(st.session_state.risky_clauses) 
             if c['clause_id'] == st.session_state.selected_clause['clause_id']), 0
        )
    )
    
    current_clause = st.session_state.risky_clauses[selected_idx]
    st.session_state.selected_clause = current_clause
    
    # Main editing interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Original Clause")
        st.info(f"**Page:** {current_clause['page']}")
        st.text_area(
            "Original Text:",
            current_clause['text'],
            height=300,
            disabled=True,
            key="original_text"
        )
        
        # Risk information
        st.subheader("⚠️ Risk Analysis")
        st.write(f"**Risk Score:** {current_clause['risk_analysis']['score']}")
        st.write("**Risk Factors:**")
        for tag in current_clause['risk_analysis']['tags']:
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
                    clause_id = current_clause['clause_id']
                    if clause_id not in st.session_state.rewrite_history:
                        st.session_state.rewrite_history[clause_id] = []
                    st.session_state.rewrite_history[clause_id].append({
                        'controls': controls,
                        'result': rewrite_result
                    })
                    
                    st.success("✅ Rewrite generated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error generating rewrite: {str(e)}")
        
        # Display latest rewrite if available
        clause_id = current_clause['clause_id']
        if clause_id in st.session_state.rewrite_history and st.session_state.rewrite_history[clause_id]:
            latest_rewrite = st.session_state.rewrite_history[clause_id][-1]['result']
            
            st.text_area(
                "Rewritten Text:",
                latest_rewrite['rewrite'],
                height=200,
                key="rewritten_text"
            )
            
            # Show rationale
            with st.expander("📝 Rationale & Explanation"):
                st.write(latest_rewrite['rationale'])
                
                if 'fallback_levels' in latest_rewrite:
                    st.write("**Alternative Approaches:**")
                    for i, fallback in enumerate(latest_rewrite['fallback_levels']):
                        st.write(f"{i+1}. {fallback}")
            
            # Show diff
            st.subheader("📊 Side-by-Side Comparison")
            diff_html = diff_generator.generate_html_diff(
                current_clause['text'], 
                latest_rewrite['rewrite']
            )
            st.html(diff_html)

def show_export_page():
    st.header("📊 Export Report")
    
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
            clause = next((c for c in st.session_state.risky_clauses if c['clause_id'] == clause_id), None)
            if clause:
                latest_rewrite = rewrites[-1]['result']
                
                with st.expander(f"✏️ {clause['title']} ({len(rewrites)} version(s))"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Original:**")
                        st.write(clause['text'][:200] + "..." if len(clause['text']) > 200 else clause['text'])
                    
                    with col2:
                        st.write("**Latest Rewrite:**")
                        st.write(latest_rewrite['rewrite'][:200] + "..." if len(latest_rewrite['rewrite']) > 200 else latest_rewrite['rewrite'])

if __name__ == "__main__":
    main()
