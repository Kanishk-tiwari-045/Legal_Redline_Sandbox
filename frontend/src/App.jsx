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

  // Add a loading state
  // We can't show the app until we know we have a user token.
  const [isLoading, setIsLoading] = useState(true);

  // This effect runs once when the app loads
  useEffect(() => {
    // Initialize app without requiring authentication
    const initializeSession = async () => {
      try {
        // Create an anonymous chat session for the user
        const sessionResponse = await api.createChatSession();
        
        // Save this new session ID to our global state
        dispatch({ 
          type: 'SET_CHAT_SESSION', 
          payload: sessionResponse.id 
        });

      } catch (err) {
        console.error("Failed to create chat session:", err);
        // Don't block the app if chat session creation fails
      }
      
      // Show the app regardless
      setIsLoading(false);
    };

    initializeSession();
  }, [dispatch]); // Run this only once
  
  const handleLeaveSession = async () => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      '⚠️ Are you sure you want to leave the session?\n\nThis will:\n• Clear all uploaded documents\n• Reset analysis results\n• Clear chat history\n• Remove all rewrite history\n• Log you out of authentication\n• Permanently delete all saved data\n\nThis action cannot be undone.'
    )

    if (confirmed) {
      // Logout from auth server
      await api.logout()

      // Reset the session state (this will also clear localStorage via enhancedDispatch)
      dispatch({ type: 'RESET_SESSION' })

      // Delete the token from storage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('sessionId');

      // Set a temporary flag in sessionStorage.
      // sessionStorage is perfect because it survives a page reload,
      // but is deleted when you close the browser tab.
      sessionStorage.setItem('showNewSessionToast', 'true');

      // Navigate to home page
      navigate('/')

      // Small delay to ensure state is processed, then reload
      setTimeout(() => {
        window.location.reload()
      }, 100)
    }
  }

  // Show a loading screen while we set up the session
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <h1 className="text-2xl font-bold text-white">🚀 Initializing Secure Session...</h1>
      </div>
    );
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