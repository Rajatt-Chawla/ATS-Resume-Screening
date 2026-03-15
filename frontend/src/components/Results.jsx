import React from 'react'

const Results = ({ results, isLoading }) => {
  if (isLoading) {
    return (
      <div className="w-full flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-600">Analyzing your resume and job description...</p>
        </div>
      </div>
    )
  }

  if (!results) {
    return null
  }

  const { match_score, missing_keywords, skill_gap_analysis, resume_suggestions, tailored_summary } = results

  // Determine score color
  const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-600'
    if (score >= 50) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBgColor = (score) => {
    if (score >= 70) return 'bg-green-100'
    if (score >= 50) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  // Calculate circle stroke for match score
  const circumference = 2 * Math.PI * 90 // radius = 90
  const strokeDashoffset = circumference - (match_score / 100) * circumference

  return (
    <div className="w-full space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Analysis Results</h2>

      {/* Match Score */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Match Score</h3>
        <div className="flex items-center justify-center space-x-8">
          <div className="relative w-48 h-48">
            <svg className="transform -rotate-90 w-48 h-48">
              <circle
                cx="96"
                cy="96"
                r="90"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                className="text-gray-200"
              />
              <circle
                cx="96"
                cy="96"
                r="90"
                stroke="currentColor"
                strokeWidth="12"
                fill="none"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className={`${getScoreColor(match_score)} transition-all duration-500`}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className={`text-4xl font-bold ${getScoreColor(match_score)}`}>
                  {match_score}%
                </div>
                <div className="text-sm text-gray-500 mt-1">Match</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Missing Keywords */}
      {missing_keywords && missing_keywords.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Missing Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {missing_keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium"
              >
                {keyword}
              </span>
            ))}
          </div>
          <p className="mt-4 text-sm text-gray-600">
            Consider adding these keywords to your resume to improve your match score.
          </p>
        </div>
      )}

      {/* Skill Gap Analysis */}
      {skill_gap_analysis && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Skill Gap Analysis</h3>
          <p className="text-gray-700 whitespace-pre-line">{skill_gap_analysis}</p>
        </div>
      )}

      {/* Resume Suggestions */}
      {resume_suggestions && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Resume Improvement Suggestions</h3>
          <div className="text-gray-700 whitespace-pre-line">
            {resume_suggestions}
          </div>
        </div>
      )}

      {/* Tailored Summary */}
      {tailored_summary && (
        <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg shadow-md p-6 border-l-4 border-primary-500">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Tailored Professional Summary</h3>
          <p className="text-gray-700 whitespace-pre-line leading-relaxed">{tailored_summary}</p>
        </div>
      )}

      {/* Generate ATS Resume Button */}
      {results && (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg shadow-md p-6 border-l-4 border-green-500">
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Ready to Optimize Your Resume?</h3>
          <p className="text-sm text-gray-600 mb-4">
            Generate a 100% ATS-friendly version of your resume with keyword optimization and proper formatting.
          </p>
          <button
            onClick={() => {
              // This will be handled by parent component
              if (window.generateATSResume) {
                window.generateATSResume()
              }
            }}
            className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 transition-colors shadow-md"
          >
            Generate 100% ATS Friendly Resume
          </button>
        </div>
      )}
    </div>
  )
}

export default Results

