"""
Quick Analyzer - Fast fallback when model loading is slow
"""

def quick_match_score(resume_text: str, jd_text: str) -> float:
    """
    Quick match score calculation using simple text similarity.
    Falls back to this if sentence-transformers is slow.
    """
    resume_words = set(resume_text.lower().split())
    jd_words = set(jd_text.lower().split())
    
    # Remove common stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those'}
    
    resume_words = resume_words - stopwords
    jd_words = jd_words - stopwords
    
    # Calculate Jaccard similarity
    intersection = len(resume_words & jd_words)
    union = len(resume_words | jd_words)
    
    if union == 0:
        return 0.0
    
    similarity = intersection / union
    # Scale to 0-100 and add some base score
    match_score = min(100, (similarity * 80) + 20)  # Scale and add base
    
    return round(match_score, 2)





