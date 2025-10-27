import React from 'react'
import { useAppState } from '../state/StateContext'

export default function RiskPage() {
  const { state } = useAppState()

  const getRiskLevel = (score) => {
    if (score >= 4) return { level: 'High', color: 'red', bgColor: 'red-50', borderColor: 'red-200' }
    if (score >= 3) return { level: 'Medium', color: 'yellow', bgColor: 'yellow-50', borderColor: 'yellow-200' }
    return { level: 'Low', color: 'green', bgColor: 'green-50', borderColor: 'green-200' }
  }

  const getRiskIcon = (score) => {
    if (score >= 4) return '🚨'
    if (score >= 3) return '⚠️'
    return '✅'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-red-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span className="text-red-400">⚠️</span>
            Risk Analysis
          </h1>
          <p className="text-gray-300">AI-powered contract risk assessment</p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 font-medium">Total Risks</p>
                <p className="text-3xl font-bold text-white">{state.riskyClauses?.length || 0}</p>
              </div>
              <div className="p-3 bg-red-600 rounded-full">
                <span className="text-2xl">📊</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-400 font-medium">High Risk</p>
                <p className="text-3xl font-bold text-red-400">
                  {state.riskyClauses?.filter(c => c.risk_analysis?.score >= 4).length || 0}
                </p>
              </div>
              <div className="p-3 bg-red-600 rounded-full">
                <span className="text-2xl">🚨</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-yellow-400 font-medium">Medium Risk</p>
                <p className="text-3xl font-bold text-yellow-400">
                  {state.riskyClauses?.filter(c => c.risk_analysis?.score === 3).length || 0}
                </p>
              </div>
              <div className="p-3 bg-yellow-600 rounded-full">
                <span className="text-2xl">⚠️</span>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-400 font-medium">Low Risk</p>
                <p className="text-3xl font-bold text-green-400">
                  {state.riskyClauses?.filter(c => c.risk_analysis?.score < 3).length || 0}
                </p>
              </div>
              <div className="p-3 bg-green-600 rounded-full">
                <span className="text-2xl">✅</span>
              </div>
            </div>
          </div>
        </div>

        {/* No Document State */}
        {!state.document && (
          <div className="bg-gray-800 rounded-2xl shadow-xl p-12 text-center border border-gray-700">
            <div className="text-6xl mb-4">📄</div>
            <h3 className="text-2xl font-semibold text-white mb-2">No Document Uploaded</h3>
            <p className="text-gray-400 mb-6">Please upload a document first to see risk analysis results</p>
            <button 
              onClick={() => window.location.href = '/upload'}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
            >
              Go to Upload Page
            </button>
          </div>
        )}

        {/* Risk Analysis Results */}
        {state.riskyClauses && state.riskyClauses.length > 0 && (
          <div className="space-y-6">
            {state.riskyClauses.map((clause, i) => {
              const riskInfo = getRiskLevel(clause.risk_analysis?.score || 0)
              return (
                <div key={i} className={`bg-gray-800 rounded-2xl shadow-lg border border-gray-700 overflow-hidden`}>
                  {/* Clause Header */}
                  <div className={`bg-gray-900 px-6 py-4 border-b border-gray-700`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{getRiskIcon(clause.risk_analysis?.score || 0)}</span>
                        <div>
                          <h3 className="font-semibold text-white">
                            Clause {i + 1}: {clause.title || 'Untitled Clause'}
                          </h3>
                          <p className="text-sm text-gray-400">
                            {clause.text?.substring(0, 100)}{clause.text?.length > 100 ? '...' : ''}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`px-4 py-2 rounded-full ${
                          riskInfo.color === 'red' ? 'bg-red-600 text-white' :
                          riskInfo.color === 'yellow' ? 'bg-yellow-600 text-white' :
                          'bg-green-600 text-white'
                        } font-semibold text-sm`}>
                          {riskInfo.level} Risk
                        </div>
                        <div className="text-sm text-gray-400 mt-1">
                          Score: {clause.risk_analysis?.score || 0}/5
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Clause Content */}
                  <div className="p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Clause Text */}
                      <div>
                        <h4 className="font-semibold text-white mb-3">Clause Text</h4>
                        <div className="bg-gray-900 p-4 rounded-lg border border-gray-600 max-h-48 overflow-y-auto">
                          <p className="text-sm text-gray-300 leading-relaxed">
                            {clause.text || 'No clause text available'}
                          </p>
                        </div>
                      </div>

                      {/* Risk Analysis */}
                      <div>
                        <h4 className="font-semibold text-white mb-3">Risk Analysis</h4>
                        <div className="space-y-4">
                          {/* Risk Tags */}
                          {clause.risk_analysis?.tags && clause.risk_analysis.tags.length > 0 && (
                            <div>
                              <p className="text-sm font-medium text-gray-400 mb-2">Risk Categories:</p>
                              <div className="flex flex-wrap gap-2">
                                {clause.risk_analysis.tags.map((tag, tagIndex) => (
                                  <span 
                                    key={tagIndex}
                                    className="px-3 py-1 bg-red-600 text-white text-xs font-medium rounded-full"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Risk Description */}
                          {clause.risk_analysis?.explanation && (
                            <div>
                              <p className="text-sm font-medium text-gray-400 mb-2">Risk Explanation:</p>
                              <div className="bg-red-900 p-3 rounded-lg border border-red-700">
                                <p className="text-sm text-gray-300">
                                  {clause.risk_analysis.explanation}
                                </p>
                              </div>
                            </div>
                          )}

                          {/* Recommendations */}
                          {clause.risk_analysis?.recommendations && (
                            <div>
                              <p className="text-sm font-medium text-gray-400 mb-2">Recommendations:</p>
                              <div className="bg-blue-900 p-3 rounded-lg border border-blue-700">
                                <p className="text-sm text-gray-300">
                                  {clause.risk_analysis.recommendations}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Empty State for Document with No Risks */}
        {state.document && state.riskyClauses && state.riskyClauses.length === 0 && (
          <div className="bg-gray-800 rounded-2xl shadow-xl p-12 text-center border border-gray-700">
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-2xl font-semibold text-white mb-2">Great News!</h3>
            <p className="text-gray-400 mb-6">No risky clauses detected in your document</p>
            <div className="text-green-400 text-sm">
              Your document appears to have standard, low-risk language.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
