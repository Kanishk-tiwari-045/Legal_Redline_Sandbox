import React, { useState, useEffect } from 'react'
import { useAppState } from '../state/StateContext'
import api from '../api'

export default function ExportPage() {
  const { state } = useAppState()
  const [exportFormat, setExportFormat] = useState('html')
  const [exportOptions, setExportOptions] = useState({
    includeOriginal: true,
    includeRationale: true,
    includeDiff: true,
    includeRiskAnalysis: true,
    includeMetadata: true
  })
  const [exportJob, setExportJob] = useState(null)
  const [exportResult, setExportResult] = useState(null)
  const [previewContent, setPreviewContent] = useState('')

  // Reset local state when session resets
  useEffect(() => {
    setExportFormat('html')
    setExportOptions({
      includeOriginal: true,
      includeRationale: true,
      includeDiff: true,
      includeRiskAnalysis: true,
      includeMetadata: true
    })
    setExportJob(null)
    setExportResult(null)
    setPreviewContent('')
  }, [state.resetFlag])

  const hasRewriteHistory = Object.keys(state.rewriteHistory).length > 0
  const hasRiskyClauses = state.riskyClauses && state.riskyClauses.length > 0
  const hasDocument = state.document !== null

  const handleExport = async () => {
    if (!hasDocument) return

    const reportData = {
      document: state.document,
      risky_clauses: state.riskyClauses || [],
      rewrite_history: state.rewriteHistory || {},
      user_info: {
        export_date: new Date().toISOString(),
        document_name: state.document.filename || 'Legal Document',
        total_clauses: state.document.clauses?.length || 0,
        risky_clauses_count: state.riskyClauses?.length || 0,
        rewrites_count: Object.keys(state.rewriteHistory).length
      }
    }

    try {
      const response = await api.exportReport(reportData, exportFormat, exportOptions)
      
      if (response.job_id) {
        setExportJob({ job_id: response.job_id, status: 'processing' })
        
        const cleanup = api.startJobPolling(response.job_id, (job) => {
          setExportJob(job)
          
          if (job.status === 'completed' && job.result) {
            setExportResult(job.result)
            if (job.result.format === 'html') {
              setPreviewContent(job.result.content)
            }
          }
        })
      }
    } catch (error) {
      console.error('Export failed:', error)
      setExportJob({ status: 'failed', error: error.message })
    }
  }

  const downloadReport = () => {
    if (!exportResult) return

    if (exportResult.format === 'html') {
      const blob = new Blob([exportResult.content], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'legal_redline_report.html'
      a.click()
      URL.revokeObjectURL(url)
    } else if (exportResult.format === 'pdf') {
      const byteCharacters = atob(exportResult.content)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'legal_redline_report.pdf'
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span className="text-blue-400">📊</span>
            Export Report
          </h2>
          <p className="text-gray-300 text-lg">Generate comprehensive analysis reports</p>
        </div>

        {!hasDocument ? (
          <div className="bg-gray-800 rounded-2xl shadow-xl p-12 text-center border border-gray-700">
            <div className="text-6xl mb-4">📄</div>
            <h3 className="text-2xl font-semibold text-white mb-2">No Document Uploaded</h3>
            <p className="text-gray-400 mb-6">Please upload and analyze a document first to generate reports</p>
            <button 
              onClick={() => window.location.href = '/'}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
            >
              Go to Upload Page
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  📋 Report Summary
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-900 p-4 rounded-lg border border-blue-700 text-center">
                    <div className="text-sm text-blue-300 font-medium">Total Clauses</div>
                    <div className="text-2xl font-bold text-blue-400">{state.document.clauses?.length || 0}</div>
                  </div>
                  <div className="bg-red-900 p-4 rounded-lg border border-red-700 text-center">
                    <div className="text-sm text-red-300 font-medium">Risky Clauses</div>
                    <div className="text-2xl font-bold text-red-400">{state.riskyClauses?.length || 0}</div>
                  </div>
                  <div className="bg-green-900 p-4 rounded-lg border border-green-700 text-center">
                    <div className="text-sm text-green-300 font-medium">Rewrites</div>
                    <div className="text-2xl font-bold text-green-400">{Object.keys(state.rewriteHistory).length}</div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  ⚙️ Export Settings
                </h3>
                
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">Export Format:</label>
                    <div className="space-y-2">
                      <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                        <input
                          type="radio"
                          value="html"
                          checked={exportFormat === 'html'}
                          onChange={(e) => setExportFormat(e.target.value)}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-white">📄 HTML Report (Interactive)</span>
                      </label>
                      <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                        <input
                          type="radio"
                          value="pdf"
                          checked={exportFormat === 'pdf'}
                          onChange={(e) => setExportFormat(e.target.value)}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-white">📕 PDF Report (Printable)</span>
                      </label>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-3">Include in Report:</label>
                    <div className="space-y-2">
                      <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                        <input
                          type="checkbox"
                          checked={exportOptions.includeOriginal}
                          onChange={(e) => setExportOptions(prev => ({
                            ...prev, includeOriginal: e.target.checked
                          }))}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-white">Original Clauses</span>
                      </label>
                      <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                        <input
                          type="checkbox"
                          checked={exportOptions.includeRiskAnalysis}
                          onChange={(e) => setExportOptions(prev => ({
                            ...prev, includeRiskAnalysis: e.target.checked
                          }))}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-white">Risk Analysis</span>
                      </label>
                      <label className={`flex items-center p-3 rounded-lg border transition-colors cursor-pointer ${
                        hasRewriteHistory 
                          ? 'bg-gray-700 border-gray-600 hover:bg-gray-600' 
                          : 'bg-gray-800 border-gray-700 cursor-not-allowed opacity-50'
                      }`}>
                        <input
                          type="checkbox"
                          checked={exportOptions.includeRationale}
                          onChange={(e) => setExportOptions(prev => ({
                            ...prev, includeRationale: e.target.checked
                          }))}
                          disabled={!hasRewriteHistory}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-white">
                          AI Rationale {!hasRewriteHistory && '(No rewrites available)'}
                        </span>
                      </label>
                      <label className={`flex items-center p-3 rounded-lg border transition-colors cursor-pointer ${
                        hasRewriteHistory 
                          ? 'bg-gray-700 border-gray-600 hover:bg-gray-600' 
                          : 'bg-gray-800 border-gray-700 cursor-not-allowed opacity-50'
                      }`}>
                        <input
                          type="checkbox"
                          checked={exportOptions.includeDiff}
                          onChange={(e) => setExportOptions(prev => ({
                            ...prev, includeDiff: e.target.checked
                          }))}
                          disabled={!hasRewriteHistory}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-white">
                          Before/After Comparison {!hasRewriteHistory && '(No rewrites available)'}
                        </span>
                      </label>
                      <label className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                        <input
                          type="checkbox"
                          checked={exportOptions.includeMetadata}
                          onChange={(e) => setExportOptions(prev => ({
                            ...prev, includeMetadata: e.target.checked
                          }))}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-white">Document Metadata</span>
                      </label>
                    </div>
                  </div>

                  <button
                    onClick={handleExport}
                    disabled={exportJob?.status === 'processing'}
                    className={`w-full py-3 px-6 rounded-lg font-semibold transition-all duration-200 ${
                      exportJob?.status === 'processing'
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl'
                    }`}
                  >
                    {exportJob?.status === 'processing' ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="animate-spin w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full"></div>
                        Generating Report...
                      </span>
                    ) : (
                      '�� Generate Report'
                    )}
                  </button>

                  {exportResult && (
                    <button
                      onClick={downloadReport}
                      className="w-full bg-gradient-to-r from-green-600 to-teal-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-green-700 hover:to-teal-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                    >
                      💾 Download Report
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              {exportJob && (
                <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                  <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    🔄 Export Status
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300">Status:</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        exportJob.status === 'completed' ? 'bg-green-600 text-white' :
                        exportJob.status === 'failed' ? 'bg-red-600 text-white' :
                        'bg-yellow-600 text-white'
                      }`}>
                        {exportJob.status}
                      </span>
                    </div>
                    {exportJob.error && (
                      <div className="bg-red-900 text-red-300 p-3 rounded-lg border border-red-700">
                        Error: {exportJob.error}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {previewContent && (
                <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                  <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    👁️ Report Preview
                  </h3>
                  <div 
                    className="bg-white p-4 rounded-lg max-h-96 overflow-y-auto text-black"
                    dangerouslySetInnerHTML={{ __html: previewContent }}
                  />
                </div>
              )}

              <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  💡 Export Tips
                </h3>
                <ul className="space-y-2 text-sm text-gray-300">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span>HTML reports are interactive and include all analysis details</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span>PDF reports are print-friendly and suitable for sharing</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span>Include rewrite history for comprehensive before/after analysis</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span>Risk analysis helps identify problematic clauses</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
