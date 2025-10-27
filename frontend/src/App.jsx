import React from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { useAppState } from './state/StateContext'
import UploadPage from './pages/UploadPage'
import RiskPage from './pages/RiskPage'
import SandboxPage from './pages/SandboxPage'
import ExplainerPage from './pages/ExplainerPage'
import ChatbotPage from './pages/ChatbotPage'
import ExportPage from './pages/ExportPage'
import PrivacyPage from './pages/PrivacyPage'
import DiffPage from './pages/DiffPage'

export default function App() {
  const { state, dispatch } = useAppState()
  const navigate = useNavigate()
  
  const handleLeaveSession = () => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      '⚠️ Are you sure you want to leave the session?\n\nThis will:\n• Clear all uploaded documents\n• Reset analysis results\n• Clear chat history\n• Remove all rewrite history\n\nThis action cannot be undone.'
    )
    
    if (confirmed) {
      // Clear any potential localStorage/sessionStorage
      localStorage.clear()
      sessionStorage.clear()
      
      // Reset the session state
      dispatch({ type: 'RESET_SESSION' })
      
      // Navigate to upload page
      navigate('/')
      
      // Force a page reload to ensure complete reset
      window.location.reload()
    }
  }
  
  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-800 shadow-lg border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3 group">
              <span className="text-3xl group-hover:scale-110 transition-transform duration-200">⚖️</span>
              <h1 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors duration-200">
                Legal AI
              </h1>
            </Link>
            
            <div className="flex items-center gap-4">
              <nav className="hidden md:flex items-center gap-1">
                <Link 
                  to="/" 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 hover:text-blue-400 transition-all duration-200"
                >
                  <span>📄</span>
                  Upload
                </Link>
                <Link 
                  to="/risk" 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 hover:text-red-400 transition-all duration-200"
                >
                  <span>⚠️</span>
                  Risk
                </Link>
                <Link 
                  to="/sandbox" 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 hover:text-green-400 transition-all duration-200"
                >
                  <span>✏️</span>
                  Edit
                </Link>
                <Link 
                  to="/explainer" 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 hover:text-purple-400 transition-all duration-200"
                >
                  <span>💡</span>
                  Explain
                </Link>
                <Link 
                  to="/chatbot" 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 hover:text-indigo-400 transition-all duration-200"
                >
                  <span>🤖</span>
                  Chat
                </Link>
                <Link 
                  to="/export" 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 hover:text-yellow-400 transition-all duration-200"
                >
                  <span>📊</span>
                  Export
                </Link>
                <Link 
                  to="/privacy" 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 hover:text-gray-100 transition-all duration-200"
                >
                  <span>🔒</span>
                  Privacy
                </Link>
                <Link 
                  to="/diff" 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-gray-300 hover:bg-gray-700 hover:text-orange-400 transition-all duration-200"
                >
                  <span>🔄</span>
                  Compare
                </Link>
              </nav>
              
              <button 
                onClick={handleLeaveSession}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
                title="Leave session and reset all data"
              >
                <span className="text-sm">🚪</span>
                <span className="text-sm font-medium">Leave Session</span>
              </button>
            </div>
          </div>
          
          {/* Mobile Navigation */}
          <div className="md:hidden mt-4 space-y-3">
            <nav className="grid grid-cols-4 gap-2">
              <Link to="/" className="flex flex-col items-center gap-1 px-2 py-2 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">
                <span>📄</span>Upload
              </Link>
              <Link to="/risk" className="flex flex-col items-center gap-1 px-2 py-2 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">
                <span>⚠️</span>Risk
              </Link>
              <Link to="/sandbox" className="flex flex-col items-center gap-1 px-2 py-2 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">
                <span>✏️</span>Edit
              </Link>
              <Link to="/explainer" className="flex flex-col items-center gap-1 px-2 py-2 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">
                <span>💡</span>Explain
              </Link>
              <Link to="/chatbot" className="flex flex-col items-center gap-1 px-2 py-2 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">
                <span>🤖</span>Chat
              </Link>
              <Link to="/export" className="flex flex-col items-center gap-1 px-2 py-2 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">
                <span>📊</span>Export
              </Link>
              <Link to="/privacy" className="flex flex-col items-center gap-1 px-2 py-2 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">
                <span>🔒</span>Privacy
              </Link>
              <Link to="/diff" className="flex flex-col items-center gap-1 px-2 py-2 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600">
                <span>🔄</span>Compare
              </Link>
            </nav>
            
            <button 
              onClick={handleLeaveSession}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white rounded-lg font-medium transition-all duration-200"
            >
              <span>🚪</span>
              <span className="text-sm font-medium">Leave Session</span>
            </button>
          </div>
        </div>
      </header>
      
      <main className="min-h-screen">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/risk" element={<RiskPage />} />
          <Route path="/sandbox" element={<SandboxPage />} />
          <Route path="/explainer" element={<ExplainerPage />} />
          <Route path="/chatbot" element={<ChatbotPage />} />
          <Route path="/export" element={<ExportPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/diff" element={<DiffPage />} />
        </Routes>
      </main>
    </div>
  )
}
