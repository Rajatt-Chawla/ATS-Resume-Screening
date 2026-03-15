"""
Analyzer Module
Handles match score calculation, keyword gap detection, and AI suggestions.
"""

import os
from typing import List, Dict
# Removed sentence-transformers import - using fast text-based method instead
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import requests

# Model loading removed - using fast text-based similarity instead


def calculate_match_score(resume_text: str, jd_text: str) -> float:
    """
    Calculate match score between resume and job description using embeddings.
    Uses fast text-based method to avoid model download delays.
    
    Args:
        resume_text: Cleaned resume text
        jd_text: Cleaned job description text
        
    Returns:
        Match score as percentage (0-100)
    """
    # Use fast text-based similarity (no model download needed)
    # This works immediately without waiting for model download
    resume_words = set(resume_text.lower().split())
    jd_words = set(jd_text.lower().split())
    
    # Remove common stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    resume_words = resume_words - stopwords
    jd_words = jd_words - stopwords
    
    # Calculate Jaccard similarity
    intersection = len(resume_words & jd_words)
    union = len(resume_words | jd_words)
    
    if union == 0:
        return 0.0
    
    similarity = intersection / union
    # Scale to 0-100 with better distribution
    match_score = min(100, (similarity * 70) + 30)  # Scale and add base
    
    return round(match_score, 2)
    
    # Original AI model code (commented out for speed)
    # Uncomment below if you want to use the AI model (requires model download)
    """
    try:
        # Get the model with timeout handling
        print("Loading AI model (first time may take 2-3 minutes)...")
        transformer = get_model()
        print("Model loaded, calculating embeddings...")
        
        # Generate embeddings
        resume_embedding = transformer.encode([resume_text])
        jd_embedding = transformer.encode([jd_text])
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(resume_embedding, jd_embedding)
        # Extract scalar value and convert to native Python float immediately
        similarity = float(np.asarray(similarity_matrix[0][0]).item())
        
        # Convert to percentage and round to 2 decimal places
        # Use Python's built-in round() and ensure float type
        match_score = float(round(similarity * 100, 2))
        
        return match_score
    except Exception as e:
        print(f"Error with AI model, using quick fallback: {str(e)}")
        # Fallback to quick text-based similarity
        from quick_analyzer import quick_match_score
        return quick_match_score(resume_text, jd_text)
    """


def detect_missing_keywords(resume_text: str, jd_keywords: List[str]) -> List[str]:
    """
    Detect keywords from JD that are missing in the resume.
    
    Args:
        resume_text: Cleaned resume text
        jd_keywords: List of keywords from job description
        
    Returns:
        List of missing keywords
    """
    resume_lower = resume_text.lower()
    missing_keywords = []
    
    for keyword in jd_keywords:
        keyword_lower = keyword.lower()
        # Check if keyword exists in resume (exact match or as part of a word)
        if keyword_lower not in resume_lower:
            missing_keywords.append(keyword)
    
    return missing_keywords


def get_ai_suggestions(resume_text: str, jd_text: str) -> Dict[str, str]:
    """
    Get AI-powered suggestions using HuggingFace Inference API.
    Uses fast fallback to avoid API delays.
    
    Args:
        resume_text: Cleaned resume text
        jd_text: Cleaned job description text
        
    Returns:
        Dictionary with skill_gap_analysis, resume_suggestions, and tailored_summary
    """
    # Use fallback immediately to avoid API delays
    # HuggingFace free tier can be slow/unreliable
    return get_fallback_suggestions(resume_text, jd_text)


def parse_ai_output(ai_output: str) -> Dict[str, str]:
    """
    Parse AI output into structured suggestions.
    
    Args:
        ai_output: Raw AI response text
        
    Returns:
        Dictionary with structured suggestions
    """
    # Basic parsing - split by common patterns
    output_lower = ai_output.lower()
    
    # Try to extract sections (this is a simple parser - can be improved)
    skill_gap = "Based on the analysis, focus on developing skills mentioned in the job description that are not currently highlighted in your resume."
    suggestions = "Consider adding specific examples of your achievements and quantifying your impact. Tailor your resume to include keywords from the job description."
    summary = "A professional summary that highlights your relevant experience and aligns with the job requirements would strengthen your application."
    
    # If AI output contains structured info, try to extract it
    if "skill" in output_lower or "gap" in output_lower:
        skill_gap = ai_output
    
    return {
        'skill_gap_analysis': skill_gap,
        'resume_suggestions': suggestions,
        'tailored_summary': summary
    }


def get_fallback_suggestions(resume_text: str, jd_text: str) -> Dict[str, str]:
    """
    Generate fallback suggestions when AI API is unavailable.
    
    Args:
        resume_text: Cleaned resume text
        jd_text: Cleaned job description text
        
    Returns:
        Dictionary with basic suggestions
    """
    return {
        'skill_gap_analysis': 'Review the job description requirements and identify skills you may need to develop or highlight more prominently in your resume.',
        'resume_suggestions': '1. Add quantifiable achievements\n2. Include relevant keywords from the job description\n3. Highlight transferable skills\n4. Use action verbs to describe your experience',
        'tailored_summary': 'Craft a professional summary that directly addresses the key requirements mentioned in the job description. Focus on your most relevant experience and achievements.'
    }


def analyze_match(resume_text: str, jd_text: str, jd_keywords: List[str]) -> Dict:
    """
    Main analysis function that combines all analysis steps.
    Optimized for speed - no slow API calls or model downloads.
    
    Args:
        resume_text: Cleaned resume text
        jd_text: Cleaned job description text
        jd_keywords: List of keywords from job description
        
    Returns:
        Complete analysis results dictionary
    """
    # Step 1: Calculate match score (fast text-based, no model needed)
    match_score = calculate_match_score(resume_text, jd_text)
    match_score = float(match_score)
    
    # Step 2: Detect missing keywords (instant)
    missing_keywords = detect_missing_keywords(resume_text, jd_keywords)
    
    # Step 3: Get suggestions (instant fallback, no API calls)
    ai_suggestions = get_ai_suggestions(resume_text, jd_text)
    
    return {
        'match_score': match_score,
        'missing_keywords': missing_keywords,
        'skill_gap_analysis': ai_suggestions['skill_gap_analysis'],
        'resume_suggestions': ai_suggestions['resume_suggestions'],
        'tailored_summary': ai_suggestions['tailored_summary']
    }

