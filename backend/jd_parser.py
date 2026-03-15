"""
Job Description Parser Module
Handles cleaning and keyword extraction from job descriptions.
"""

import re
from typing import List
from collections import Counter
import string


# Common stopwords to filter out (expanded list)
STOPWORDS = {
    # Articles and prepositions
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
    'to', 'was', 'will', 'with', 'this', 'but', 'they', 'have',
    'had', 'what', 'said', 'each', 'which', 'their', 'time', 'if',
    'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her',
    'would', 'make', 'like', 'into', 'him', 'two', 'more',
    'very', 'after', 'words', 'long', 'than', 'first', 'been', 'call',
    'who', 'oil', 'now', 'find', 'down', 'day', 'did', 'get',
    'come', 'made', 'may', 'part',
    # Pronouns and common verbs
    'you', 'your', 'yours', 'we', 'our', 'ours', 'us', 'i', 'me', 'my',
    'can', 'could', 'should', 'must', 'might', 'shall',
    # Common adjectives and adverbs
    'about', 'all', 'also', 'any', 'both', 'other', 'such', 'only',
    'just', 'even', 'most', 'much', 'well', 'too', 'how', 'when',
    'where', 'why', 'there', 'here',
    # Common nouns (not skills)
    'job', 'work', 'team', 'company', 'role', 'position', 'experience',
    'years', 'year', 'month', 'months', 'week', 'weeks', 'day', 'days',
    'hour', 'hours', 'time', 'times', 'way', 'ways', 'thing', 'things',
    'one', 'ones', 'use', 'uses', 'need', 'needs', 'want', 'wants',
    # Common verbs
    'join', 'work', 'help', 'helping', 'need', 'needs', 'want', 'wants',
    'use', 'uses', 'using', 'used', 'know', 'knows', 'knowing', 'known',
    'see', 'sees', 'seeing', 'seen', 'look', 'looks', 'looking', 'looked',
    'take', 'takes', 'taking', 'took', 'taken', 'give', 'gives', 'giving',
    'gave', 'given', 'go', 'goes', 'going', 'went', 'gone', 'come', 'comes',
    'coming', 'came', 'say', 'says', 'saying', 'said', 'tell', 'tells',
    'telling', 'told', 'think', 'thinks', 'thinking', 'thought',
    # Common adjectives (not skills)
    'good', 'great', 'best', 'better', 'new', 'old', 'big', 'small',
    'large', 'little', 'high', 'low', 'right', 'wrong', 'true', 'false',
    'real', 'sure', 'able', 'same', 'different', 'important', 'main',
    'next', 'last', 'early', 'late', 'young', 'long', 'short', 'free',
    'full', 'empty', 'ready', 'sure', 'clear', 'easy', 'hard', 'strong',
    'weak', 'open', 'closed', 'hot', 'cold', 'warm', 'cool', 'clean',
    'dirty', 'nice', 'bad', 'sad', 'happy', 'sorry', 'afraid', 'free',
    # Skill level indicators (not skills themselves)
    'proficiency', 'proficient', 'beginner', 'intermediate', 'advanced',
    'expert', 'level', 'levels', 'skill', 'skills', 'ability', 'abilities',
    # Common workplace terms (not technical skills)
    'environment', 'environments', 'relevant', 'relevance', 'about',
    'description', 'descriptions', 'requirement', 'requirements',
    'responsibility', 'responsibilities', 'qualification', 'qualifications',
    # Other common words
    'please', 'thank', 'thanks', 'yes', 'no', 'not', 'don', 'doesn',
    'didn', 'won', 'wouldn', 'shouldn', 'couldn', 'can', 'cannot',
    'must', 'might', 'may', 'maybe', 'perhaps', 'probably', 'possibly'
}


def clean_jd_text(jd_text: str) -> str:
    """
    Clean job description text by removing stopwords and normalizing.
    
    Args:
        jd_text: Raw job description text
        
    Returns:
        Cleaned JD text
    """
    # Convert to lowercase
    text = jd_text.lower()
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep alphanumeric and spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_keywords(text: str, top_n: int = 20) -> List[str]:
    """
    Extract top keywords from job description, focusing on technical skills.
    
    Args:
        text: Cleaned job description text
        top_n: Number of top keywords to return
        
    Returns:
        List of top keywords (technical skills and important terms)
    """
    # Split text into words
    words = text.split()
    
    # Filter out stopwords and very short words
    # Minimum length of 4 characters to focus on substantial terms
    keywords = [
        word for word in words 
        if (word not in STOPWORDS and 
            len(word) >= 4 and  # Minimum 4 characters
            not word.isdigit())  # Exclude pure numbers
    ]
    
    # Count word frequencies
    word_freq = Counter(keywords)
    
    # Get top keywords, prioritizing:
    # 1. Technical terms (longer words often indicate technologies/frameworks)
    # 2. Frequency (how often they appear)
    # 3. Exclude very common generic words even if they passed stopword filter
    
    # Additional generic words to exclude (even if not in main stopwords)
    additional_generic = {
        'experience', 'working', 'develop', 'development', 'design', 'designing',
        'manage', 'management', 'project', 'projects', 'create', 'creating',
        'build', 'building', 'implement', 'implementation', 'provide', 'provides',
        'support', 'supports', 'ensure', 'ensures', 'maintain', 'maintains'
    }
    
    # Score keywords: frequency * length bonus (technical terms are often longer)
    # But exclude generic words unless they appear very frequently
    scored_keywords = []
    for word, count in word_freq.items():
        if word in additional_generic and count < 3:
            continue  # Skip generic words that don't appear frequently
        # Score: frequency with bonus for longer words (likely technical terms)
        score = count * (1 + len(word) * 0.05)
        scored_keywords.append((word, score, count))
    
    # Sort by score (descending)
    scored_keywords.sort(key=lambda x: x[1], reverse=True)
    
    # Take top N keywords
    top_keywords = [word for word, score, count in scored_keywords[:top_n]]
    
    return top_keywords


def process_job_description(jd_text: str) -> dict:
    """
    Process job description and extract keywords.
    
    Args:
        jd_text: Raw job description text
        
    Returns:
        Dictionary with cleaned text and keywords
    """
    # Clean the JD text
    cleaned_text = clean_jd_text(jd_text)
    
    # Extract top keywords
    keywords = extract_keywords(cleaned_text, top_n=20)
    
    return {
        'cleaned_text': cleaned_text,
        'keywords': keywords
    }

