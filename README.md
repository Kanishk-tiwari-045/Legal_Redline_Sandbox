# Legal Redline Sandbox

An AI-powered contract analysis and clause rewriting tool with React frontend and FastAPI backend. The application helps legal professionals identify risky contract clauses, suggests balanced rewrites using AI, and generates comprehensive reports with visual diffs.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud Project with Gemini API access

### 1. Environment Setup
```bash
# Clone and setup
git clone <your-repo-url>
cd Legal_Redline_Sandbox

# Configure environment
# Edit .env with your Google Cloud credentials
```

### 2. Automated Setup (Recommended)
```bash
# Windows
setup.bat

# Linux/Mac  
chmod +x setup.sh
./setup.sh
```

### 3. Manual Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend  
cd ../frontend
npm install
```

### 4. Run Application
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate  
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 5. Test System
```bash
python test_system.py  # Validates setup
```

**🌐 Access**: http://localhost:3000

## 📋 Required .env Configuration

```env
# Google Cloud (Required)
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./path/to/service-account.json  
GOOGLE_API_KEY=your-gemini-api-key

# Security (Required)
SECRET_KEY=your-64-character-random-secret

# Basic Config
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
```

## 🏗️ Architecture

- **Frontend**: React + Vite with Context state management
- **Backend**: FastAPI with async job processing + JWT auth
- **AI**: Google Gemini API for clause analysis and rewriting
- **Processing**: Document AI OCR + Cloud DLP for privacy scanning
- **Features**: Real-time job polling, export reports, diff visualization

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

# Quick Start

## Prerequisites
- Python 3.11+
- Node.js 16+
- Google Gemini API Key (get it from [Google AI Studio](https://aistudio.google.com/))

## Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET_KEY=your_secret_key_for_jwt
GOOGLE_CLOUD_PROJECT_ID=your_project_id (optional, for OCR/DLP)
```

## Installation & Running

### Backend (FastAPI)
```powershell
# Create virtual environment
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt

# Run the backend server
uvicorn backend.main:app --reload --port 8000
```

### Frontend (React)
```powershell
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000` and the backend API at `http://localhost:8000`.

## First Time Setup

1. Register a new account at `http://localhost:3000/register`
2. Login with your credentials
3. Upload a contract document (PDF or image)
4. Review risk analysis and use the redline sandbox

3. **Set up environment variables**

   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

   Or export the environment variable:
   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

# Usage Guide

## 🏠 Main Application

### 1. 📄 Document Upload
- Upload your PDF contract documents
- The system automatically processes and analyzes the document

### 2. 🔍 Risk Analysis
- View identified risky clauses with risk scores
- Understand why certain clauses might be problematic

### 3. ✏️ Redline Sandbox
- Select and rewrite specific risky clauses
- Use AI-powered suggestions for better alternatives

### 4. 📊 Export Report
- Generate comprehensive HTML or PDF reports
- Include analysis, rewrites, and side-by-side comparisons

### 5. 💬 Chat Assistant (New!)
- **General Chat**: Ask legal questions without a document
- **Document-Context Chat**: Get answers specific to your uploaded contract
- **Features**:
  - Conversation history and context awareness
  - Document-aware responses when contracts are uploaded
  - Export chat history
  - Clear chat and statistics

#### Chat Assistant Usage
- **Without Document**: Ask general legal questions like "What is force majeure?"
- **With Document**: Reference your uploaded contract like "Explain the termination clause"
- **Example Queries**:
  - "What are the main risks in this contract?"
  - "What's the difference between arbitration and mediation?"
  - "How should I negotiate better contract terms?"

## 🧪 Testing

Run the test suite:
```bash
# Test the chatbot functionality
python test_chatbot.py

# Test the risk detection system
python test_risk_detection.py
```

## ⚖️ Legal Disclaimer

**IMPORTANT**: This tool is for informational purposes only and does not constitute legal advice. Always consult with a qualified attorney for legal matters. The AI analyses and suggestions provided are educational and should not be relied upon as legal counsel.

# Project Structure

```
Gen_AI_Google_Hackathon/
├── app.py                      # Main Streamlit application
├── utils/
│   ├── chatbot.py             # AI Chat Assistant
│   ├── clause_rewriter.py     # AI clause rewriting
│   ├── diff_generator.py      # Text diff generation
│   ├── export_manager.py      # Report export functionality
│   ├── pdf_processor.py       # PDF document processing
│   └── risk_detector.py       # Risk analysis engine
├── test_chatbot.py           # Chatbot functionality tests
├── test_risk_detection.py    # Risk detection tests
├── sample_contract.txt       # Sample contract for testing
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```
