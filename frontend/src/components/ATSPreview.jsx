import React from 'react'

const ATSPreview = ({ atsResume, isLoading }) => {
  if (isLoading) {
    return (
      <div className="w-full flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-600">Generating ATS-optimized resume...</p>
        </div>
      </div>
    )
  }

  if (!atsResume) {
    return null
  }

  return (
    <div className="w-full">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">
            ATS Optimized Resume
          </h3>
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
            ATS-Friendly Format
          </span>
        </div>
        
        <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
          <div className="bg-white rounded p-6 max-h-96 overflow-y-auto text-sm leading-relaxed whitespace-pre-wrap">
            <div className="font-mono text-xs">
              {atsResume.split('\n').map((line, index) => {
                const sectionHeaders = ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 'CERTIFICATIONS', 'PROFESSIONAL SUMMARY']
                const isSectionHeader = line === line.toUpperCase() && 
                                       line.length > 3 && 
                                       line.length < 50 && 
                                       !line.includes('•') && 
                                       !line.startsWith('-') && 
                                       !line.startsWith('=') &&
                                       sectionHeaders.some(h => line.includes(h))
                
                // Format section headers (uppercase, no bullets)
                if (isSectionHeader) {
                  return <h4 key={index} className="font-bold text-gray-900 mt-6 mb-3 text-sm uppercase tracking-wide">{line}</h4>
                }
                
                // Format section separators
                if (line.startsWith('-') && line.length > 20) {
                  return <div key={index} className="border-t border-gray-300 my-2"></div>
                }
                
                // Format bullet points (indented)
                if (line.trim().startsWith('•')) {
                  const indentMatch = line.match(/^(\s*)/)
                  const indent = indentMatch ? indentMatch[1].length : 0
                  const indentClass = indent > 4 ? 'ml-8' : 'ml-4'
                  return <div key={index} className={`${indentClass} mb-1 text-gray-700`}>{line.trim()}</div>
                }
                
                // Format company/title lines (with right-aligned dates)
                if (line.includes('  ') && line.length > 30 && !line.trim().startsWith('•')) {
                  const parts = line.split(/\s{2,}/)
                  if (parts.length >= 2) {
                    return (
                      <div key={index} className="flex justify-between mb-1 text-gray-800">
                        <span className="font-semibold">{parts[0]}</span>
                        <span className="text-gray-600 text-xs">{parts.slice(1).join(' ')}</span>
                      </div>
                    )
                  }
                }
                
                // Regular text
                return <div key={index} className="text-gray-700 mb-1">{line || '\u00A0'}</div>
              })}
            </div>
          </div>
        </div>
        
        <p className="mt-4 text-xs text-gray-500">
          This resume has been optimized for Applicant Tracking Systems (ATS) with:
          single-column layout, standard headings, keyword optimization, and clean formatting.
        </p>
      </div>
    </div>
  )
}

export default ATSPreview


