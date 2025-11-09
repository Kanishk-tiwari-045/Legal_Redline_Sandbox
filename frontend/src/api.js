const API_BASE = import.meta.env.VITE_API_BASE || 'https://legal-redline-sandbox.onrender.com'
const AUTH_API_BASE = import.meta.env.VITE_AUTH_API_BASE || 'https://legal-redline-sandbox-1.onrender.com'

// Helper to get auth token
function getAuthToken() {
  return localStorage.getItem('auth_token')
}

// Helper to get auth headers
function getAuthHeaders() {
  const token = getAuthToken()
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

async function apiCall(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      signal: controller.signal,
      headers: {
        ...options.headers,
        ...getAuthHeaders(),
      }
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      // If it fails, create an error object that our app can understand
      const errorData = await response.json().catch(() => ({}));
      const error = new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      
      // This part makes it behave like axios, so err.response.status works
      error.response = { 
        status: response.status,
        data: errorData,
      };
      throw error;
    }

    // If we are here, the request was successful
    return response
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timed out');
    }
    throw error;
  }
}

// Auth API functions
export async function sendOtp(email) {
  const res = await fetch(`${AUTH_API_BASE}/auth/send-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
  return res.json()
}

export async function verifyOtp(email, otp) {
  const res = await fetch(`${AUTH_API_BASE}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp }),
  })
  return res.json()
}

export async function verifyToken() {
  const token = getAuthToken()
  if (!token) return { valid: false }
  
  try {
    const res = await fetch(`${AUTH_API_BASE}/auth/verify-token`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    return res.json()
  } catch (error) {
    return { valid: false }
  }
}

export async function logout() {
  const token = getAuthToken()
  if (!token) return

  try {
    await fetch(`${AUTH_API_BASE}/auth/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  } catch (error) {
    console.error('Logout error:', error)
  }

  // Clear local storage
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_user')
  localStorage.removeItem('auth_session_id')
}

export async function registerUser(email, username, password) {
  const res = await fetch(`${AUTH_API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password }),
  })
  return res.json()
}

export async function loginUser(email, password) {
  const res = await fetch(`${AUTH_API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return res.json()
}

export async function createChatSession() {
  const res = await apiCall('/api/chat/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  return res.json()
}

export function isAuthenticated() {
  return !!getAuthToken()
}

export function getAuthUser() {
  const user = localStorage.getItem('auth_user')
  return user ? JSON.parse(user) : null
}

// Job API
export async function getJobStatus(jobId) {
  const res = await apiCall(`/jobs/${jobId}`)
  return res?.json()
}

export async function getAllJobs() {
  const res = await apiCall('/jobs')
  return res?.json()
}

// Main API functions
export async function uploadFile(file, forceOcr = false) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('force_ocr', forceOcr)

  const res = await apiCall('/upload', { method: 'POST', body: fd })
  return res?.json()
}

export async function rewriteClause(clause, controls) {
  const res = await apiCall('/rewrite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clause, controls }),
  })
  return res?.json()
}

export async function startChat(chatData) {
  const res = await apiCall('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(chatData),
  })
  return res?.json()
}

export async function explainTerm(term, context = '') {
  const res = await apiCall('/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ term, context }),
  })
  return res?.json()
}

export async function analyzeClause(clauseText) {
  const res = await apiCall('/analyze/clause', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clause_text: clauseText }),
  })
  return res?.json()
}

export async function translateToPlain(legalText) {
  const res = await apiCall('/translate/plain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ legal_text: legalText }),
  })
  return res?.json()
}

export async function getHistoricalContext(clauseText) {
  const res = await apiCall('/historical/context', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clause_text: clauseText }),
  })
  return res?.json()
}

export async function exportReport(reportData, format, options) {
  const res = await apiCall('/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ report_data: reportData, format, options }),
  })
  return res?.json()
}

export async function generateDiff(original, rewritten) {
  const res = await apiCall('/diff', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ original, rewritten }),
  })
  return res?.json()
}

export async function redactDocument(text) {
  const res = await apiCall('/privacy/redact', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return res?.json()
}

export async function processPrivacy(documentContent, infoTypes, redactionLevel) {
  const res = await apiCall('/privacy/redact', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      text: documentContent,
      info_types: infoTypes,
      redaction_level: redactionLevel
    }),
  })
  return res?.json()
}

// Job polling helper
export function startJobPolling(jobId, onUpdate, interval = 2000) {
  const poll = async () => {
    try {
      const job = await getJobStatus(jobId)
      onUpdate(job)
      
      if (job.status === 'completed' || job.status === 'failed') {
        clearInterval(pollInterval)
      }
    } catch (error) {
      console.error('Polling error:', error)
      clearInterval(pollInterval)
    }
  }
  
  const pollInterval = setInterval(poll, interval)
  poll() // Initial call
  
  return () => clearInterval(pollInterval) // Return cleanup function
}

export default { 
  uploadFile, rewriteClause, startChat, explainTerm,
  analyzeClause, translateToPlain, getHistoricalContext, exportReport, 
  generateDiff, redactDocument, processPrivacy, getJobStatus, getAllJobs, startJobPolling,
  // Auth exports
  sendOtp, verifyOtp, verifyToken, logout, isAuthenticated, getAuthUser,
  registerUser, loginUser, createChatSession
}
