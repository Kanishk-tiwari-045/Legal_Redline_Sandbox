import React, { useState, useRef, useEffect } from 'react'
import { useAppState } from '../state/StateContext'
import api from '../api'
import { toast } from 'react-toastify'

export default function ChatbotPageNew() {
  const { state } = useAppState()
  const { sessionId } = state // Get the real sessionId from the global state
  const [generalHistory, setGeneralHistory] = useState([])
  const [documentHistory, setDocumentHistory] = useState([])
  const [activeTab, setActiveTab] = useState('general')
  const [currentMessage, setCurrentMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const isInitialMount = useRef(true);
  
  // Critical refs for input management
  const textareaRef = useRef(null)
  const messagesEndRef = useRef(null)
  const lastCursorPosition = useRef(0)
  const isUserTyping = useRef(false)
  const inputContainerRef = useRef(null)

  // Track when user is actively interacting with input
  const handleInputFocus = () => {
    isUserTyping.current = true
  }

  const handleInputBlur = (e) => {
    // Only set typing to false if focus moved outside input container
    if (!inputContainerRef.current?.contains(e.relatedTarget)) {
      isUserTyping.current = false
    }
  }

  const handleInputChange = (e) => {
    // Store cursor position before state change
    const cursorPos = e.target.selectionStart
    lastCursorPosition.current = cursorPos
    
    // Update message state
    setCurrentMessage(e.target.value)
    
    // Restore cursor position after React re-render
    requestAnimationFrame(() => {
      if (textareaRef.current && isUserTyping.current) {
        textareaRef.current.setSelectionRange(cursorPos, cursorPos)
      }
    })
  }

  // Auto-resize function that preserves cursor position
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current
    if (!textarea || !isUserTyping.current) return

    // Store current cursor position
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    
    // Adjust height
    textarea.style.height = 'auto'
    const newHeight = Math.min(textarea.scrollHeight, 80)
    textarea.style.height = newHeight + 'px'
    
    // Restore cursor position immediately
    textarea.setSelectionRange(start, end)
  }

  // Safe scroll function that respects input focus
  const scrollToBottom = () => {
    if (isUserTyping.current) return // Never scroll while user is typing
    
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.closest('.overflow-y-auto')
      if (container) {
        container.scrollTop = container.scrollHeight
      } else {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" })
      }
    }
  }

  // Force scroll to bottom (for initial load and tab switching)
  const forceScrollToBottom = () => {
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.closest('.overflow-y-auto')
      if (container) {
        container.scrollTop = container.scrollHeight
      } else {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" })
      }
    }
  }

  // Reset page state when session resets
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return; // Skip the effect on the first run
    }

    setGeneralHistory([])
    setDocumentHistory([])
    setCurrentMessage('')
    setActiveTab('general')
    setLoading(false)
    isUserTyping.current = false
    toast.info("Chat session reset");
  }, [state.resetFlag])

  // Handle new messages - only scroll if user is not typing
  useEffect(() => {
    const messageCount = generalHistory.length + documentHistory.length
    if (messageCount > 0 && !isUserTyping.current) {
      const timeoutId = setTimeout(scrollToBottom, 100)
      return () => clearTimeout(timeoutId)
    }
  }, [generalHistory.length, documentHistory.length])

  // Scroll to bottom when component mounts or tab changes
  useEffect(() => {
    const timeoutId = setTimeout(forceScrollToBottom, 200)
    return () => clearTimeout(timeoutId)
  }, [activeTab])

  // Scroll to bottom when there are existing messages on page load
  useEffect(() => {
    const currentHistory = activeTab === 'general' ? generalHistory : documentHistory
    if (currentHistory.length > 0) {
      const timeoutId = setTimeout(forceScrollToBottom, 300)
      return () => clearTimeout(timeoutId)
    }
  }, [generalHistory, documentHistory, activeTab])

  // Adjust height when content changes, preserving cursor
  useEffect(() => {
    if (isUserTyping.current) {
      adjustTextareaHeight()
    }
  }, [currentMessage])

  // Scroll when loading state changes (to show loading indicator and responses)
  useEffect(() => {
    if (!isUserTyping.current) {
      const timeoutId = setTimeout(forceScrollToBottom, 150)
      return () => clearTimeout(timeoutId)
    }
  }, [loading])

  const addMessage = (role, content, isGeneral = true) => {
    const message = { role, content, timestamp: new Date() }
    if (isGeneral) {
      setGeneralHistory(prev => [...prev, message])
    } else {
      setDocumentHistory(prev => [...prev, message])
    }
  }

  const handleSendMessage = async (isGeneral = true) => {
    if (!currentMessage.trim() || !sessionId) {
      if (!sessionId) toast.error("Session not initialized. Please wait.");
      return;
    }

    const userMessage = currentMessage.trim()
    setCurrentMessage('')
    addMessage('user', userMessage, isGeneral)
    setLoading(true)

    setTimeout(forceScrollToBottom, 100)
    setTimeout(() => {
      if (textareaRef.current) {
        textareaRef.current.focus()
        isUserTyping.current = true
      }
    }, 50)

    try {
      // This object is perfectly constructed.
      const fullChatData = {
        session_id: sessionId,
        type: isGeneral ? 'general' : 'document',
        prompt: userMessage,
        history: isGeneral ? generalHistory : documentHistory,
        document_text: !isGeneral && state.document ? 
          state.document.clauses?.map(c => c.text).join('\n') : ''
      }

      // Call the new API endpoint
      // Instead of `api.startChat(chatData)`, we call `api.post`
      // 1. Call the startChat function from your api.js file
      const response = await api.startChat(fullChatData)
      
      // 2. Access .job_id directly (since api.startChat already returns the JSON)
      if (response.job_id) {
        const cleanup = api.startJobPolling(response.job_id, (job) => {
          if (job.status === 'completed' && job.result) {
            addMessage('assistant', job.result.response, isGeneral)
            setLoading(false)
          } else if (job.status === 'failed') {
            const errorMsg = "Sorry, I encountered an error. Please try again."
            toast.error(errorMsg);
            addMessage('assistant', errorMsg, isGeneral)
            setLoading(false)
          }
        })
      }
    } catch (error) {
      const errorMsg = "Sorry, I encountered a network error. Please try again."
      toast.error(errorMsg);
      addMessage('assistant', errorMsg, isGeneral)
      setLoading(false)
    }
  }

  const clearHistory = (isGeneral = true) => {
    if (isGeneral) {
      setGeneralHistory([])
      toast.success("General history cleared");
    } else {
      setDocumentHistory([])
      toast.success("Document history cleared");
    }
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const isGeneral = activeTab === 'general'
  const currentHistory = isGeneral ? generalHistory : documentHistory

  if (!state.document && !isGeneral) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">📄 No Document Loaded</h2>
          <p className="text-gray-300 mb-6">Please upload a document first to use document-specific chat.</p>
          <button
            onClick={() => {
              setActiveTab('general')
              toast.info("Switched to General Assistant");
            }}
            className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-6 py-3 rounded-lg font-semibold hover:from-indigo-600 hover:to-purple-600 transition-all duration-200"
          >
            Switch to General Chat
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-white mb-4 flex items-center justify-center gap-3">
            <span className="text-indigo-400">🤖</span>
            Legal AI Assistant
          </h1>
          
          {/* Tab Switching - Horizontal Layout */}
          <div className="flex justify-center">
            <div className="bg-gray-700/50 backdrop-blur-sm rounded-xl p-1 flex space-x-1">
              <button
                onClick={() => {
                  setActiveTab('general')
                  toast.info("Switched to General Assistant");
                }}
                className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 text-sm ${
                  activeTab === 'general'
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                    : 'text-gray-300 hover:bg-gray-600 hover:text-white'
                }`}
              >
                🌟 General Assistant
              </button>
              <button
                onClick={() => {
                  if (state.document) {
                    setActiveTab('document')
                    toast.info("Switched to Document Q&A");
                  } else {
                    toast.warn("Please upload a document to use this tab.");
                  }
                }}
                className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 text-sm ${
                  activeTab === 'document'
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                    : !state.document 
                      ? 'text-gray-500 cursor-not-allowed' 
                      : 'text-gray-300 hover:bg-gray-600 hover:text-white'
                }`}
              >
                📄 Document Q&A
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full p-6 min-h-0">
        
        {/* Messages Area */}
        <div className="flex-1 bg-gray-800/30 backdrop-blur-sm rounded-2xl border border-gray-700 mb-6 flex flex-col min-h-0 max-h-[70vh]">
          
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-700 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{isGeneral ? '🌟' : '📄'}</span>
              <div>
                <h3 className="font-semibold text-white">
                  {isGeneral ? 'General Legal Assistant' : 'Document Analysis'}
                </h3>
                <p className="text-sm text-gray-400">
                  {isGeneral 
                    ? 'Ask any legal question' 
                    : `Analyzing ${state.document?.clauses?.length || 0} clauses`
                  }
                </p>
              </div>
            </div>
            
            {currentHistory.length > 0 && (
              <button
                onClick={() => clearHistory(isGeneral)}
                className="text-gray-400 hover:text-red-400 transition-colors duration-200 text-sm px-3 py-1 hover:bg-gray-700 rounded-lg"
              >
                🗑️ Clear
              </button>
            )}
          </div>

          {/* Messages List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0 scroll-smooth">
            {currentHistory.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">{isGeneral ? '🌟' : '📄'}</div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  {isGeneral ? 'General Legal Assistant' : 'Document Q&A Ready'}
                </h3>
                <p className="text-gray-400 mb-6">
                  {isGeneral 
                    ? 'Ask me anything about legal topics, contracts, or legal procedures.' 
                    : 'Ask questions about your uploaded document and get detailed analysis.'
                  }
                </p>
              </div>
            ) : (
              currentHistory.map((message, index) => (
                <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} w-full`}>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-3 break-words overflow-hidden ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white'
                      : 'bg-gray-700 text-white border border-gray-600'
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-300">
                        {message.role === 'user' ? '👤 You' : '🤖 Assistant'}
                      </span>
                      <span className="text-xs text-gray-400">
                        {formatTimestamp(message.timestamp)}
                      </span>
                    </div>
                    <div className="space-y-1">
                      {message.content.split('\n').map((line, i) => (
                        <p key={i} className="text-sm leading-relaxed break-words whitespace-pre-wrap">{line}</p>
                      ))}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {loading && (
              <div className="flex justify-start">
                <div className="max-w-[85%] bg-gray-700 rounded-2xl px-4 py-3 border border-gray-600">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-gray-300">🤖 Assistant</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-xs text-gray-400">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area - CRITICAL SECTION */}
        <div 
          ref={inputContainerRef}
          className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700 p-4"
        >
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <textarea
                ref={textareaRef}
                value={currentMessage}
                onChange={handleInputChange}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                placeholder={isGeneral ? 
                  "Ask a general legal question..." : 
                  "Ask a question about the uploaded document..."
                }
                rows={1}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage(isGeneral)
                  }
                }}
                disabled={loading || (!isGeneral && !state.document)}
                className="w-full p-3 bg-gray-700/70 border border-gray-600 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-800 disabled:cursor-not-allowed text-white placeholder-gray-400 text-sm leading-tight transition-all duration-200"
                style={{ 
                  minHeight: '44px',
                  maxHeight: '80px',
                  height: 'auto'
                }}
              />
            </div>
            <button
              onClick={() => handleSendMessage(isGeneral)}
              disabled={!currentMessage.trim() || loading || (!isGeneral && !state.document)}
              className={`px-4 py-3 rounded-xl font-semibold transition-all duration-200 flex items-center justify-center ${
                !currentMessage.trim() || loading || (!isGeneral && !state.document)
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white hover:from-indigo-600 hover:to-purple-600 shadow-lg hover:shadow-xl transform hover:scale-105'
              }`}
              style={{ minWidth: '52px', height: '44px' }}
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                '📤'
              )}
            </button>
          </div>
          
          {!isGeneral && state.document && (
            <div className="mt-3 p-3 bg-indigo-900/30 border border-indigo-700/50 rounded-lg">
              <p className="text-xs text-indigo-300 flex items-center gap-2">
                <span>📄</span>
                Analyzing: {state.document.clauses?.length || 0} clauses from your document
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}