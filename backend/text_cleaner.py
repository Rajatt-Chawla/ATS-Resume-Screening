"""
Hard Text Cleaner Module
Removes icon words, URLs, repeated words, and normalizes text.
This is MANDATORY before sending text to AI.
"""

import re
from typing import List


# Icon words and patterns to remove
ICON_WORDS = [
    'phone-alt', 'phone', 'envelope', 'email', 'youtube', 'map-marker-alt',
    'map-marker', 'linkedin', 'github', 'twitter', 'facebook', 'instagram',
    'globe', 'home', 'user', 'briefcase', 'graduation-cap', 'award',
    'calendar', 'clock', 'location', 'address', 'contact'
]

# Common URL patterns
URL_PATTERNS = [
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    r'www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    r'[a-zA-Z0-9.-]+\.(com|org|net|edu|io|co|gov)',
]

# Section markers for programmatic detection
SECTION_MARKERS = {
    'experience': ['experience', 'work experience', 'employment', 'professional experience', 'career'],
    'education': ['education', 'academic', 'qualifications', 'degrees'],
    'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'proficiencies'],
    'projects': ['projects', 'portfolio', 'work samples', 'key projects'],
    'summary': ['summary', 'professional summary', 'profile', 'objective', 'about'],
    'certifications': ['certifications', 'certificates', 'licenses', 'credentials']
}


def hard_clean_text(text: str) -> str:
    """
    Hard clean text by removing icon words, URLs, repeated words, and normalizing.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Step 1: Remove URLs
    text = remove_urls(text)
    
    # Step 2: Remove icon words
    text = remove_icon_words(text)
    
    # Step 3: Remove repeated consecutive words (3+ times)
    text = remove_repeated_words(text)
    
    # Step 4: Normalize whitespace
    text = normalize_whitespace(text)
    
    # Step 5: Remove words shorter than 2 chars (except common ones)
    text = remove_short_words(text)
    
    # Step 6: Remove special characters that break parsing
    text = clean_special_chars(text)
    
    return text.strip()


def remove_urls(text: str) -> str:
    """Remove URLs from text."""
    for pattern in URL_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text


def remove_icon_words(text: str) -> str:
    """Remove icon words and patterns."""
    # Create pattern to match icon words (case insensitive, whole word)
    for icon_word in ICON_WORDS:
        # Match whole word only
        pattern = r'\b' + re.escape(icon_word) + r'\b'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove font-awesome style classes
    text = re.sub(r'fa-[a-z-]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'fas?\s+fa-[a-z-]+', '', text, flags=re.IGNORECASE)
    
    return text


def remove_repeated_words(text: str) -> str:
    """
    Remove words repeated 3+ times consecutively.
    Example: "youtube youtube youtube" -> "youtube"
    """
    # Pattern to match word repeated 3+ times
    pattern = r'\b(\w+)(\s+\1){2,}\b'
    text = re.sub(pattern, r'\1', text, flags=re.IGNORECASE)
    
    # Also handle case where word is concatenated (e.g., "YouTubeYouTubeYouTube")
    pattern_concat = r'(\w+)\1{2,}'
    text = re.sub(pattern_concat, r'\1', text)
    
    return text


def normalize_whitespace(text: str) -> str:
    """Replace multiple spaces/tabs/newlines with single space."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with single newline
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Replace tabs with spaces
    text = re.sub(r'\t+', ' ', text)
    # Remove leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text


def remove_short_words(text: str) -> str:
    """
    Remove words shorter than 2 chars (except common ones like 'I', 'a').
    This helps remove random characters and noise.
    """
    # Keep common short words
    keep_words = {'i', 'a', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 'if', 'in', 'is', 'it', 'me', 'my', 'no', 'of', 'on', 'or', 'so', 'to', 'up', 'us', 'we'}
    
    words = text.split()
    cleaned_words = []
    
    for word in words:
        # Keep if it's a common short word or longer than 2 chars
        if len(word) > 2 or word.lower() in keep_words:
            cleaned_words.append(word)
        # Also keep if it contains numbers or special chars (like dates, percentages)
        elif re.search(r'[0-9%$]', word):
            cleaned_words.append(word)
    
    return ' '.join(cleaned_words)


def clean_special_chars(text: str) -> str:
    """Remove or normalize special characters that break parsing."""
    # Remove zero-width characters
    text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    # Remove excessive punctuation (keep single punctuation)
    text = re.sub(r'[!?]{2,}', '!', text)
    text = re.sub(r'[.]{3,}', '...', text)
    
    return text


def extract_name_and_contact(text: str) -> dict:
    """
    Extract name and contact info from first few lines of resume.
    This MUST be done separately - do NOT include in summary.
    
    Args:
        text: Resume text
        
    Returns:
        Dictionary with name and contact info
    """
    lines = text.split('\n')
    
    # First 1-3 lines usually contain name and contact
    header_lines = [line.strip() for line in lines[:5] if line.strip()]
    
    name = ""
    contact = {
        'phone': '',
        'email': '',
        'linkedin': '',
        'location': ''
    }
    
    # First line is usually name (if it's not too long and doesn't look like contact)
    if header_lines:
        first_line = header_lines[0]
        # Name is usually 2-50 chars, doesn't contain @ or phone patterns
        if len(first_line) <= 50 and '@' not in first_line and not re.search(r'\d{10,}', first_line):
            name = first_line
            header_lines = header_lines[1:]
    
    # Extract contact info from remaining header lines
    contact_text = ' '.join(header_lines[:3])
    
    # Extract phone
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', contact_text)
    if phone_match:
        contact['phone'] = phone_match.group(0).strip()
    
    # Extract email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', contact_text)
    if email_match:
        contact['email'] = email_match.group(0).strip()
    
    # Extract LinkedIn
    linkedin_match = re.search(r'(linkedin\.com/in/|linkedin\.com/company/)[\w-]+', contact_text, re.IGNORECASE)
    if linkedin_match:
        contact['linkedin'] = linkedin_match.group(0).strip()
    
    # Extract location (usually country, city, or state)
    # Look for common location patterns
    location_keywords = ['india', 'usa', 'united states', 'california', 'new york', 'texas', 'london', 'uk']
    for keyword in location_keywords:
        if keyword.lower() in contact_text.lower():
            # Extract surrounding context
            match = re.search(rf'\b[\w\s]*{re.escape(keyword)}[\w\s]*\b', contact_text, re.IGNORECASE)
            if match:
                contact['location'] = match.group(0).strip()
                break
    
    # If no location found but there's text left, use it
    if not contact['location'] and header_lines:
        remaining = ' '.join(header_lines)
        # Remove already extracted info
        remaining = remaining.replace(contact['phone'], '').replace(contact['email'], '').replace(contact['linkedin'], '')
        remaining = remaining.strip()
        if remaining and len(remaining) < 50:
            contact['location'] = remaining
    
    return {
        'name': name,
        'contact': contact
    }


def detect_sections(text: str) -> dict:
    """
    Programmatically detect sections in resume text.
    Uses regex to find section headers BEFORE sending to AI.
    
    Args:
        text: Resume text
        
    Returns:
        Dictionary with section names as keys and content as values
    """
    sections = {}
    
    # Remove header/contact info first (first 1-3 lines)
    lines = text.split('\n')
    # Skip first few lines (header)
    content_start = 0
    for i, line in enumerate(lines[:5]):
        if any(marker in line.lower() for markers in SECTION_MARKERS.values() for marker in markers):
            content_start = i
            break
    
    # Section detection patterns (case insensitive)
    section_patterns = {
        'summary': re.compile(r'\n\s*(PROFESSIONAL\s+SUMMARY|SUMMARY|PROFILE|OBJECTIVE|ABOUT)\s*\n', re.IGNORECASE),
        'skills': re.compile(r'\n\s*(SKILLS|TECHNICAL\s+SKILLS|COMPETENCIES|EXPERTISE)\s*\n', re.IGNORECASE),
        'experience': re.compile(r'\n\s*(EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT|PROFESSIONAL\s+EXPERIENCE|CAREER)\s*\n', re.IGNORECASE),
        'projects': re.compile(r'\n\s*(PROJECTS|PORTFOLIO|WORK\s+SAMPLES|KEY\s+PROJECTS)\s*\n', re.IGNORECASE),
        'education': re.compile(r'\n\s*(EDUCATION|ACADEMIC|QUALIFICATIONS|DEGREES)\s*\n', re.IGNORECASE),
        'certifications': re.compile(r'\n\s*(CERTIFICATIONS|CERTIFICATES|LICENSES|CREDENTIALS)\s*\n', re.IGNORECASE)
    }
    
    # Find all section positions
    section_positions = []
    for section_name, pattern in section_patterns.items():
        for match in pattern.finditer(text):
            section_positions.append((match.start(), section_name, match.group(0)))
    
    # Sort by position
    section_positions.sort(key=lambda x: x[0])
    
    # Extract content for each section
    for i, (start_pos, section_name, header) in enumerate(section_positions):
        # Find end position (next section or end of text)
        if i + 1 < len(section_positions):
            end_pos = section_positions[i + 1][0]
        else:
            end_pos = len(text)
        
        # Extract section content (skip the header itself)
        section_content = text[start_pos + len(header):end_pos].strip()
        if section_content:
            sections[section_name] = section_content
    
    # If no sections detected, try keyword-based detection
    if not sections:
        return detect_sections_by_keywords(text[content_start * 20:])  # Skip header area
    
    return sections


def detect_sections_by_keywords(text: str) -> dict:
    """
    Fallback: Detect sections by keywords when regex fails.
    """
    sections = {}
    lines = text.split('\n')
    
    current_section = None
    current_content = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if this line is a section header
        detected_section = None
        for section_name, markers in SECTION_MARKERS.items():
            for marker in markers:
                if marker in line_lower and len(line_lower) < 50:
                    detected_section = section_name
                    break
            if detected_section:
                break
        
        if detected_section:
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            current_section = detected_section
            current_content = []
        elif current_section:
            # Add to current section
            if line.strip():
                current_content.append(line)
        else:
            # Content before first section (likely summary)
            if not sections.get('summary'):
                sections['summary'] = []
            if line.strip():
                sections['summary'].append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # Convert summary list to string
    if 'summary' in sections and isinstance(sections['summary'], list):
        sections['summary'] = '\n'.join(sections['summary']).strip()
    
    return sections


def extract_structured_data_from_text(text: str, detected_sections: dict = None) -> dict:
    """
    Extract structured data from cleaned text using programmatic parsing.
    This is used as a fallback when AI fails.
    
    Args:
        text: Cleaned resume text
        detected_sections: Pre-detected sections (if available)
        
    Returns:
        Structured resume dictionary
    """
    # Use provided sections or detect them
    if detected_sections:
        sections = detected_sections
    else:
        sections = detect_sections(text)
    
    # Extract professional summary
    summary = sections.get('summary', sections.get('header', ''))
    if len(summary) > 500:
        summary = summary[:500] + '...'
    
    # Extract skills
    skills_text = sections.get('skills', '')
    skills = extract_skills_from_text(skills_text)
    
    # Extract experience
    experience_text = sections.get('experience', '')
    experience = extract_experience_from_text(experience_text)
    
    # Extract projects
    projects_text = sections.get('projects', '')
    projects = extract_projects_from_text(projects_text)
    
    # Extract education (return as list)
    education_text = sections.get('education', '')
    education = extract_education_from_text(education_text)
    
    # Ensure education is a list
    if isinstance(education, dict):
        education = [education]
    
    return {
        'professional_summary': summary,
        'skills': skills,
        'experience': experience,
        'projects': projects,
        'education': education if isinstance(education, list) else [education] if education else []
    }


def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from text (comma-separated or bullet list)."""
    if not text:
        return []
    
    skills = []
    
    # Try comma-separated first
    if ',' in text:
        skills = [s.strip() for s in text.split(',') if s.strip() and len(s.strip()) > 2]
    else:
        # Try bullet points or line breaks
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Remove bullet markers
            line = re.sub(r'^[•\-\*]\s*', '', line)
            if line and len(line) > 2 and len(line) < 30:
                skills.append(line)
    
    # Filter out common non-skill words
    non_skills = {'and', 'or', 'with', 'including', 'such', 'as', 'the', 'a', 'an'}
    skills = [s for s in skills if s.lower() not in non_skills]
    
    return skills[:25]


def extract_experience_from_text(text: str) -> List[dict]:
    """Extract experience entries from text."""
    if not text:
        return []
    
    experience = []
    lines = text.split('\n')
    
    current_entry = {
        'company': '',
        'role': '',
        'duration': '',
        'location': '',
        'bullets': []
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line looks like company/role header
        if '|' in line or '—' in line or '–' in line:
            # Save previous entry if it has content
            if current_entry['company'] or current_entry['bullets']:
                experience.append(current_entry.copy())
                current_entry = {
                    'company': '',
                    'role': '',
                    'duration': '',
                    'location': '',
                    'bullets': []
                }
            
            # Parse company/role line
            parts = re.split(r'[|—–]', line)
            if len(parts) >= 2:
                current_entry['company'] = parts[0].strip()
                current_entry['role'] = parts[1].strip() if len(parts) > 1 else ''
        elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
            # Bullet point
            bullet = re.sub(r'^[•\-\*]\s*', '', line)
            if bullet:
                current_entry['bullets'].append(bullet)
        elif not current_entry['company']:
            # Might be company name
            if len(line) < 50 and not any(char.isdigit() for char in line[:10]):
                current_entry['company'] = line
    
    # Save last entry
    if current_entry['company'] or current_entry['bullets']:
        experience.append(current_entry)
    
    return experience[:5]


def extract_projects_from_text(text: str) -> List[dict]:
    """Extract projects from text."""
    if not text:
        return []
    
    projects = []
    lines = text.split('\n')
    
    current_project = {'title': '', 'bullets': []}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('•') or line.startswith('-') or line.startswith('*'):
            bullet = re.sub(r'^[•\-\*]\s*', '', line)
            if bullet:
                current_project['bullets'].append(bullet)
        elif not current_project['title']:
            # First non-bullet line is likely project title
            if len(line) < 60:
                current_project['title'] = line
        else:
            # New project, save previous
            if current_project['title'] or current_project['bullets']:
                projects.append(current_project.copy())
            current_project = {'title': line, 'bullets': []}
    
    # Save last project
    if current_project['title'] or current_project['bullets']:
        projects.append(current_project)
    
    return projects[:5]


def extract_education_from_text(text: str) -> dict:
    """Extract education from text."""
    if not text:
        return {}
    
    lines = text.split('\n')
    education = {
        'institution': '',
        'degree': '',
        'duration': '',
        'location': ''
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for institution name (usually first line)
        if not education['institution']:
            # Check if line contains common education keywords
            if any(word in line.lower() for word in ['university', 'college', 'institute', 'school']):
                education['institution'] = line
            elif len(line) < 60:
                education['institution'] = line
        # Look for degree
        elif not education['degree']:
            if any(word in line.lower() for word in ['bachelor', 'master', 'phd', 'degree', 'b.s', 'b.a', 'm.s', 'm.a']):
                education['degree'] = line
        # Look for date/location
        elif not education['duration']:
            # Check for date patterns
            if re.search(r'\d{4}', line):
                education['duration'] = line
            else:
                education['location'] = line
    
    return education

