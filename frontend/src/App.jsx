import React, { useEffect, useState } from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import { useAppState } from './state/StateContext'
import HomePage from './pages/Home'
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
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import api from './api'
import { v4 as uuidv4 } from 'uuid'

export default function App() {
  const { state, dispatch } = useAppState()
  const navigate = useNavigate()

  // No loading state needed - session created on file upload
  
  const handleLeaveSession = async () => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      '⚠️ Are you sure you want to leave the session?\n\nThis will:\n• Clear all uploaded documents\n• Reset analysis results\n• Clear chat history\n• Remove all rewrite history\n• Permanently delete all saved data\n\nThis action cannot be undone.'
    )

    if (confirmed) {
      // Reset the session state (this will also clear localStorage via enhancedDispatch)
      dispatch({ type: 'RESET_SESSION' })

      // Delete session data from storage
      localStorage.removeItem('sessionId');

      // Set a temporary flag in sessionStorage.
      sessionStorage.setItem('showNewSessionToast', 'true');

      // Navigate to home page
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

      {/* This component is the "Toaster" */}
      <ToastContainer
        position="top-right"
        autoClose={4000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
      
      <main className="min-h-screen">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
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