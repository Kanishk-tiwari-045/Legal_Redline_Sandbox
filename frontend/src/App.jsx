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
import Footer from './components/Footer.jsx'
import Header from './components/Header.jsx'

export default function App() {
  const { state, dispatch } = useAppState()
  const navigate = useNavigate()
  
  const handleLeaveSession = () => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      '⚠️ Are you sure you want to leave the session?\n\nThis will:\n• Clear all uploaded documents\n• Reset analysis results\n• Clear chat history\n• Remove all rewrite history\n• Permanently delete all saved data\n\nThis action cannot be undone.'
    )
    
    if (confirmed) {
      // Reset the session state (this will also clear localStorage via enhancedDispatch)
      dispatch({ type: 'RESET_SESSION' })
      
      // Navigate to upload page
      navigate('/')
      
      // Small delay to ensure state is processed, then reload
      setTimeout(() => {
        window.location.reload()
      }, 100)
    }
  }
  
  return (
    <div className="min-h-screen bg-gray-900">
      
      <Header handleLeaveSession={handleLeaveSession} />

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

      <Footer />
    </div>
  )
}
