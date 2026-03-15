"""
Resume Parser Module
Handles extraction of text from PDF and DOCX resume files.
"""

import re
from typing import Optional

# Try to import PyMuPDF
fitz = None
try:
    import fitz  # PyMuPDF (pymupdf package)
except ImportError:
    try:
        import pymupdf as fitz  # Fallback for newer package name
    except ImportError:
        fitz = None
        print("Warning: PyMuPDF not installed. PDF parsing will be limited.")

# Try to import python-docx
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    Document = None
    print("Warning: python-docx not installed. DOCX parsing will be disabled.")


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file using PyMuPDF.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    if fitz is None:
        raise Exception("PyMuPDF is not installed. Please install it with: pip install pymupdf")
    
    try:
        # Ensure file exists and is readable
        import os
        if not os.path.exists(file_path):
            raise Exception(f"PDF file not found: {file_path}")
        
        # Open PDF with error handling
        doc = None
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            return text
        finally:
            if doc:
                doc.close()
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX file using python-docx.
    
    Args:
        file_path: Path to the DOCX file
        
    Returns:
        Extracted text as string
    """
    if not DOCX_AVAILABLE or Document is None:
        raise Exception("python-docx is not installed. Please install it with: pip install python-docx")
    
    try:
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text)
    except Exception as e:
        raise Exception(f"Error reading DOCX: {str(e)}")


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing special characters and normalizing.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep alphanumeric, spaces, and common punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-]', ' ', text)
    
    # Normalize case (convert to lowercase for consistency)
    text = text.lower()
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def parse_resume(file_path: str, file_extension: str) -> str:
    """
    Main function to parse resume file and return cleaned text.
    
    Args:
        file_path: Path to the resume file
        file_extension: File extension ('.pdf' or '.docx')
        
    Returns:
        Cleaned resume text
    """
    # Extract text based on file type
    if file_extension.lower() == '.pdf':
        raw_text = extract_text_from_pdf(file_path)
    elif file_extension.lower() in ['.docx', '.doc']:
        raw_text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    # Clean the extracted text
    cleaned_text = clean_text(raw_text)
    
    return cleaned_text

