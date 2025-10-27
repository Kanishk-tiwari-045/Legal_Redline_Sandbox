import React, { createContext, useContext, useReducer, useEffect } from 'react'

const initialState = {
  // Session state (persists until page refresh)
  sessionId: Math.random().toString(36).substr(2, 9),
  sessionStartTime: new Date().toISOString(),
  resetFlag: 0, // Increment this to trigger component resets
  
  // App state
  document: null,
  riskyClauses: [],
  rewriteHistory: {},
  chatHistory: [],
  
  // Job state
  activeJobs: {},
  jobResults: {},
  
  // Activity tracking
  activities: []
}

function reducer(state, action) {
  switch (action.type) {
    case 'LOG_ACTIVITY':
      return {
        ...state,
        activities: [...state.activities, {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          type: action.payload.type,
          description: action.payload.description,
          data: action.payload.data || null
        }]
      }
    
    case 'SET_DOCUMENT':
      return { 
        ...state, 
        document: action.payload,
        activities: [...state.activities, {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          type: 'document_uploaded',
          description: `Uploaded document: ${action.payload.filename}`,
          data: { filename: action.payload.filename, pages: action.payload.total_pages }
        }]
      }
    
    case 'SET_RISKY':
      return { 
        ...state, 
        riskyClauses: action.payload,
        activities: [...state.activities, {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          type: 'risk_analysis',
          description: `Found ${action.payload.length} risky clauses`,
          data: { count: action.payload.length }
        }]
      }
    
    case 'ADD_REWRITE':
      return { 
        ...state, 
        rewriteHistory: { ...state.rewriteHistory, [action.clauseId]: action.payload },
        activities: [...state.activities, {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          type: 'clause_rewritten',
          description: `Rewrote clause: ${action.clauseTitle || 'Unknown clause'}`,
          data: { clauseId: action.clauseId }
        }]
      }
    
    case 'ADD_CHAT_MESSAGE':
      return {
        ...state,
        chatHistory: [...state.chatHistory, action.payload],
        activities: [...state.activities, {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          type: 'chat_interaction',
          description: `Chat: ${action.payload.type === 'user' ? 'User question' : 'AI response'}`,
          data: { messageType: action.payload.type }
        }]
      }
    
    case 'ADD_JOB':
      return {
        ...state,
        activeJobs: { ...state.activeJobs, [action.payload.job_id]: action.payload }
      }
    
    case 'UPDATE_JOB':
      const updatedJobs = { ...state.activeJobs }
      if (action.payload.status === 'completed' || action.payload.status === 'failed') {
        delete updatedJobs[action.payload.job_id]
      } else {
        updatedJobs[action.payload.job_id] = action.payload
      }
      
      const updatedResults = { ...state.jobResults }
      if (action.payload.status === 'completed') {
        updatedResults[action.payload.job_id] = action.payload.result
      }
      
      return {
        ...state,
        activeJobs: updatedJobs,
        jobResults: updatedResults
      }
    
    case 'RESET_SESSION':
      return {
        ...initialState,
        sessionId: Math.random().toString(36).substr(2, 9),
        sessionStartTime: new Date().toISOString(),
        resetFlag: state.resetFlag + 1, // Increment reset counter
        activities: [{
          id: Date.now(),
          timestamp: new Date().toISOString(),
          type: 'session_reset',
          description: 'Session reset by user',
          data: { previousSessionId: state.sessionId }
        }]
      }
    
    default:
      return state
  }
}

const AppContext = createContext()

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  
  // Log session start activity
  useEffect(() => {
    dispatch({
      type: 'LOG_ACTIVITY',
      payload: {
        type: 'session_started',
        description: 'New session started',
        data: { sessionId: state.sessionId }
      }
    })
  }, [])
  
  return <AppContext.Provider value={{ state, dispatch }}>{children}</AppContext.Provider>
}

export function useAppState() {
  return useContext(AppContext)
}
