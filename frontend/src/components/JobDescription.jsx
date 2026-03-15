import React from 'react'

const JobDescription = ({ value, onChange, placeholder }) => {
  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        Job Description
      </label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder || "Paste the job description here..."}
        className="w-full h-64 px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
        rows={12}
      />
      <p className="mt-2 text-xs text-gray-500">
        Paste the complete job description including requirements, responsibilities, and qualifications
      </p>
    </div>
  )
}

export default JobDescription





