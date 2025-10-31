import React, { useState, useEffect } from 'react'
import { useAppState } from '../state/StateContext'
import api from '../api'

export default function PrivacyPage() {
  const { state } = useAppState()
  const [selectedInfoTypes, setSelectedInfoTypes] = useState([
    'PERSON_NAME',
    'EMAIL_ADDRESS',
    'PHONE_NUMBER',
    'CREDIT_CARD_NUMBER',
    'US_SOCIAL_SECURITY_NUMBER',
    'DATE_OF_BIRTH'
  ])
  const [redactionLevel, setRedactionLevel] = useState('PARTIAL_MASKING')
  const [privacyJob, setPrivacyJob] = useState(null)
  const [privacyResults, setPrivacyResults] = useState(null)
  const [activeTab, setActiveTab] = useState('scan')

  // Reset page state when session resets
  useEffect(() => {
    setSelectedInfoTypes([
      'PERSON_NAME',
      'EMAIL_ADDRESS',
      'PHONE_NUMBER',
      'CREDIT_CARD_NUMBER',
      'US_SOCIAL_SECURITY_NUMBER',
      'DATE_OF_BIRTH'
    ])
    setRedactionLevel('PARTIAL_MASKING')
    setPrivacyJob(null)
    setPrivacyResults(null)
    setActiveTab('scan')
  }, [state.resetFlag])

  const availableInfoTypes = [
    { id: 'PERSON_NAME', label: 'Person Names', icon: '👤' },
    { id: 'EMAIL_ADDRESS', label: 'Email Addresses', icon: '📧' },
    { id: 'PHONE_NUMBER', label: 'Phone Numbers', icon: '📱' },
    { id: 'CREDIT_CARD_NUMBER', label: 'Credit Card Numbers', icon: '💳' },
    { id: 'US_SOCIAL_SECURITY_NUMBER', label: 'Social Security Numbers', icon: '🆔' },
    { id: 'DATE_OF_BIRTH', label: 'Birth Dates', icon: '📅' },
    { id: 'US_PASSPORT', label: 'Passport Numbers', icon: '📔' },
    { id: 'US_DRIVERS_LICENSE_NUMBER', label: 'Driver License Numbers', icon: '🚗' },
    { id: 'GENERIC_ID', label: 'Generic IDs', icon: '🏷️' },
    { id: 'IP_ADDRESS', label: 'IP Addresses', icon: '🌐' },
    { id: 'MAC_ADDRESS', label: 'MAC Addresses', icon: '💻' },
    { id: 'IBAN_CODE', label: 'IBAN Codes', icon: '🏦' }
  ]

  const redactionOptions = [
    { id: 'PARTIAL_MASKING', label: 'Partial Masking', description: 'Show first/last characters with asterisks' },
    { id: 'FULL_MASKING', label: 'Full Masking', description: 'Replace with asterisks or placeholder text' },
    { id: 'REDACTION', label: 'Complete Redaction', description: 'Remove sensitive information entirely' },
    { id: 'REPLACEMENT', label: 'Fake Data Replacement', description: 'Replace with realistic but fake data' }
  ]

  const hasDocument = state.document !== null

  const handlePrivacyScan = async () => {
    if (!hasDocument) return

    try {
      const response = await api.processPrivacy(
        state.document.content,
        selectedInfoTypes,
        redactionLevel
      )
      
      if (response.job_id) {
        setPrivacyJob({ job_id: response.job_id, status: 'processing' })
        
        const cleanup = api.startJobPolling(response.job_id, (job) => {
          setPrivacyJob(job)
          
          if (job.status === 'completed' && job.result) {
            setPrivacyResults(job.result)
            setActiveTab('results')
          }
        })
      }
    } catch (error) {
      console.error('Privacy scanning failed:', error)
      setPrivacyJob({ status: 'failed', error: error.message })
    }
  }

  const downloadRedactedDocument = () => {
    if (!privacyResults?.redacted_content) return

    const blob = new Blob([privacyResults.redacted_content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `redacted_${state.document.filename || 'document.txt'}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadPrivacyReport = () => {
    if (!privacyResults) return

    const report = {
      scan_date: new Date().toISOString(),
      document_name: state.document.filename || 'Legal Document',
      info_types_scanned: selectedInfoTypes,
      redaction_level: redactionLevel,
      findings: privacyResults.findings || [],
      summary: {
        total_findings: privacyResults.findings?.length || 0,
        info_types_found: [...new Set(privacyResults.findings?.map(f => f.info_type) || [])],
        confidence_scores: privacyResults.findings?.map(f => f.confidence) || []
      }
    }

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'privacy_scan_report.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!hasDocument) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-blue-900 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-bold text-white mb-2 flex items-center justify-center gap-3">
              <span className="text-blue-400">🔒</span>
              Privacy & Security
            </h2>
            <p className="text-gray-300 text-lg">Detect and redact sensitive information</p>
          </div>
          <div className="bg-gray-800 rounded-2xl shadow-xl p-12 text-center border border-gray-700">
            <div className="text-6xl mb-4">📄</div>
            <h3 className="text-2xl font-semibold text-white mb-2">No Document Uploaded</h3>
            <p className="text-gray-400 mb-6">Please upload a document first to scan for sensitive information</p>
            <button 
              onClick={() => window.location.href = '/'}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all duration-200"
            >
              Go to Upload Page
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
            <span className="text-blue-400">🔒</span>
            Privacy & Security
          </h2>
          <p className="text-gray-300 text-lg">Detect and redact sensitive information using Google Cloud DLP</p>
        </div>

        <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700 mb-6">
          <div className="flex space-x-1 bg-gray-700 p-1 rounded-lg">
            <button 
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                activeTab === 'scan' 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : 'text-gray-300 hover:text-white hover:bg-gray-600'
              }`}
              onClick={() => setActiveTab('scan')}
            >
              🔍 Privacy Scanner
            </button>
            <button 
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                activeTab === 'results' 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : privacyResults ? 'text-gray-300 hover:text-white hover:bg-gray-600' : 'text-gray-500 cursor-not-allowed'
              }`}
              onClick={() => setActiveTab('results')}
              disabled={!privacyResults}
            >
              📋 Scan Results
            </button>
            <button 
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                activeTab === 'guidelines' 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : 'text-gray-300 hover:text-white hover:bg-gray-600'
              }`}
              onClick={() => setActiveTab('guidelines')}
            >
              📚 Privacy Guidelines
            </button>
          </div>
        </div>

        <div className="space-y-6">
          {activeTab === 'scan' && (
            <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    🎯 Information Types to Detect
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {availableInfoTypes.map(type => (
                      <label key={type.id} className="flex items-center p-3 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedInfoTypes.includes(type.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedInfoTypes(prev => [...prev, type.id])
                            } else {
                              setSelectedInfoTypes(prev => prev.filter(id => id !== type.id))
                            }
                          }}
                          className="mr-3 text-blue-500"
                        />
                        <span className="text-2xl mr-2">{type.icon}</span>
                        <span className="text-white text-sm font-medium">{type.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    🛡️ Redaction Level
                  </h3>
                  <div className="space-y-3">
                    {redactionOptions.map(option => (
                      <label key={option.id} className="flex items-start p-4 bg-gray-700 rounded-lg border border-gray-600 hover:bg-gray-600 transition-colors cursor-pointer">
                        <input
                          type="radio"
                          value={option.id}
                          checked={redactionLevel === option.id}
                          onChange={(e) => setRedactionLevel(e.target.value)}
                          className="mt-1 mr-3 text-blue-500"
                        />
                        <div>
                          <div className="text-white font-medium">{option.label}</div>
                          <div className="text-gray-300 text-sm mt-1">{option.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={handlePrivacyScan}
                    disabled={privacyJob?.status === 'processing' || selectedInfoTypes.length === 0}
                    className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-all duration-200 ${
                      privacyJob?.status === 'processing' || selectedInfoTypes.length === 0
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl'
                    }`}
                  >
                    {privacyJob?.status === 'processing' ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="animate-spin w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full"></div>
                        Scanning...
                      </span>
                    ) : (
                      '🔍 Start Privacy Scan'
                    )}
                  </button>
                </div>

                {privacyJob && (
                  <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                    <h4 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                      🔄 Scan Status
                    </h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-300">Status:</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                          privacyJob.status === 'completed' ? 'bg-green-600 text-white' :
                          privacyJob.status === 'failed' ? 'bg-red-600 text-white' :
                          'bg-yellow-600 text-white'
                        }`}>
                          {privacyJob.status}
                        </span>
                      </div>
                      {privacyJob.progress && (
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Progress:</span>
                          <span className="text-white">{privacyJob.progress}%</span>
                        </div>
                      )}
                      {privacyJob.error && (
                        <div className="bg-red-900 text-red-300 p-3 rounded-lg border border-red-700">
                          Error: {privacyJob.error}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'results' && privacyResults && (
            <div className="space-y-6">
              <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  📊 Scan Summary
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-blue-900 p-4 rounded-lg border border-blue-700 text-center">
                    <div className="text-2xl font-bold text-blue-400">{privacyResults.findings?.length || 0}</div>
                    <div className="text-sm text-blue-300 font-medium">Sensitive Items Found</div>
                  </div>
                  <div className="bg-purple-900 p-4 rounded-lg border border-purple-700 text-center">
                    <div className="text-2xl font-bold text-purple-400">
                      {[...new Set(privacyResults.findings?.map(f => f.info_type) || [])].length}
                    </div>
                    <div className="text-sm text-purple-300 font-medium">Info Types Detected</div>
                  </div>
                  <div className="bg-green-900 p-4 rounded-lg border border-green-700 text-center">
                    <div className="text-2xl font-bold text-green-400">
                      {privacyResults.findings?.filter(f => f.confidence > 0.8).length || 0}
                    </div>
                    <div className="text-sm text-green-300 font-medium">High Confidence</div>
                  </div>
                </div>

                <div className="flex gap-4">
                  <button 
                    onClick={downloadRedactedDocument} 
                    className="bg-gradient-to-r from-green-600 to-teal-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-green-700 hover:to-teal-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    📥 Download Redacted Document
                  </button>
                  <button 
                    onClick={downloadPrivacyReport} 
                    className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    📊 Download Privacy Report
                  </button>
                </div>
              </div>

              <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  🔍 Detailed Findings
                </h3>
                {privacyResults.findings?.length > 0 ? (
                  <div className="space-y-4">
                    {privacyResults.findings.map((finding, index) => (
                      <div key={index} className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex items-center gap-2">
                            <span className="text-2xl">
                              {availableInfoTypes.find(t => t.id === finding.info_type)?.icon || '🏷️'}
                            </span>
                            <span className="text-white font-medium">
                              {finding.info_type.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            finding.confidence > 0.8 ? 'bg-green-600 text-white' : 
                            finding.confidence > 0.5 ? 'bg-yellow-600 text-white' : 'bg-red-600 text-white'
                          }`}>
                            {Math.round(finding.confidence * 100)}% confidence
                          </span>
                        </div>
                        <div className="space-y-2">
                          <div className="bg-gray-800 p-3 rounded border border-gray-600">
                            <strong className="text-gray-300">Original:</strong>
                            <code className="block text-white mt-1">{finding.quote}</code>
                          </div>
                          <div className="bg-gray-800 p-3 rounded border border-gray-600">
                            <strong className="text-gray-300">Redacted:</strong>
                            <code className="block text-white mt-1">{finding.redacted_value || '[REDACTED]'}</code>
                          </div>
                          <div className="text-sm text-gray-400">
                            Location: Character {finding.start_offset} to {finding.end_offset}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-green-900 text-green-300 p-4 rounded-lg border border-green-700 text-center">
                    ✅ No sensitive information detected with the current settings.
                  </div>
                )}
              </div>

              {privacyResults.redacted_content && (
                <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
                  <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    📄 Redacted Document Preview
                  </h3>
                  <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
                    <textarea
                      readOnly
                      value={privacyResults.redacted_content}
                      className="w-full h-96 bg-transparent text-white resize-none outline-none font-mono text-sm"
                      placeholder="Redacted content will appear here..."
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'guidelines' && (
            <div className="bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-700">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                🏛️ Legal Privacy Requirements
              </h3>
              
              <div className="space-y-6">
                <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                  <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                    📋 GDPR Compliance
                  </h4>
                  <ul className="space-y-2 text-gray-300">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Personal data must be processed lawfully, fairly, and transparently</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Data processing should be limited to what is necessary</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Personal data must be accurate and kept up to date</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Storage should be limited to what is necessary</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Appropriate security measures must be implemented</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                  <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                    🇺🇸 CCPA Requirements
                  </h4>
                  <ul className="space-y-2 text-gray-300">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Consumers have the right to know what personal information is collected</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Consumers have the right to delete personal information</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Consumers have the right to opt-out of the sale of personal information</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Consumers have the right to non-discrimination for exercising their privacy rights</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                  <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                    🏥 HIPAA Compliance
                  </h4>
                  <ul className="space-y-2 text-gray-300">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Protected Health Information (PHI) must be safeguarded</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Minimum necessary standard should be applied</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Administrative, physical, and technical safeguards required</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Business associate agreements needed for third-party access</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                  <h4 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                    💳 PCI DSS Standards
                  </h4>
                  <ul className="space-y-2 text-gray-300">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Install and maintain firewalls to protect cardholder data</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Do not use vendor-supplied defaults for system passwords</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Protect stored cardholder data</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Encrypt transmission of cardholder data across open networks</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-1">•</span>
                      <span>Regularly test security systems and processes</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-gray-700 rounded-lg p-4 border border-gray-600">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    ✅ Best Practices for Legal Documents
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="bg-gray-800 p-4 rounded-lg border border-gray-600">
                      <div className="text-xl mb-2">🔍</div>
                      <div className="font-semibold text-white mb-2">Regular Scanning</div>
                      <div className="text-sm text-gray-300">Scan all documents for PII before sharing or storing</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg border border-gray-600">
                      <div className="text-xl mb-2">🛡️</div>
                      <div className="font-semibold text-white mb-2">Appropriate Redaction</div>
                      <div className="text-sm text-gray-300">Use the minimum redaction necessary for your use case</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg border border-gray-600">
                      <div className="text-xl mb-2">📚</div>
                      <div className="font-semibold text-white mb-2">Documentation</div>
                      <div className="text-sm text-gray-300">Keep records of what was redacted and why</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg border border-gray-600">
                      <div className="text-xl mb-2">👥</div>
                      <div className="font-semibold text-white mb-2">Access Control</div>
                      <div className="text-sm text-gray-300">Limit access to sensitive documents to authorized personnel only</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg border border-gray-600">
                      <div className="text-xl mb-2">🔄</div>
                      <div className="font-semibold text-white mb-2">Regular Updates</div>
                      <div className="text-sm text-gray-300">Update privacy scanning as regulations change</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-lg border border-gray-600">
                      <div className="text-xl mb-2">⚖️</div>
                      <div className="font-semibold text-white mb-2">Legal Review</div>
                      <div className="text-sm text-gray-300">Have privacy procedures reviewed by legal counsel</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}