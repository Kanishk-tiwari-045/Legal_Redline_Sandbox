const API_BASE = import.meta.env.VITE_API_BASE || 'https://legal-redline-sandbox.onrender.com'

// Helper to get session ID
function getSessionId() {
  return localStorage.getItem('sessionId')
}

async function apiCall(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    // Don't set Content-Type for FormData - let the browser set it with proper boundary
    const headers = options.body instanceof FormData 
      ? { ...options.headers }
      : { 'Content-Type': 'application/json', ...options.headers };

    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      signal: controller.signal,
      headers
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

// Session management functions

export async function createChatSession() {
  const res = await apiCall('/api/chat/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  const data = await res.json()
  
  // Store session ID in localStorage
  localStorage.setItem('sessionId', data.id)
  
  return data
}

// Job API
export async function getJobStatus(jobId) {
  const res = await apiCall(`/api/jobs/${jobId}`)
  return res?.json()
}

export async function getAllJobs() {
  const res = await apiCall('/api/jobs')
  return res?.json()
}

// Main API functions
export async function uploadFile(file, forceOcr = false) {
  const fd = new FormData()
  fd.append('file', file)

  const url = `/api/upload?force_ocr=${forceOcr}`
  const res = await apiCall(url, { method: 'POST', body: fd })
  return res?.json()
}

export async function rewriteClause(clause, controls) {
  const res = await apiCall('/api/rewrite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clause, controls }),
  })
  return res?.json()
}

export async function startChat(chatData) {
  const res = await apiCall('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(chatData),
  })
  return res?.json()
}

export async function explainTerm(term, context = '') {
  const res = await apiCall('/api/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ term, context }),
  })
  return res?.json()
}

export async function analyzeClause(clauseText) {
  const res = await apiCall('/api/analyze/clause', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clause_text: clauseText }),
  })
  return res?.json()
}

export async function translateToPlain(legalText) {
  const res = await apiCall('/api/translate/plain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ legal_text: legalText }),
  })
  return res?.json()
}

export async function getHistoricalContext(clauseText) {
  const res = await apiCall('/api/historical/context', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clause_text: clauseText }),
  })
  return res?.json()
}

export async function exportReport(reportData, format, options) {
  const res = await apiCall('/api/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ report_data: reportData, format, options }),
  })
  return res?.json()
}

export async function generateDiff(original, rewritten) {
  const res = await apiCall('/api/diff', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ original, rewritten }),
  })
  return res?.json()
}

export async function redactDocument(text) {
  const res = await apiCall('/api/privacy/redact', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return res?.json()
}

export async function processPrivacy(documentContent, infoTypes, redactionLevel) {
  const res = await apiCall('/api/privacy/redact', {
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
  createChatSession
}
