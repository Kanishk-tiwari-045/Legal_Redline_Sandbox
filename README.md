# Overview

Legal Redline Sandbox is an AI-powered contract analysis and clause rewriting tool built with Streamlit. The application helps legal professionals identify risky contract clauses, suggests balanced rewrites using AI, and generates comprehensive reports with visual diffs. The tool focuses on making contract review more efficient while providing educational insights into potential legal risks.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Streamlit Web Application**: Single-page application with sidebar navigation for different workflow stages
- **Session State Management**: Maintains processed documents, risky clauses, selected clauses, and rewrite history across user interactions
- **Component-Based UI**: Modular interface with separate sections for document upload, risk analysis, clause rewriting, and export functionality

## Backend Architecture
- **Modular Processing Pipeline**: Separate utility classes handle distinct responsibilities:
  - `PDFProcessor`: Document parsing and text extraction using PyMuPDF
  - `RiskDetector`: Rule-based clause risk analysis with pattern matching
  - `ClauseRewriter`: AI-powered clause rewriting using Google Gemini API
  - `DiffGenerator`: HTML diff generation for comparing original vs. rewritten text
  - `ExportManager`: Report generation in HTML and PDF formats

## AI Integration
- **Google Gemini API**: Primary AI service for clause rewriting with structured JSON responses
- **Rule-Based Risk Detection**: Pattern matching system for identifying problematic clauses including auto-renewal, unilateral changes, short notice periods, high penalties, and exclusive jurisdiction clauses
- **Contextual Rewriting**: AI considers user-specified controls and generates rationale, fallback positions, and risk reduction explanations

## Data Processing
- **PDF Text Extraction**: Uses PyMuPDF (fitz) for reliable PDF parsing and page-by-page text extraction
- **Clause Identification**: Pattern-based clause detection using regex for common legal document structures
- **Risk Scoring**: Numerical risk assessment system with thresholds for different clause types
- **Diff Generation**: HTML-based visual comparison between original and rewritten clauses

## Export System
- **Multi-Format Reports**: Generates both HTML and PDF reports with comprehensive analysis
- **Visual Diff Integration**: Includes side-by-side comparisons with syntax highlighting
- **Structured Output**: Reports contain risk analysis, rewrite suggestions, and implementation recommendations

# External Dependencies

## AI Services
- **Google Gemini API**: Primary AI service for clause rewriting and analysis via `google.genai` client
- **Environment-Based Authentication**: Requires `GEMINI_API_KEY` environment variable for API access

## Document Processing
- **PyMuPDF (fitz)**: PDF parsing and text extraction library for handling legal documents
- **Python-docx**: Microsoft Word document processing capabilities
- **PyPDF**: Additional PDF processing utilities

## Web Framework
- **Streamlit**: Primary web framework for building the interactive user interface
- **FastAPI/Uvicorn**: Backend API framework for potential service expansion

## Utility Libraries
- **difflib**: Built-in Python library for generating text differences and comparisons
- **base64**: Encoding utilities for file handling and data transfer
- **tempfile**: Temporary file management for document processing
- **re (regex)**: Pattern matching for clause identification and risk detection

## Data Handling
- **JSON**: Data serialization for API communication and session state management
- **Pandas/NumPy**: Data manipulation and analysis capabilities for document statistics
- **HTML**: Custom HTML generation for reports and diff visualization

## Potential Cloud Integration
- **Google Cloud Services**: Architecture supports integration with Document AI, Cloud Storage, and AI Platform for enhanced processing capabilities
- **Cloud Logging**: Structured logging support for production deployment monitoring