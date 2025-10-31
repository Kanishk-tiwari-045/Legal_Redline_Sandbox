import React, { useState, useEffect } from 'react'
import { useAppState } from '../state/StateContext'
import api from '../api'

export default function SandboxPage() {
  const { state, dispatch } = useAppState()
  const [selectedIdx, setSelectedIdx] = useState(0)
  const [rewrite, setRewrite] = useState('')
  const [loading, setLoading] = useState(false)
  // Reset local state when session resets
  useEffect(() => {
    setSelectedIdx(0)
    setRewrite('')
    setLoading(false)
  }, [state.resetFlag])

  const clause = state.riskyClauses?.[selectedIdx]

  async function onRewrite() {
    if (!clause) return
    setLoading(true)
    
    try {
      const controls = { 
        notice_days: 30, 
        late_fee_percent: 5.0, 
        jurisdiction_neutral: true, 
        favor_customer: true 
      }
      
      const res = await api.rewriteClause(clause, controls)
      
      if (res.job_id) {
        // Poll for job completion
        const cleanup = api.startJobPolling(res.job_id, (job) => {
          console.log('Rewrite job update:', job)
          
          if (job.status === 'completed' && job.result) {
            // Check if result contains an error
            if (job.result.error) {
              const errorType = job.result.error_type || 'unknown';
              let userMessage = job.result.rewrite || 'An error occurred during rewriting.';
              
              // Add helpful context for common errors
              if (errorType === 'rate_limit') {
                userMessage += '\n\n💡 Tip: The AI service is experiencing high demand. Try again in 2-3 minutes.';
              } else if (errorType === 'auth_error') {
                userMessage += '\n\n⚙️ This appears to be a configuration issue. Please contact support.';
              }
              
              setRewrite(userMessage);
            } else {
              const rewriteText = job.result.rewritten_clause || job.result.rewrite || JSON.stringify(job.result, null, 2)
              setRewrite(rewriteText)
              dispatch({ 
                type: 'ADD_REWRITE', 
                clauseId: clause.clause_id || `clause_${selectedIdx}`, 
                payload: job.result,
                clauseTitle: clause.title 
              })
            }
            setLoading(false)
          } else if (job.status === 'failed') {
            console.error('Rewrite job failed:', job.error)
            setRewrite(`Error: ${job.error || 'Rewrite failed'}`)
            setLoading(false)
          }
        })
      } else {
        setRewrite(res.rewrite || JSON.stringify(res))
        dispatch({ 
          type: 'ADD_REWRITE', 
          clauseId: clause.clause_id || `clause_${selectedIdx}`, 
          payload: res,
          clauseTitle: clause.title 
        })
        setLoading(false)
      }
    } catch (error) {
      setRewrite(`Error: ${error.message}`)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-green-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span className="text-green-400">✏️</span>
            Redline Sandbox
          </h1>
          <p className="text-gray-300 text-lg">Rewrite and improve risky contract clauses with AI assistance</p>
        </div>

        {/* No Risky Clauses State */}
        {!state.riskyClauses?.length ? (
          <div className="bg-gray-800 rounded-2xl shadow-xl p-12 text-center border border-gray-700">
            <div className="text-6xl mb-4">📝</div>
            <h3 className="text-2xl font-semibold text-white mb-2">No Risky Clauses Found</h3>
            <p className="text-gray-400 mb-6">Upload and analyze a document first to see clauses that need improvement</p>
            <button 
              onClick={() => window.location.href = '/'}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
            >
              Go to Upload Page
            </button>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Clause Selector */}
            <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
              <div className="flex items-center gap-4 mb-4">
                <span className="text-2xl">🎯</span>
                <h3 className="text-xl font-semibold text-white">Select Clause to Rewrite</h3>
              </div>
              
              <select 
                onChange={(e) => {
                  setSelectedIdx(Number(e.target.value))
                  setRewrite('')
                }} 
                value={selectedIdx}
                className="w-full p-4 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent bg-gray-700 text-white"
              >
                {state.riskyClauses.map((c, i) => (
                  <option key={i} value={i}>
                    Clause {i + 1}: {c.title || `Risk Score ${c.risk_analysis?.score || 'N/A'}`}
                  </option>
                ))}
              </select>

              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="bg-red-900 p-3 rounded-lg border border-red-700">
                  <div className="font-medium text-red-300">Risk Score</div>
                  <div className="text-2xl font-bold text-red-400">
                    {clause?.risk_analysis?.score || 'N/A'}/5
                  </div>
                </div>
                <div className="bg-blue-900 p-3 rounded-lg border border-blue-700">
                  <div className="font-medium text-blue-300">Risk Categories</div>
                  <div className="text-blue-400">
                    {clause?.risk_analysis?.tags?.length || 0} identified
                  </div>
                </div>
                <div className="bg-green-900 p-3 rounded-lg border border-green-700">
                  <div className="font-medium text-green-300">Word Count</div>
                  <div className="text-green-400">
                    {clause?.text?.split(' ').length || 0} words
                  </div>
                </div>
              </div>
            </div>

            {/* Clause Content and Rewrite */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Original Clause */}
              <div className="bg-gray-800 rounded-2xl shadow-lg border border-gray-700 overflow-hidden">
                <div className="bg-red-900 px-6 py-4 border-b border-red-700">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">📄</span>
                    <h3 className="text-xl font-semibold text-white">Original Clause</h3>
                    <span className="px-3 py-1 bg-red-600 text-white text-sm font-medium rounded-full">
                      Risk Score: {clause?.risk_analysis?.score || 'N/A'}
                    </span>
                  </div>
                </div>
                
                <div className="p-6">
                  <div className="bg-gray-900 p-4 rounded-lg border border-gray-600 max-h-96 overflow-y-auto">
                    <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
                      {clause?.text || 'No clause selected'}
                    </pre>
                  </div>
                  
                  {clause?.risk_analysis?.tags && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-gray-400 mb-2">Risk Categories:</p>
                      <div className="flex flex-wrap gap-2">
                        {clause.risk_analysis.tags.slice(0, 4).map((tag, index) => (
                          <span 
                            key={index}
                            className="px-3 py-1 bg-red-600 text-white text-xs font-medium rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                        {clause.risk_analysis.tags.length > 4 && (
                          <span className="px-3 py-1 bg-gray-600 text-gray-300 text-xs font-medium rounded-full">
                            +{clause.risk_analysis.tags.length - 4} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Rewritten Clause */}
              <div className="bg-gray-800 rounded-2xl shadow-lg border border-gray-700 overflow-hidden">
                <div className="bg-green-900 px-6 py-4 border-b border-green-700">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">✨</span>
                    <h3 className="text-xl font-semibold text-white">AI-Improved Version</h3>
                  </div>
                </div>
                
                <div className="p-6">
                  {!rewrite && !loading ? (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">🚀</div>
                      <p className="text-gray-400 mb-6">Click the button below to generate an improved version of this clause</p>
                      <button
                        onClick={onRewrite}
                        disabled={!clause || loading}
                        className="bg-gradient-to-r from-green-600 to-teal-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-teal-700 transition-all duration-200 shadow-lg hover:shadow-xl disabled:bg-gray-600 disabled:cursor-not-allowed"
                      >
                        ✏️ Generate Rewrite
                      </button>
                    </div>
                  ) : loading ? (
                    <div className="text-center py-12">
                      <div className="animate-spin w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                      <p className="text-gray-400">AI is rewriting your clause...</p>
                      <p className="text-sm text-gray-500 mt-2">This may take a moment</p>
                    </div>
                  ) : (
                    <div>
                      <div className="bg-green-900 p-4 rounded-lg border border-green-700 max-h-96 overflow-y-auto mb-4">
                        <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
                          {rewrite}
                        </pre>
                      </div>
                      
                      <div className="flex gap-3">
                        <button
                          onClick={onRewrite}
                          disabled={loading}
                          className="flex-1 bg-gradient-to-r from-green-600 to-teal-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-green-700 hover:to-teal-700 transition-all duration-200"
                        >
                          🔄 Generate New Version
                        </button>
                        
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(rewrite)
                            alert('Rewritten clause copied to clipboard!')
                          }}
                          className="px-6 py-3 bg-gray-600 text-gray-300 rounded-lg font-semibold hover:bg-gray-500 transition-colors duration-200"
                        >
                          📋 Copy
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Rewrite Controls */}
            <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">⚙️</span>
                <h3 className="text-xl font-semibold text-white">Rewrite Settings</h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 bg-blue-900 rounded-lg border border-blue-700 text-center">
                  <div className="text-2xl mb-2">📅</div>
                  <div className="font-semibold text-blue-300">Notice Period</div>
                  <div className="text-sm text-blue-400">30 days</div>
                </div>
                
                <div className="p-4 bg-purple-900 rounded-lg border border-purple-700 text-center">
                  <div className="text-2xl mb-2">💰</div>
                  <div className="font-semibold text-purple-300">Late Fee</div>
                  <div className="text-sm text-purple-400">5.0%</div>
                </div>
                
                <div className="p-4 bg-green-900 rounded-lg border border-green-700 text-center">
                  <div className="text-2xl mb-2">⚖️</div>
                  <div className="font-semibold text-green-300">Jurisdiction</div>
                  <div className="text-sm text-green-400">Neutral</div>
                </div>
                
                <div className="p-4 bg-orange-900 rounded-lg border border-orange-700 text-center">
                  <div className="text-2xl mb-2">🤝</div>
                  <div className="font-semibold text-orange-300">Favor</div>
                  <div className="text-sm text-orange-400">Customer</div>
                </div>
              </div>
              
              <p className="text-sm text-gray-400 mt-4">
                These settings are applied to generate customer-friendly rewrites with standard terms.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
