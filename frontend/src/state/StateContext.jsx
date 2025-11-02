import React, { createContext, useContext, useReducer, useEffect } from 'react'

const STORAGE_KEY = 'legal_ai_app_state'

const getInitialState = () => {
  // Try to load from localStorage first
  try {
    const savedState = localStorage.getItem(STORAGE_KEY)
    if (savedState) {
      const parsedState = JSON.parse(savedState)
      // Merge with default structure
      return {
        sessionId: null, // Wait for App.jsx to provide this

        sessionStartTime: parsedState.sessionStartTime || new Date().toISOString(),
        resetFlag: 0,
        document: parsedState.document || null,
        riskyClauses: parsedState.riskyClauses || [],
        rewriteHistory: parsedState.rewriteHistory || {},
        // REMOVED chatHistory
        activeJobs: {},
        jobResults: parsedState.jobResults || {},
        activities: parsedState.activities || []
      }
    }
  } catch (error) {
    console.warn('Failed to load state from localStorage:', error)
  }
  
  // Fallback to default initial state
  return {
    sessionId: null, // Wait for App.jsx to provide this

    sessionStartTime: new Date().toISOString(),
    resetFlag: 0,
    document: null,
    riskyClauses: [],
    rewriteHistory: {},
    // REMOVED chatHistory
    activeJobs: {},
    jobResults: {},
    activities: []
  }
}

const initialState = getInitialState()

function reducer(state, action) {
  switch (action.type) {
    // This is called by App.jsx after it gets a session ID from the backend
    case 'SET_CHAT_SESSION':
      return {
        ...state,
        sessionId: action.payload,
      };

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
    
    // case 'ADD_CHAT_MESSAGE':
    //   return {
    //     ...state,
    //     chatHistory: [...state.chatHistory, action.payload],
    //     activities: [...state.activities, {
    //       id: Date.now(),
    //       timestamp: new Date().toISOString(),
    //       type: 'chat_interaction',
    //       description: `Chat: ${action.payload.type === 'user' ? 'User question' : 'AI response'}`,
    //       data: { messageType: action.payload.type }
    //     }]
    //   }
    
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
        sessionId: null, // Reset session ID

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

// Helper function to save state to localStorage
const saveStateToStorage = (state) => {
  try {
    // Don't persist activeJobs (they're temporary)
    const stateToSave = {
      ...state,
      activeJobs: {} // Always clear active jobs in storage
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave))
  } catch (error) {
    console.warn('Failed to save state to localStorage:', error)
  }
}

// Helper function to clear localStorage completely
const clearAllStorage = () => {
  try {
    // Clear our specific key
    localStorage.removeItem(STORAGE_KEY)
    
    // Also clear any other legal AI related keys that might exist
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.includes('legal') || key.includes('ai') || key.includes('app')) {
        localStorage.removeItem(key)
      }
    })
    
    // Clear session storage as well
    sessionStorage.clear()
  } catch (error) {
    console.warn('Failed to clear storage:', error)
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  
  // Enhanced dispatch that also handles persistence
  const enhancedDispatch = (action) => {
    dispatch(action)
    
    // For RESET_SESSION, clear storage completely
    if (action.type === 'RESET_SESSION') {
      clearAllStorage()
    }
  }
  
  // Save state to localStorage whenever it changes
  useEffect(() => {
    // Don't save on the very first render or after reset
    if (state.resetFlag === 0) {
      saveStateToStorage(state)
    }
  }, [state])
  
  // Log session start activity only once
  useEffect(() => {
    if (state.activities.length === 0 || !state.activities.some(a => a.type === 'session_started')) {
      dispatch({
        type: 'LOG_ACTIVITY',
        payload: {
          type: 'session_started',
          description: state.document ? 'Session resumed with existing data' : 'New session started',
          data: { sessionId: state.sessionId, hasExistingData: !!state.document }
        }
      })
    }
  }, [])
  
  return <AppContext.Provider value={{ state, dispatch: enhancedDispatch }}>{children}</AppContext.Provider>
}

export function useAppState() {
  return useContext(AppContext)
}
