import React, { useEffect, useState } from 'react'
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
import Footer from './components/Footer.jsx'
import Header from './components/Header.jsx'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import api from './api'

import { v4 as uuidv4 } from 'uuid';
import api from './api'; // The api.js file you just created

export default function App() {
  const { state, dispatch } = useAppState()
  const navigate = useNavigate()

  // Add a loading state
  // We can't show the app until we know we have a user token.
  const [isLoading, setIsLoading] = useState(true);

  // This effect runs once when the app loads
  useEffect(() => {
    // This function checks for a token and creates a guest user if needed.
    const initializeSession = async () => {
      let token = localStorage.getItem('accessToken');

      if (!token) {
        // No token found, so let's create a new anonymous user
        try {
          // 1. Generate random user credentials
          const randomEmail = `${uuidv4()}@guest.com`;
          const randomPassword = uuidv4();

          // 2. Register this new guest user (using api.js)
          await api.registerUser(randomEmail, randomEmail, randomPassword);

          // 3. Log in as this new user to get a token (using api.js)
          const loginResponse = await api.loginUser(randomEmail, randomPassword);

          // .json() is handled inside api.js, so we get the data directly
          token = loginResponse.access_token;
          localStorage.setItem('accessToken', token);

        } catch (err) {
          console.error("Failed to create anonymous session:", err);
        }
      }

      // Now we have a token (either old or new).
      // Let's get/create a chat session for this user.
      try {
        // 4. Create chat session (using api.js)
        const sessionResponse = await api.createChatSession();
        
        // Save this new session ID to our global state
        dispatch({ 
          type: 'SET_CHAT_SESSION', 
          payload: sessionResponse.id 
        });

      } catch (err) {
        console.error("Failed to create/get chat session:", err);

        if (err.response && err.response.status === 401) {
          localStorage.removeItem('accessToken');
          window.location.reload();
        }
      }
      
      // We're done! Show the app.
      setIsLoading(false);
    };

    initializeSession();
  }, [dispatch]); // Run this only once
  
  const handleLeaveSession = () => {
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
      
      // Navigate to upload page
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
<<<<<<< HEAD

=======
>>>>>>> ishita

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