"""
FastAPI Main Application
ATS Intelligence - Resume & JD Match Analyzer Backend
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
import tempfile
import os
import json
from pathlib import Path
from typing import Optional

from resume_parser import parse_resume
from jd_parser import process_job_description
from analyzer import analyze_match
from resume_generator import generate_ats_resume

# PDF generator is optional (only needed for PDF download)
try:
    from pdf_generator import generate_pdf_from_text, create_pdf_file
    PDF_AVAILABLE = True
    print("PDF generation enabled (reportlab installed)")
except ImportError as e:
    PDF_AVAILABLE = False
    print(f"Warning: reportlab not installed. PDF generation will be disabled. Error: {str(e)}")

app = FastAPI(
    title="ATS Intelligence API",
    description="AI-powered Resume and Job Description Match Analyzer",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "message": "ATS Intelligence API is running",
        "version": "1.0.0"
    }


@app.post("/analyze")
async def analyze_resume_jd(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Analyze resume and job description match.
    
    Args:
        resume: Uploaded resume file (PDF or DOCX)
        job_description: Job description text
        
    Returns:
        JSON response with analysis results
    """
    try:
        # Validate file type
        file_extension = Path(resume.filename).suffix.lower()
        if file_extension not in ['.pdf', '.docx', '.doc']:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload PDF or DOCX file."
            )
        
        # Validate job description
        if not job_description or len(job_description.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Job description cannot be empty."
            )
        
        # Save uploaded file temporarily
        # Use delete=False and ensure file is closed before reading
        tmp_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_path = tmp_file.name
            content = await resume.read()
            tmp_file.write(content)
            tmp_file.flush()  # Ensure data is written to disk
            os.fsync(tmp_file.fileno())  # Force write to disk
        # File is now closed, safe to read
        
        # Small delay to ensure file system has updated
        import time
        time.sleep(0.1)
        
        try:
            # Verify file exists before parsing
            if not os.path.exists(tmp_path):
                raise HTTPException(
                    status_code=400,
                    detail="Temporary file was not created properly."
                )
            
            # Parse resume
            resume_text = parse_resume(tmp_path, file_extension)
            
            if not resume_text or len(resume_text.strip()) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract text from resume. Please ensure the file is not corrupted."
                )
            
            # Process job description
            jd_processed = process_job_description(job_description)
            jd_text = jd_processed['cleaned_text']
            jd_keywords = jd_processed['keywords']
            
            # Perform analysis
            print("Starting analysis...")
            try:
                analysis_results = analyze_match(resume_text, jd_text, jd_keywords)
                print("Analysis completed successfully")
                return JSONResponse(content=analysis_results)
            except Exception as analysis_error:
                print(f"Analysis error: {str(analysis_error)}")
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=500,
                    detail=f"Error during analysis: {str(analysis_error)}"
                )
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@app.post("/generate-ats-resume")
async def generate_ats_friendly_resume(
    resume: UploadFile = File(None),
    resume_text: str = Form(None),
    job_description: str = Form(...),
    missing_keywords: str = Form(None)
):
    """
    Generate ATS-friendly resume from original resume and job description.
    
    Args:
        resume: Uploaded resume file (PDF or DOCX) - optional if resume_text provided
        resume_text: Original resume text - optional if resume file provided
        job_description: Job description text
        missing_keywords: Comma-separated list of missing keywords (optional)
        
    Returns:
        JSON response with ATS-optimized resume text
    """
    try:
        # Get resume text from file or form data
        final_resume_text = None
        
        if resume and resume.filename:
            # Parse resume from file
            file_extension = Path(resume.filename).suffix.lower()
            if file_extension not in ['.pdf', '.docx', '.doc']:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Please upload PDF or DOCX file."
                )
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_path = tmp_file.name
                content = await resume.read()
                tmp_file.write(content)
            
            try:
                # Parse resume
                final_resume_text = parse_resume(tmp_path, file_extension)
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        elif resume_text:
            # Use provided resume text
            final_resume_text = resume_text
        else:
            raise HTTPException(
                status_code=400,
                detail="Either resume file or resume_text must be provided."
            )
        
        if not final_resume_text or len(final_resume_text.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Could not extract resume text. Please ensure the file is not corrupted."
            )
        
        # Parse missing keywords if provided
        keywords_list = []
        if missing_keywords:
            keywords_list = [kw.strip() for kw in missing_keywords.split(',') if kw.strip()]
        
        # Generate ATS-friendly resume (returns structured dict)
        resume_data = generate_ats_resume(final_resume_text, job_description, keywords_list)
        
        # Convert to text for display
        from resume_parser_json import resume_dict_to_text
        ats_resume_text = resume_dict_to_text(resume_data)
        
        return JSONResponse(content={
            "ats_resume_text": ats_resume_text,
            "ats_resume_data": resume_data  # Also return structured data for PDF generation
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating ATS resume: {str(e)}"
        )


@app.post("/download-pdf")
async def download_ats_resume_pdf(
    resume_data: str = Form(...)
):
    """
    Generate and download ATS resume as PDF.
    REQUIRES structured data - does NOT accept raw text.
    
    Args:
        resume_data: Structured resume JSON (REQUIRED)
        
    Returns:
        PDF file response
    """
    if not PDF_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="PDF generation is not available. Please install reportlab: pip install reportlab"
        )
    
    try:
        # Parse structured data (REQUIRED)
        try:
            resume_data_dict = json.loads(resume_data)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON format for resume_data: {str(e)}"
            )
        
        # Validate structure
        required_keys = ['professional_summary', 'skills', 'experience', 'projects', 'education']
        if not all(key in resume_data_dict for key in required_keys):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields in resume_data. Required: {required_keys}"
            )
        
        # Generate PDF bytes from structured data ONLY
        print(f"Generating PDF from structured data...")
        pdf_bytes = generate_pdf_from_text("", None, resume_data_dict)
        
        if not pdf_bytes or len(pdf_bytes) == 0:
            raise HTTPException(
                status_code=500,
                detail="PDF generation returned empty data."
            )
        
        print(f"PDF generated successfully ({len(pdf_bytes)} bytes)")
        
        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=ats_optimized_resume.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"PDF generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating PDF: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

