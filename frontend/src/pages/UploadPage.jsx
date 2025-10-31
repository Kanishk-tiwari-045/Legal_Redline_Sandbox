import React, { useState, useEffect, useRef } from 'react'
import { useAppState } from '../state/StateContext'
import api from '../api'
import { toast } from 'react-toastify'

export default function UploadPage() {
  const { state, dispatch } = useAppState()
  const { sessionId } = state;
  const [file, setFile] = useState(null)
  const [forceOcr, setForceOcr] = useState(false)
  const [uploadJob, setUploadJob] = useState(null)
  const isInitialMount = useRef(true);
  // Reset local state when session resets
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return; // Skip the effect on the first run
    }

    setFile(null)
    setForceOcr(false)
    setUploadJob(null)

    // TRIGGER 3: "New session" toast
    toast.info("New session started");
  }, [state.resetFlag])

  // Check for existing completed jobs on component mount
  useEffect(() => {
    // Only run this check *after* the sessionId is available
    if (sessionId) {
      checkExistingJobs()
    }
  }, [sessionId]) // <-- Run this effect when sessionId changes, when it's loaded)

  async function checkExistingJobs() {
    if (!sessionId) return;

    try {
      const jobs = await api.getAllJobs()
      console.log('Existing jobs:', jobs)
      
      // Find the most recent completed document processing job
      const completedJob = jobs
        .filter(job => job.job_type === 'document_processing' && job.status === 'completed')
        .sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at))[0]
      
      if (completedJob && completedJob.result) {
        console.log('Found completed job:', completedJob)
        dispatch({ type: 'SET_DOCUMENT', payload: completedJob.result.document })
        dispatch({ type: 'SET_RISKY', payload: completedJob.result.risky_clauses })
        
        // Log activity for found job
        dispatch({
          type: 'LOG_ACTIVITY',
          payload: {
            type: 'data_restored',
            description: `Restored analysis: ${completedJob.result.risky_clauses?.length || 0} risky clauses`,
            data: { 
              jobId: completedJob.job_id,
              totalClauses: completedJob.result.document?.clauses?.length || 0
            }
          }
        })
      }
    } catch (error) {
      console.error('Failed to check existing jobs:', error)
      // Add error toast
      toast.error("Failed to check for existing jobs.");
    }
  }

  async function onUpload() {
    if (!file) return

    // Check if the session is ready before trying to upload
    if (!sessionId) {
      toast.error("Session is not ready. Please wait a moment.");
      return;
    }
    
    try {
      console.log('Starting upload for file:', file.name)
      const response = await api.uploadFile(file, forceOcr)
      console.log('Upload response:', response)
      
      
      if (response.job_id) {
        // TRIGGER 1: "Document is uploaded" toast
        toast.info(`Processing: ${file.name}`); // <-- ADDED

        setUploadJob({ job_id: response.job_id, status: 'processing' })
        dispatch({ 
          type: 'ADD_JOB', 
          payload: { 
            job_id: response.job_id, 
            job_type: 'document_processing',
            status: 'processing' 
          } 
        })
        
        // Log activity
        dispatch({
          type: 'LOG_ACTIVITY',
          payload: {
            type: 'document_uploaded',
            description: `Processing: ${file.name}`,
            data: { filename: file.name, jobId: response.job_id }
          }
        })
        
        // Start polling for job completion
        const cleanup = api.startJobPolling(response.job_id, (job) => {
          console.log('Job update:', job)
          setUploadJob(job)
          dispatch({ type: 'UPDATE_JOB', payload: job })
          
          // Handle streaming updates - update state with partial results
          if (job.result) {
            if (job.result.document) {
              dispatch({ type: 'SET_DOCUMENT', payload: job.result.document })
            }
            if (job.result.risky_clauses) {
              dispatch({ type: 'SET_RISKY', payload: job.result.risky_clauses })
            }
          }
          
          if (job.status === 'completed' && job.result) {
            console.log('Job completed with result:', job.result)
            const riskCount = job.result.risky_clauses?.length || 0;
            
            // TRIGGER 2: "Analysis complete" toast
            toast.success(`Analysis complete: ${riskCount} risks found!`);
            
            // Log completion activity
            dispatch({
              type: 'LOG_ACTIVITY',
              payload: {
                type: 'risk_analysis',
                description: `Analysis complete: ${job.result.risky_clauses?.length || 0} risks found`,
                data: { 
                  totalClauses: job.result.document?.clauses?.length || 0,
                  riskyClauses: job.result.risky_clauses?.length || 0
                }
              }
            })
            
            setUploadJob(null)
          } else if (job.status === 'failed') {
            console.error('Job failed:', job.error)
            // Add error toast
            toast.error(`Analysis failed: ${job.error || 'Unknown error'}`);
            setUploadJob(job)
          }
        }, 3000)
        
        // Store cleanup function
        window.currentJobCleanup = cleanup
      }
    } catch (error) {
      console.error('Upload failed:', error)
      // Add error toast
      toast.error(`Upload failed: ${error.message}`);
      setUploadJob({ status: 'failed', error: error.message })
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span className="text-blue-400">📄</span>
            Document Analysis
          </h1>
          <p className="text-gray-300">AI-powered legal document risk analysis</p>
        </div>

        {/* Upload Card */}
        <div className="bg-gray-800 rounded-2xl shadow-xl p-8 mb-8 border border-gray-700">
          <div className="space-y-6">
            {/* File Input */}
            <div>
              <label className="block text-sm font-semibold text-gray-300 mb-3">
                Select Document
              </label>
              <input 
                type="file" 
                accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
                onChange={(e) => setFile(e.target.files[0])} 
                className="block w-full text-sm text-gray-300 file:mr-4 file:py-3 file:px-6 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer cursor-pointer border border-gray-600 bg-gray-700 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              
              {file && (
                <div className="mt-2 p-3 bg-green-900/30 border border-green-700 rounded-lg">
                  <p className="text-sm text-green-300 flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    Selected: <span className="font-medium">{file.name}</span>
                  </p>
                </div>
              )}
            </div>

            {/* OCR Option */}
            <div className="flex items-center p-4 bg-gray-700 rounded-lg">
              <input 
                type="checkbox" 
                id="forceOcr"
                checked={forceOcr}
                onChange={(e) => setForceOcr(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-600 border-gray-500 rounded focus:ring-blue-500"
              />
              <label htmlFor="forceOcr" className="ml-3 text-sm font-medium text-gray-300 cursor-pointer">
                Force OCR for scanned documents
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <button 
                onClick={onUpload} 
                disabled={!file || uploadJob?.status === 'processing'}
                className={`flex-1 py-4 px-6 rounded-lg font-semibold text-white transition-all duration-200 ${
                  !file || uploadJob?.status === 'processing'
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 transform hover:scale-[1.02] shadow-lg hover:shadow-xl'
                }`}
              >
                {uploadJob?.status === 'processing' ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" className="opacity-25" />
                      <path fill="currentColor" className="opacity-75" d="M4 12a8 8 0 018-8v8z" />
                    </svg>
                    Processing...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <span>🚀</span>
                    Analyze Document
                  </span>
                )}
              </button>
              
              <button 
                onClick={checkExistingJobs}
                className="px-6 py-4 bg-gray-700 text-gray-300 rounded-lg font-semibold hover:bg-gray-600 transition-colors duration-200 flex items-center gap-2"
              >
                <span>🔄</span>
                Check Results
              </button>
            </div>
          </div>
        </div>

        {/* Processing Status */}
        {uploadJob && (
          <div className="bg-gray-800 rounded-2xl shadow-xl p-6 mb-8 border border-gray-700">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-blue-600 rounded-full">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white">Processing Status</h3>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Status:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  uploadJob.status === 'completed' ? 'bg-green-600 text-white' :
                  uploadJob.status === 'processing' ? 'bg-blue-600 text-white' :
                  uploadJob.status === 'failed' ? 'bg-red-600 text-white' :
                  'bg-gray-600 text-white'
                }`}>
                  {uploadJob.status.charAt(0).toUpperCase() + uploadJob.status.slice(1)}
                </span>
              </div>
              
              {uploadJob.progress !== undefined && (
                <div>
                  <div className="flex justify-between text-sm text-gray-400 mb-1">
                    <span>Progress</span>
                    <span>{uploadJob.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadJob.progress}%` }}
                    />
                  </div>
                </div>
              )}
              
              {uploadJob.error && (
                <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg">
                  <p className="text-red-300 text-sm">
                    <span className="font-medium">Error:</span> {uploadJob.error}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Document Summary */}
        {state.document && (
          <div className="bg-gray-800 rounded-2xl shadow-xl p-6 mb-8 border border-gray-700">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-green-600 rounded-full">
                <span className="text-2xl">✅</span>
              </div>
              <h3 className="text-xl font-semibold text-white">Document Loaded</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-600 to-blue-700 p-6 rounded-xl text-center">
                <div className="text-3xl mb-2">📑</div>
                <div className="text-2xl font-bold text-white">{state.document.total_pages || 0}</div>
                <div className="text-sm text-blue-200 font-medium">Pages</div>
              </div>
              
              <div className="bg-gradient-to-br from-purple-600 to-purple-700 p-6 rounded-xl text-center">
                <div className="text-3xl mb-2">📝</div>
                <div className="text-2xl font-bold text-white">{state.document.clauses?.length || 0}</div>
                <div className="text-sm text-purple-200 font-medium">Clauses</div>
              </div>
              
              <div className="bg-gradient-to-br from-red-600 to-red-700 p-6 rounded-xl text-center">
                <div className="text-3xl mb-2">⚠️</div>
                <div className="text-2xl font-bold text-white">{state.riskyClauses?.length || 0}</div>
                <div className="text-sm text-red-200 font-medium">Risks Found</div>
              </div>
            </div>
          </div>
        )}

        {/* Active Jobs */}
        {Object.keys(state.activeJobs).length > 0 && (
          <div className="bg-gray-800 rounded-2xl shadow-xl p-6 border border-gray-700">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-yellow-600 rounded-full">
                <svg className="w-6 h-6 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white">Active Jobs</h3>
            </div>
            
            <div className="space-y-3">
              {Object.values(state.activeJobs).map(job => (
                <div key={job.job_id} className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
                    <span className="font-medium text-gray-300">
                      {job.job_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">{job.status}</span>
                    {job.progress && (
                      <span className="text-sm font-medium text-blue-400">({job.progress}%)</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}