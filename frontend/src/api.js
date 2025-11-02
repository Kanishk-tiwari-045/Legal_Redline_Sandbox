const API_BASE = import.meta.env.VITE_API_BASE || '/api'

async function apiCall(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      ...options.headers,
    }
  })
  
  return response
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
  generateDiff, redactDocument, processPrivacy, getJobStatus, getAllJobs, startJobPolling, sendOtp, verifyOtp
}
