import React, { useState } from 'react'
import UploadResume from './components/UploadResume'
import JobDescription from './components/JobDescription'
import Results from './components/Results'
import ATSPreview from './components/ATSPreview'
import DownloadButton from './components/DownloadButton'

// Sample data for demo mode
const SAMPLE_RESUME_FILE = new File(
  ['Sample Resume Content - Software Engineer with 5 years experience in React, Node.js, Python'],
  'sample_resume.pdf',
  { type: 'application/pdf' }
)

const SAMPLE_JD = `Software Engineer - Full Stack Developer

We are looking for an experienced Full Stack Developer to join our dynamic team. The ideal candidate will have strong experience in modern web technologies and a passion for building scalable applications.

Requirements:
- 5+ years of experience in software development
- Strong proficiency in React, Node.js, and Python
- Experience with RESTful APIs and microservices architecture
- Knowledge of Docker and CI/CD pipelines
- Experience with cloud platforms (AWS, Azure, or GCP)
- Strong problem-solving skills and attention to detail
- Excellent communication and teamwork abilities

Responsibilities:
- Design and develop scalable web applications
- Collaborate with cross-functional teams
- Write clean, maintainable code
- Participate in code reviews and technical discussions
- Optimize application performance
- Implement best practices for security and data protection

Nice to have:
- Experience with TypeScript
- Knowledge of GraphQL
- Experience with Kubernetes
- Familiarity with machine learning concepts`

function App() {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [results, setResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [atsResume, setAtsResume] = useState(null)
  const [atsResumeData, setAtsResumeData] = useState(null)
  const [isGeneratingATS, setIsGeneratingATS] = useState(false)

  const handleDemoMode = () => {
    setResumeFile(SAMPLE_RESUME_FILE)
    setJobDescription(SAMPLE_JD)
    setResults(null)
    setError(null)
  }

  const handleAnalyze = async () => {
    // Validation
    if (!resumeFile) {
      setError('Please upload a resume file')
      return
    }

    if (!jobDescription.trim()) {
      setError('Please enter a job description')
      return
    }

    setIsLoading(true)
    setError(null)
    setResults(null)

    try {
      const formData = new FormData()
      formData.append('resume', resumeFile)
      formData.append('job_description', jobDescription)

      // Use proxy or direct backend URL
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${backendUrl}/analyze`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const data = await response.json()
      setResults(data)
      
      // Extract and store resume text for ATS generation
      // We'll extract it when needed, but for now we can parse the file
      // In a production app, the backend could return the parsed text
    } catch (err) {
      setError(err.message || 'An error occurred during analysis. Please try again.')
      console.error('Analysis error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGenerateATSResume = async () => {
    if (!resumeFile) {
      setError('Please upload a resume file first')
      return
    }

    if (!jobDescription.trim()) {
      setError('Please enter a job description first')
      return
    }

    setIsGeneratingATS(true)
    setError(null)
    setAtsResume(null)

    try {
      // Get missing keywords from results if available
      const missingKeywords = results?.missing_keywords || []

      // Generate ATS resume - backend will parse the file
      const atsFormData = new FormData()
      atsFormData.append('resume', resumeFile)
      atsFormData.append('job_description', jobDescription)
      if (missingKeywords.length > 0) {
        atsFormData.append('missing_keywords', missingKeywords.join(','))
      }

      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${backendUrl}/generate-ats-resume`, {
        method: 'POST',
        body: atsFormData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'ATS resume generation failed')
      }

      const data = await response.json()
      setAtsResume(data.ats_resume_text)
      setAtsResumeData(data.ats_resume_data)  // Store structured data for PDF
    } catch (err) {
      setError(err.message || 'An error occurred while generating ATS resume. Please try again.')
      console.error('ATS generation error:', err)
    } finally {
      setIsGeneratingATS(false)
    }
  }


  // Expose function to Results component
  React.useEffect(() => {
    window.generateATSResume = handleGenerateATSResume
    return () => {
      delete window.generateATSResume
    }
  }, [resumeFile, jobDescription, results])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                ATS Intelligence
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                AI Resume & JD Match Analyzer
              </p>
            </div>
            <button
              onClick={handleDemoMode}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium shadow-sm"
            >
              Demo Mode
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* Upload Resume Section */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <UploadResume
                onFileSelect={setResumeFile}
                selectedFile={resumeFile}
              />
            </div>

            {/* Job Description Section */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <JobDescription
                value={jobDescription}
                onChange={setJobDescription}
              />
            </div>

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              disabled={isLoading}
              className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold text-lg hover:bg-primary-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed shadow-md"
            >
              {isLoading ? 'Analyzing...' : 'Analyze Match'}
            </button>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}
          </div>

          {/* Right Column - Results */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6">
              <Results results={results} isLoading={isLoading} />
            </div>
          </div>
        </div>

        {/* ATS Resume Generator Section */}
        {(atsResume || isGeneratingATS) && (
          <div className="mt-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <ATSPreview atsResume={atsResume} isLoading={isGeneratingATS} />
              {atsResume && (
                <div className="mt-6">
                  <DownloadButton 
                    atsResume={atsResume} 
                    atsResumeData={atsResumeData}
                    disabled={isGeneratingATS} 
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600">
            © 2024 ATS Intelligence. Powered by AI & NLP.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App

