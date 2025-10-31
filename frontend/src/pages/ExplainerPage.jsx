import React, { useState, useEffect } from 'react'
import { useAppState } from '../state/StateContext'
import api from '../api'
import { toast } from 'react-toastify'

export default function ExplainerPage() {
  const { state } = useAppState()
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState({})
  const [jobs, setJobs] = useState({})

  // Reset local state when session resets
  useEffect(() => {
    setLoading(false)
    setResults({})
    setJobs({})
  }, [state.resetFlag])

  const handleJobResult = (jobType, job) => {
    setJobs(prev => ({ ...prev, [jobType]: job }))

    if (job.status === 'completed') {
      // TRIGGER 3: "see explained results"
      toast.success("Explanation ready!");
      setResults(prev => ({ ...prev, [jobType]: job.result }))
      setLoading(false)
    } else if (job.status === 'failed') {
      const errorMsg = `Explanation failed: ${job.error || 'Unknown error'}`;
      toast.error(errorMsg);
      setResults(prev => ({ ...prev, [jobType]: { error: job.error } }))
      setLoading(false)
    }
  }

  const TermExplainer = () => {
    const [term, setTerm] = useState('')
    const [context, setContext] = useState('')
    const [detectedTerms, setDetectedTerms] = useState([])

    const handleExplain = async () => {
      if (!term) return
      setLoading(true)

      // TRIGGER 2: "explaining terms"
      toast.info(`Analyzing term: "${term}"...`);

      try {
        const response = await api.explainTerm(term, context)
        if (response.job_id) {
          const cleanup = api.startJobPolling(response.job_id, (job) =>
            handleJobResult('term_explanation', job)
          )
        }
      } catch (error) {
        const errorMsg = `Request failed: ${error.message}`;
        toast.error(errorMsg);
        setResults(prev => ({ ...prev, term_explanation: { error: error.message } }))
        setLoading(false)
      }
    }

    const extractTermsFromDocument = () => {
      if (state.document && state.document.clauses) {
        const allText = state.document.clauses.map(c => c.text).join(' ')
        // Simple legal term extraction (can be enhanced)
        const legalTerms = allText.match(/\b(indemnif\w+|liability|liquidated damages|force majeure|arbitration|jurisdiction|termination|breach|warranty|guarantee|covenant|severability|waiver)\b/gi)
        if (legalTerms) {
          setDetectedTerms([...new Set(legalTerms)])
        }
      }
    }

    React.useEffect(() => {
      extractTermsFromDocument()
    }, [state.document])

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-2xl font-bold text-white mb-2 flex items-center justify-center gap-2">
            📚 Legal Term Explainer
          </h3>
          <p className="text-gray-400">Get plain-English explanations of legal terminology</p>
        </div>

        {detectedTerms.length > 0 && (
          <div className="bg-gray-700 rounded-xl p-4 border border-gray-600">
            <h4 className="text-lg font-semibold text-white mb-3">Terms found in your document:</h4>
            <div className="flex flex-wrap gap-2">
              {detectedTerms.slice(0, 10).map(detectedTerm => (
                <button
                  key={detectedTerm}
                  className="px-3 py-1 bg-purple-600 text-white rounded-full text-sm hover:bg-purple-700 transition-colors duration-200"
                  onClick={() => {
                    setTerm(detectedTerm)
                    // TRIGGER 1: "term selected"
                    toast.info(`Selected: ${detectedTerm}`);
                  }}
                >
                  {detectedTerm}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Legal Term:</label>
            <input
              type="text"
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="e.g., indemnification, force majeure, liquidated damages"
              className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Context (optional):</label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Provide context where this term appears for better explanation"
              rows={3}
              className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
          </div>
        </div>

        <button
          onClick={handleExplain}
          disabled={!term || loading}
          className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all duration-200 disabled:bg-gray-600 disabled:cursor-not-allowed"
        >
          {loading ? 'Explaining...' : '🔍 Explain Term'}
        </button>

        {jobs.term_explanation && (
          <div className="bg-blue-900 rounded-lg p-4 border border-blue-700">
            <p className="text-blue-300">Status: {jobs.term_explanation.status}</p>
            {jobs.term_explanation.progress && <p className="text-blue-400">Progress: {jobs.term_explanation.progress}%</p>}
          </div>
        )}

        {results.term_explanation && (
          <div className="bg-gray-700 rounded-xl p-6 border border-gray-600 space-y-6">
            {results.term_explanation.error ? (
              <div className="bg-red-900 text-red-300 p-4 rounded-lg border border-red-700">{results.term_explanation.error}</div>
            ) : (
              <div className="space-y-6">
                <div className="bg-gray-800 p-4 rounded-lg">
                  <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                    📖 Plain English Explanation
                  </h4>
                  <p className="text-gray-300 leading-relaxed">{results.term_explanation.plain_english}</p>
                </div>

                <div className="bg-gray-800 p-4 rounded-lg">
                  <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                    ⚖️ Legal Definition
                  </h4>
                  <p className="text-gray-300 leading-relaxed">{results.term_explanation.legal_definition}</p>
                </div>

                <div className="bg-gray-800 p-4 rounded-lg">
                  <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                    🎯 Real-World Impact
                  </h4>
                  <p className="text-gray-300 leading-relaxed">{results.term_explanation.real_world_impact}</p>
                </div>

                {results.term_explanation.risk_level && (
                  <div className="flex justify-center">
                    <span className={`px-4 py-2 rounded-full text-sm font-medium ${results.term_explanation.risk_level.toLowerCase() === 'high' ? 'bg-red-600 text-white' :
                        results.term_explanation.risk_level.toLowerCase() === 'medium' ? 'bg-yellow-600 text-white' :
                          'bg-green-600 text-white'
                      }`}>
                      Risk Level: {results.term_explanation.risk_level}
                    </span>
                  </div>
                )}

                {results.term_explanation.alternatives && results.term_explanation.alternatives.length > 0 && (
                  <div className="bg-gray-800 p-4 rounded-lg">
                    <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                      🔄 Alternative Terms
                    </h4>
                    <ul className="text-gray-300 space-y-1 list-disc list-inside">
                      {results.term_explanation.alternatives.map((alt, i) => (
                        <li key={i}>{alt}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-purple-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
            <span className="text-purple-400">📚</span>
            Legal Term Explainer
          </h1>
          <p className="text-gray-300 text-lg">AI-Powered Legal Term Explanation & Definition</p>
        </div>

        {/* Term Explainer Content */}
        <div className="bg-gray-800 rounded-2xl shadow-lg border border-gray-700 min-h-[60vh] p-6">
          <TermExplainer />
        </div>
      </div>
    </div>
  )
}