import React, { useState, useEffect, useRef } from 'react'
import { useAppState } from '../state/StateContext'
import api from '../api'
import { toast } from 'react-toastify'

export default function DiffPage() {
  const { state } = useAppState()
  const { sessionId } = state;
  const [selectedClause, setSelectedClause] = useState('')
  const [selectedVersion, setSelectedVersion] = useState('latest')
  const [diffJob, setDiffJob] = useState(null)
  const [diffResults, setDiffResults] = useState(null)
  const [viewMode, setViewMode] = useState('side-by-side') // 'side-by-side', 'unified', 'split'
  const isInitialMount = useRef(true);

  // Reset page state when session resets
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    setSelectedClause('')
    setSelectedVersion('latest')
    setDiffJob(null)
    setDiffResults(null)
    setViewMode('side-by-side')
    toast.info("Diff page reset");
  }, [state.resetFlag])

  const hasRewriteHistory = Object.keys(state.rewriteHistory).length > 0
  const availableClauses = hasRewriteHistory ? Object.keys(state.rewriteHistory) : []

  const getClauseVersions = (clauseId) => {
    const rewrites = state.rewriteHistory[clauseId]
    if (!rewrites) return []
    
    if (Array.isArray(rewrites)) {
      return rewrites.map((rewrite, index) => ({
        id: `version_${index}`,
        label: `Version ${index + 1}`,
        timestamp: rewrite.timestamp || new Date().toISOString(),
        content: rewrite.result?.rewrite || ''
      }))
    } else {
      return [{
        id: 'version_0',
        label: 'Rewritten Version',
        timestamp: rewrites.timestamp || new Date().toISOString(),
        content: rewrites.result?.rewrite || ''
      }]
    }
  }

  const getOriginalClause = (clauseId) => {
    const clause = state.riskyClauses.find(c => 
      c.clause_id === clauseId || c.title === clauseId
    )
    return clause?.text || 'Original text not available'
  }

  const handleGenerateDiff = async () => {
    if (!selectedClause) {
      toast.warn("Please select a clause first.");
      return
    }

    if (!sessionId) {
      toast.error("Session is not ready. Please wait a moment.");
      return;
    }

    const originalText = getOriginalClause(selectedClause)
    const versions = getClauseVersions(selectedClause)
    
    let comparisonText = ''
    if (selectedVersion === 'latest' && versions.length > 0) {
      comparisonText = versions[versions.length - 1].content
    } else if (selectedVersion === 'all') {
      comparisonText = versions.map(v => v.content).join('\n\n--- Next Version ---\n\n')
    } else {
      const version = versions.find(v => v.id === selectedVersion)
      comparisonText = version?.content || ''
    }

    toast.info("Generating comparison...");

    try {
      const response = await api.generateDiff(originalText, comparisonText, {
        format: viewMode,
        context_lines: 3,
        ignore_whitespace: false
      })
      
      if (response.job_id) {
        setDiffJob({ job_id: response.job_id, status: 'processing' })
        
        const cleanup = api.startJobPolling(response.job_id, (job) => {
          setDiffJob(job)
          
          if (job.status === 'completed' && job.result) {
            toast.success("Comparison ready!");
            setDiffResults(job.result)
          }else if (job.status === 'failed') {
            toast.error(`Diff generation failed: ${job.error || 'Unknown error'}`);
          }
        })
      }
    } catch (error) {
      console.error('Diff generation failed:', error)
      toast.error(`Diff generation failed: ${error.message}`);
      setDiffJob({ status: 'failed', error: error.message })
    }
  }



  const renderDiffContent = () => {
    if (!diffResults) return null

    if (viewMode === 'side-by-side') {
      return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
            <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              📄 Original
            </h4>
            <div className="space-y-1 font-mono text-sm">
              {diffResults.original_lines?.map((line, index) => (
                <div key={index} className={`flex ${
                  line.type === 'removed' ? 'bg-red-900 bg-opacity-50' : 
                  line.type === 'context' ? 'bg-gray-700' : 'bg-gray-800'
                } rounded px-2 py-1`}>
                  <span className="text-gray-400 w-12 flex-shrink-0">{line.line_number}</span>
                  <span className="text-gray-200">{line.content}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
            <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              ✏️ Modified
            </h4>
            <div className="space-y-1 font-mono text-sm">
              {diffResults.modified_lines?.map((line, index) => (
                <div key={index} className={`flex ${
                  line.type === 'added' ? 'bg-green-900 bg-opacity-50' : 
                  line.type === 'context' ? 'bg-gray-700' : 'bg-gray-800'
                } rounded px-2 py-1`}>
                  <span className="text-gray-400 w-12 flex-shrink-0">{line.line_number}</span>
                  <span className="text-gray-200">{line.content}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )
    } else if (viewMode === 'unified') {
      return (
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <div className="space-y-1 font-mono text-sm">
            {diffResults.unified_diff?.map((line, index) => (
              <div key={index} className={`flex ${
                line.type === 'added' ? 'bg-green-900 bg-opacity-50' : 
                line.type === 'removed' ? 'bg-red-900 bg-opacity-50' : 
                'bg-gray-700'
              } rounded px-2 py-1`}>
                <div className="flex gap-2 w-20 flex-shrink-0 text-gray-400">
                  <span className="w-8">{line.old_line_number || ''}</span>
                  <span className="w-8">{line.new_line_number || ''}</span>
                </div>
                <span className="text-gray-300 w-4 flex-shrink-0">{line.prefix || ''}</span>
                <span className="text-gray-200">{line.content}</span>
              </div>
            ))}
          </div>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-600">
          <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            📊 Change Summary
          </h4>
          <div className="flex gap-4 text-sm">
            <span className="bg-green-900 text-green-300 px-3 py-1 rounded-full">
              +{diffResults.stats?.additions || 0} additions
            </span>
            <span className="bg-red-900 text-red-300 px-3 py-1 rounded-full">
              -{diffResults.stats?.deletions || 0} deletions
            </span>
            <span className="bg-yellow-900 text-yellow-300 px-3 py-1 rounded-full">
              ~{diffResults.stats?.modifications || 0} modifications
            </span>
          </div>
        </div>
        <div className="space-y-3">
          {diffResults.change_blocks?.map((block, index) => (
            <div key={index} className="bg-gray-800 rounded-lg border border-gray-600 overflow-hidden">
              <div className="bg-gray-700 px-4 py-2 border-b border-gray-600">
                <div className="flex justify-between items-center">
                  <span className={`px-2 py-1 rounded text-sm font-medium ${
                    block.type === 'addition' ? 'bg-green-600 text-white' :
                    block.type === 'deletion' ? 'bg-red-600 text-white' :
                    'bg-yellow-600 text-white'
                  }`}>
                    {block.type}
                  </span>
                  <span className="text-gray-300 text-sm">
                    Lines {block.start_line} - {block.end_line}
                  </span>
                </div>
              </div>
              <div className="p-4 space-y-4">
                <div>
                  <div className="text-white font-medium mb-2">Before:</div>
                  <pre className="bg-gray-900 p-3 rounded border border-gray-600 text-gray-300 text-sm overflow-x-auto">
                    {block.before_content}
                  </pre>
                </div>
                <div>
                  <div className="text-white font-medium mb-2">After:</div>
                  <pre className="bg-gray-900 p-3 rounded border border-gray-600 text-gray-300 text-sm overflow-x-auto">
                    {block.after_content}
                  </pre>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!hasRewriteHistory) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
              <span className="text-blue-400">🔄</span>
              Diff Generator
            </h2>
            <p className="text-gray-300 text-lg">Compare original and rewritten clause versions</p>
          </div>
          <div className="bg-gray-800 rounded-2xl shadow-xl p-12 text-center border border-gray-700">
            <div className="text-6xl mb-4">🔄</div>
            <h3 className="text-2xl font-semibold text-white mb-2">No Clause Rewrites Available</h3>
            <p className="text-gray-400 mb-6">Please rewrite some clauses first to generate comparisons</p>
            <button 
              onClick={() => {
                toast.info("Redirecting to Risk Analysis...");
                window.location.href = '/risk'
              }}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
            >
              Go to Risk Analysis
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span className="text-blue-400">🔄</span>
            Diff Generator
          </h2>
          <p className="text-gray-300 text-lg">Compare original and rewritten clause versions</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Controls */}
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                📋 Select Clause
              </h3>
              <select
                value={selectedClause}
                onChange={(e) => {
                  const clauseId = e.target.value;
                  setSelectedClause(clauseId);
                  
                  // Reset results when changing clause
                  setDiffResults(null);
                  setDiffJob(null);

                  if (clauseId) {
                    const clause = state.riskyClauses.find(c => 
                      c.clause_id === clauseId || c.title === clauseId
                    );
                    toast.info(`Selected: ${clause?.title || clauseId}`);
                  }
                }}
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Choose a clause to compare...</option>
                {availableClauses.map(clauseId => {
                  const clause = state.riskyClauses.find(c => 
                    c.clause_id === clauseId || c.title === clauseId
                  )
                  return (
                    <option key={clauseId} value={clauseId}>
                      {clause?.title || clauseId}
                    </option>
                  )
                })}
              </select>
            </div>

            {selectedClause && (
              <>
                <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                  <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    📊 Comparison Type
                  </h3>
                  <div className="space-y-3">
                    <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                      <input
                        type="radio"
                        value="latest"
                        checked={selectedVersion === 'latest'}
                        onChange={(e) => setSelectedVersion(e.target.value)}
                        className="mr-3 text-blue-500"
                      />
                      <span className="text-white">Latest Version vs Original</span>
                    </label>
                    <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                      <input
                        type="radio"
                        value="all"
                        checked={selectedVersion === 'all'}
                        onChange={(e) => setSelectedVersion(e.target.value)}
                        className="mr-3 text-blue-500"
                      />
                      <span className="text-white">All Versions Combined vs Original</span>
                    </label>
                    {getClauseVersions(selectedClause).map(version => (
                      <label key={version.id} className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                        <input
                          type="radio"
                          value={version.id}
                          checked={selectedVersion === version.id}
                          onChange={(e) => setSelectedVersion(e.target.value)}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-white">{version.label} vs Original</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                  <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    👁️ View Mode
                  </h3>
                  <div className="space-y-3">
                    <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                      <input
                        type="radio"
                        value="side-by-side"
                        checked={viewMode === 'side-by-side'}
                        onChange={(e) => setViewMode(e.target.value)}
                        className="mr-3 text-blue-500"
                      />
                      <span className="text-white">📱 Side by Side</span>
                    </label>
                    <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                      <input
                        type="radio"
                        value="unified"
                        checked={viewMode === 'unified'}
                        onChange={(e) => setViewMode(e.target.value)}
                        className="mr-3 text-blue-500"
                      />
                      <span className="text-white">📄 Unified View</span>
                    </label>
                    <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                      <input
                        type="radio"
                        value="split"
                        checked={viewMode === 'split'}
                        onChange={(e) => setViewMode(e.target.value)}
                        className="mr-3 text-blue-500"
                      />
                      <span className="text-white">🔄 Change Blocks</span>
                    </label>
                  </div>
                </div>

                <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                  <div className="flex gap-4">
                    <button
                      onClick={handleGenerateDiff}
                      disabled={diffJob?.status === 'processing'}
                      className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-all duration-200 ${
                        diffJob?.status === 'processing'
                          ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                          : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl'
                      }`}
                    >
                      {diffJob?.status === 'processing' ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="animate-spin w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full"></div>
                          Generating...
                        </span>
                      ) : (
                        '🔄 Generate Diff'
                      )}
                    </button>
                    

                  </div>

                  {diffJob && (
                    <div className="mt-4 bg-gray-700 rounded-lg p-4 border border-gray-600">
                      <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                        🔄 Generation Status
                      </h4>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Status:</span>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            diffJob.status === 'completed' ? 'bg-green-600 text-white' :
                            diffJob.status === 'failed' ? 'bg-red-600 text-white' :
                            'bg-yellow-600 text-white'
                          }`}>
                            {diffJob.status}
                          </span>
                        </div>
                        {diffJob.error && (
                          <div className="bg-red-900 text-red-300 p-3 rounded-lg border border-red-700">
                            Error: {diffJob.error}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Preview and Results */}
          <div className="space-y-6">
            {selectedClause && (
              <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  📄 Clause Preview
                </h3>
                <div className="space-y-4">
                  <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                    <h4 className="text-lg font-semibold text-white mb-2">Original Clause</h4>
                    <div className="bg-gray-900 p-3 rounded border border-gray-600 text-gray-300 text-sm leading-relaxed">
                      {getOriginalClause(selectedClause)}
                    </div>
                  </div>
                  
                  {selectedVersion && selectedVersion !== '' && (
                    <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                      <h4 className="text-lg font-semibold text-white mb-3">Available Versions</h4>
                      <div className="space-y-3">
                        {getClauseVersions(selectedClause).map((version, index) => (
                          <div key={version.id} className="bg-gray-800 p-3 rounded border border-gray-600">
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-white font-medium">{version.label}</span>
                              <span className="text-gray-400 text-sm">
                                {new Date(version.timestamp).toLocaleString()}
                              </span>
                            </div>
                            <div className="text-gray-300 text-sm leading-relaxed">
                              {version.content.length > 200 ? 
                                version.content.substring(0, 200) + '...' : 
                                version.content
                              }
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {diffResults && (
              <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                    📊 Diff Results
                  </h3>
                  {diffResults.stats && (
                    <div className="flex gap-4 text-sm">
                      <span className="text-gray-300">Lines changed: <span className="text-white font-medium">{diffResults.stats.total_changes || 0}</span></span>
                      <span className="text-gray-300">Similarity: <span className="text-white font-medium">{Math.round((diffResults.stats.similarity || 0) * 100)}%</span></span>
                    </div>
                  )}
                </div>
                
                <div className="bg-gray-900 rounded-lg p-4 border border-gray-600 overflow-auto">
                  {renderDiffContent()}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}