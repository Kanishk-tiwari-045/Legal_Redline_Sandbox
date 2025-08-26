import html
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
from .diff_generator import DiffGenerator

class ExportManager:
    """Manages export functionality for reports"""
    
    def __init__(self):
        self.diff_generator = DiffGenerator()
    
    def generate_html_report(self, report_data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Generate a comprehensive HTML report"""
        
        try:
            document = report_data.get('document', {})
            risky_clauses = report_data.get('risky_clauses', [])
            rewrite_history = report_data.get('rewrite_history', [])
            
            # Build HTML report with error handling for each section
            html_content = self._generate_html_header()
            html_content += self._generate_report_summary(document, risky_clauses, rewrite_history)
            html_content += self._generate_risk_analysis_section(risky_clauses)
            html_content += self._generate_rewrites_section(risky_clauses, rewrite_history, options)
            html_content += self._generate_html_footer()
            
            return html_content
            
        except Exception as e:
            # Return a basic error report if generation fails
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Report Generation Error</title></head>
            <body>
                <h1>Report Generation Error</h1>
                <p>There was an error generating the report: {html.escape(str(e))}</p>
                <p>Please try again or contact support.</p>
            </body>
            </html>
            """
    
    def generate_pdf_report(self, report_data: Dict[str, Any], options: Dict[str, Any]) -> bytes:
        """Generate a PDF-formatted HTML report"""
        
        try:
            # Generate basic HTML content first
            html_content = self.generate_html_report(report_data, options)
            
            # Add PDF-specific styling and structure
            pdf_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Legal Redline Report</title>
    <style>
        @page {{ margin: 1in; }}
        body {{ 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            color: #333;
            max-width: none;
            margin: 0;
            padding: 0;
        }}
        .page-break {{ page-break-before: always; }}
        .section {{ margin-bottom: 30px; }}
        .clause-box {{ 
            border: 1px solid #ddd; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 5px;
        }}
        .metrics {{ display: block; }}
        .metric {{ 
            display: inline-block; 
            margin: 10px; 
            text-align: center;
            border: 1px solid #ccc;
            padding: 10px;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
            
            return pdf_html.encode('utf-8')
            
        except Exception as e:
            # Return a simple error document
            error_html = f"""<!DOCTYPE html>
<html>
<head><title>PDF Generation Error</title></head>
<body>
    <h1>PDF Generation Error</h1>
    <p>Error: {html.escape(str(e))}</p>
</body>
</html>"""
            return error_html.encode('utf-8')
    
    def _generate_html_header(self) -> str:
        """Generate HTML header with styling"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Legal Redline Report</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }
                .header h1 {
                    margin: 0;
                    font-size: 2.5em;
                }
                .header p {
                    margin: 10px 0 0;
                    opacity: 0.9;
                }
                .section {
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    margin-bottom: 25px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .section h2 {
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                    margin-top: 0;
                }
                .metrics {
                    display: flex;
                    justify-content: space-around;
                    flex-wrap: wrap;
                    margin: 20px 0;
                }
                .metric {
                    text-align: center;
                    min-width: 150px;
                    margin: 10px;
                }
                .metric .number {
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #3498db;
                }
                .metric .label {
                    color: #7f8c8d;
                    font-size: 0.9em;
                }
                .risk-high { border-left: 5px solid #e74c3c; }
                .risk-medium { border-left: 5px solid #f39c12; }
                .risk-low { border-left: 5px solid #27ae60; }
                .clause-box {
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    padding: 20px;
                    margin: 15px 0;
                }
                .original-text {
                    background: #fff5f5;
                    border-left: 4px solid #e53e3e;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 5px 5px 0;
                }
                .rewritten-text {
                    background: #f0fff4;
                    border-left: 4px solid #38a169;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 5px 5px 0;
                }
                .rationale {
                    background: #e6f3ff;
                    border: 1px solid #b3d9ff;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                .disclaimer {
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                    text-align: center;
                }
                .footer {
                    text-align: center;
                    color: #7f8c8d;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                }
                @media (max-width: 768px) {
                    .metrics {
                        flex-direction: column;
                        align-items: center;
                    }
                    .header h1 {
                        font-size: 2em;
                    }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚖️ Legal Redline Report</h1>
                <p>AI-Powered Contract Analysis and Clause Rewriting</p>
                <p>Generated on: {}</p>
            </div>
            
            <div class="disclaimer">
                <strong>⚠️ LEGAL DISCLAIMER:</strong> This report is generated by AI for informational purposes only 
                and does not constitute legal advice. Always consult with a qualified attorney for legal matters.
            </div>
        """.format(datetime.now().strftime("%B %d, %Y at %I:%M %p"))
    
    def _generate_report_summary(self, document: Dict, risky_clauses: List, rewrite_history: Dict) -> str:
        """Generate the report summary section"""
        
        total_rewrites = sum(len(rewrites) for rewrites in rewrite_history.values()) if rewrite_history else 0
        avg_risk_score = sum(clause['risk_analysis']['score'] for clause in risky_clauses) / len(risky_clauses) if risky_clauses else 0
        
        # Safely get document data
        total_pages = document.get('total_pages', 'N/A')
        total_clauses = len(document.get('clauses', []))
        
        return f"""
            <div class="section">
                <h2>📊 Executive Summary</h2>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="number">{total_pages}</div>
                        <div class="label">Total Pages</div>
                    </div>
                    <div class="metric">
                        <div class="number">{total_clauses}</div>
                        <div class="label">Total Clauses</div>
                    </div>
                    <div class="metric">
                        <div class="number">{len(risky_clauses)}</div>
                        <div class="label">Risky Clauses</div>
                    </div>
                    <div class="metric">
                        <div class="number">{len(rewrite_history)}</div>
                        <div class="label">Clauses Rewritten</div>
                    </div>
                    <div class="metric">
                        <div class="number">{avg_risk_score:.1f}</div>
                        <div class="label">Avg Risk Score</div>
                    </div>
                </div>
                
                <p><strong>Document Analysis:</strong> This contract contains {len(risky_clauses)} potentially 
                problematic clauses that may warrant attention during negotiation or review.</p>
                
                <p><strong>Recommendations:</strong> Review the highlighted clauses and consider the suggested 
                rewrites to improve contract balance and reduce potential risks.</p>
            </div>
        """
    
    def _generate_risk_analysis_section(self, risky_clauses: List) -> str:
        """Generate the risk analysis section"""
        
        if not risky_clauses:
            return """
                <div class="section">
                    <h2>🔍 Risk Analysis</h2>
                    <p>No significant risks detected in the contract.</p>
                </div>
            """
        
        # Calculate risk distribution
        risk_counts = {}
        for clause in risky_clauses:
            for tag in clause['risk_analysis']['tags']:
                risk_counts[tag] = risk_counts.get(tag, 0) + 1
        
        risk_labels = {
            'auto_renew': 'Auto-Renewal Clauses',
            'unilateral_change': 'Unilateral Modification Rights',
            'short_notice': 'Short Notice Periods',
            'high_penalty': 'High Penalty Fees',
            'exclusive_jurisdiction': 'Exclusive Jurisdiction',
            'liability_limitation': 'Liability Limitations',
            'broad_termination': 'Broad Termination Rights'
        }
        
        risk_html = """
            <div class="section">
                <h2>🔍 Risk Analysis</h2>
                
                <h3>Risk Distribution</h3>
                <ul>
        """
        
        for tag, count in risk_counts.items():
            label = risk_labels.get(tag, tag.replace('_', ' ').title())
            risk_html += f"<li><strong>{label}:</strong> {count} clause(s)</li>"
        
        risk_html += """
                </ul>
                
                <h3>Detailed Risk Assessment</h3>
        """
        
        for clause in risky_clauses:
            risk_score = clause['risk_analysis']['score']
            risk_class = 'risk-high' if risk_score >= 4 else 'risk-medium' if risk_score >= 2 else 'risk-low'
            
            risk_html += f"""
                <div class="clause-box {risk_class}">
                    <h4>{clause['title']} (Risk Score: {risk_score})</h4>
                    <p><strong>Page:</strong> {clause['page']}</p>
                    <p><strong>Risk Factors:</strong> {', '.join(tag.replace('_', ' ').title() for tag in clause['risk_analysis']['tags'])}</p>
                    <p><strong>Rationale:</strong> {html.escape(clause['risk_analysis'].get('rationale', 'No rationale provided'))}</p>
                    
                    <details>
                        <summary>View Full Clause Text</summary>
                        <div class="original-text">
                            {html.escape(clause['text'])}
                        </div>
                    </details>
                </div>
            """
        
        risk_html += "</div>"
        return risk_html
    
    def _generate_rewrites_section(self, risky_clauses: List, rewrite_history: Dict, options: Dict) -> str:
        """Generate the rewrites section"""
        
        if not rewrite_history:
            return """
                <div class="section">
                    <h2>✏️ Clause Rewrites</h2>
                    <p>No clause rewrites have been generated yet.</p>
                </div>
            """
        
        rewrites_html = """
            <div class="section">
                <h2>✏️ AI-Generated Clause Rewrites</h2>
                <p>The following clauses have been rewritten to improve balance and reduce risk:</p>
        """
        
        for clause_id, rewrites in rewrite_history.items():
            # Find the corresponding clause
            clause = next((c for c in risky_clauses if c['clause_id'] == clause_id), None)
            if not clause:
                continue
            
            latest_rewrite = rewrites[-1]['result']
            
            rewrites_html += f"""
                <div class="clause-box">
                    <h3>{clause['title']}</h3>
                    <p><strong>Original Page:</strong> {clause['page']} | <strong>Risk Score:</strong> {clause['risk_analysis']['score']}</p>
            """
            
            if options.get('include_original', True):
                rewrites_html += f"""
                    <h4>📋 Original Clause</h4>
                    <div class="original-text">
                        {html.escape(clause['text'])}
                    </div>
                """
            
            rewrites_html += f"""
                <h4>✏️ AI-Generated Rewrite</h4>
                <div class="rewritten-text">
                    {html.escape(latest_rewrite.get('rewrite', 'Rewrite not available'))}
                </div>
            """
            
            if options.get('include_rationale', True):
                rewrites_html += f"""
                    <h4>💡 Rationale</h4>
                    <div class="rationale">
                        {html.escape(latest_rewrite.get('rationale', 'Rationale not available'))}
                    </div>
                """
                
                if 'fallback_levels' in latest_rewrite and latest_rewrite['fallback_levels']:
                    rewrites_html += """
                        <h4>🎯 Alternative Negotiation Positions</h4>
                        <ol>
                    """
                    for fallback in latest_rewrite['fallback_levels']:
                        rewrites_html += f"<li>{html.escape(fallback)}</li>"
                    rewrites_html += "</ol>"
            
            if options.get('include_diff', True):
                try:
                    diff_html = self.diff_generator.generate_inline_diff(clause['text'], latest_rewrite.get('rewrite', ''))
                    rewrites_html += f"""
                        <h4>📊 Change Highlights</h4>
                        {diff_html}
                    """
                except Exception as e:
                    rewrites_html += f"""
                        <h4>📊 Change Highlights</h4>
                        <p>Unable to generate diff comparison: {html.escape(str(e))}</p>
                    """
            
            # Show controls used
            controls = rewrites[-1]['controls']
            rewrites_html += f"""
                <details>
                    <summary>🎛️ Rewrite Parameters Used</summary>
                    <ul>
                        <li>Notice Period: {controls.get('notice_days', 'N/A')} days</li>
                        <li>Late Fee Percentage: {controls.get('late_fee_percent', 'N/A')}%</li>
                        <li>Jurisdiction Neutral: {'Yes' if controls.get('jurisdiction_neutral') else 'No'}</li>
                        <li>Favor Customer: {'Yes' if controls.get('favor_customer') else 'No'}</li>
                    </ul>
                </details>
            """
            
            rewrites_html += "</div>"
        
        rewrites_html += "</div>"
        return rewrites_html
    
    def _generate_html_footer(self) -> str:
        """Generate HTML footer"""
        return """
            <div class="footer">
                <p>Report generated by Legal Redline Sandbox</p>
                <p>This AI-powered tool is designed to assist in contract review but does not replace professional legal advice.</p>
                <p>&copy; 2025 Legal Redline Sandbox. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

    def export_clause_data(self, clause_data: Dict, rewrite_data: Dict) -> Dict[str, Any]:
        """Export individual clause data for external use"""
        
        export_data = {
            'clause_info': {
                'id': clause_data['clause_id'],
                'title': clause_data['title'],
                'page': clause_data['page'],
                'original_text': clause_data['text'],
                'word_count': clause_data['word_count']
            },
            'risk_analysis': clause_data.get('risk_analysis', {}),
            'rewrite_info': {
                'rewritten_text': rewrite_data.get('rewrite', ''),
                'rationale': rewrite_data.get('rationale', ''),
                'fallback_options': rewrite_data.get('fallback_levels', []),
                'risk_reduction': rewrite_data.get('risk_reduction', ''),
                'controls_used': rewrite_data.get('controls_used', {}),
                'api_model': rewrite_data.get('api_model', ''),
                'generation_timestamp': datetime.now().isoformat()
            },
            'change_analysis': self.diff_generator.generate_summary_diff(
                clause_data['text'], 
                rewrite_data.get('rewrite', '')
            ) if rewrite_data.get('rewrite') else {}
        }
        
        return export_data
