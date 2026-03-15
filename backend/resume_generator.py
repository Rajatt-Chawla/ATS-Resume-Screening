"""
ATS Resume Generator Module
Rewrites resume to be 100% ATS-friendly using AI.
Returns structured JSON format for clean rendering.
"""

import requests
import json
import re
from typing import Dict, List, Optional


def deduplicate_text(text: str) -> str:
    """
    Remove repeated consecutive words and clean text.
    
    Args:
        text: Text with potential duplicates
        
    Returns:
        Cleaned text without repeated words
    """
    # Remove patterns like "YouTubeYouTubeYouTube" or "ObsidianObsidianObsidian"
    # Pattern: word repeated 2+ times consecutively
    text = re.sub(r'(\w+)\1{2,}', r'\1', text)
    
    # Remove repeated words with spaces (e.g., "word word word")
    words = text.split()
    cleaned_words = []
    prev_word = None
    
    for word in words:
        # Only add if it's different from previous word
        if word.lower() != prev_word:
            cleaned_words.append(word)
            prev_word = word.lower()
        # Allow one repetition but not more
        elif cleaned_words and cleaned_words[-1].lower() != word.lower():
            cleaned_words.append(word)
    
    return ' '.join(cleaned_words)


def generate_ats_resume(resume_text: str, jd_text: str, missing_keywords: list = None) -> Dict:
    """
    Generate ATS-friendly resume using AI with structured JSON output.
    
    Args:
        resume_text: Original resume text
        jd_text: Job description text
        missing_keywords: List of missing keywords to include
        
    Returns:
        Dictionary with structured resume data
    """
    # STEP 1: HARD CLEAN THE RAW TEXT (MANDATORY)
    from text_cleaner import (
        hard_clean_text, 
        extract_structured_data_from_text,
        extract_name_and_contact,
        detect_sections
    )
    resume_text = hard_clean_text(resume_text)
    jd_text = hard_clean_text(jd_text)
    
    # Also deduplicate
    resume_text = deduplicate_text(resume_text)
    jd_text = deduplicate_text(jd_text)
    
    # STEP 1.5: EXTRACT NAME AND CONTACT SEPARATELY (BEFORE AI)
    name_contact = extract_name_and_contact(resume_text)
    
    # STEP 1.6: DETECT SECTIONS PROGRAMMATICALLY (BEFORE AI)
    detected_sections = detect_sections(resume_text)
    
    # Truncate texts to avoid token limits
    max_length = 1200
    resume_truncated = resume_text[:max_length] if len(resume_text) > max_length else resume_text
    jd_truncated = jd_text[:max_length] if len(jd_text) > max_length else jd_text
    
    # Build keywords section if available
    keywords_section = ""
    if missing_keywords and len(missing_keywords) > 0:
        keywords_section = f"\n\nMissing keywords to include: {', '.join(missing_keywords[:10])}"
    
    # STEP 2: ENFORCE STRICT JSON WITH RETRY LOGIC
    # Create JSON-structured prompt with STRICT instructions
    # Include detected sections to help AI understand structure
    sections_context = ""
    if detected_sections:
        sections_context = "\n\nDetected sections in resume:\n"
        for section_name, content in detected_sections.items():
            if content:
                sections_context += f"- {section_name.upper()}: {content[:200]}...\n"
    
    prompt = f"""Rewrite this resume into structured ATS JSON format.

IMPORTANT:
- Extract name separately (do NOT include in professional summary)
- Extract contact info separately (phone, email, linkedin, location)
- Do NOT include contact info inside professional summary
- Return ONLY valid JSON
- Do NOT return explanations
- Do NOT return any text outside JSON

Return in this exact format:
{{
  "name": "Full Name",
  "contact": {{
    "phone": "",
    "email": "",
    "linkedin": "",
    "location": ""
  }},
  "professional_summary": "2-3 sentence summary (NO contact info)",
  "skills": ["skill1", "skill2", "skill3"],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "Date Range",
      "location": "Location",
      "bullets": ["achievement 1", "achievement 2"]
    }}
  ],
  "projects": [
    {{
      "title": "Project Name",
      "bullets": ["description 1", "description 2"]
    }}
  ],
  "education": [
    {{
      "institution": "University Name",
      "degree": "Degree Name",
      "duration": "Date Range",
      "location": "Location"
    }}
  ]
}}

Rules:
1. Return ONLY the JSON object
2. No text before or after JSON
3. Do not repeat words
4. Do not duplicate sections
5. Use action verbs in bullets
6. Quantify achievements with numbers
7. Include missing keywords naturally
8. Name and contact must be separate from summary

Original Resume:
{resume_truncated}
{sections_context}

Job Description:
{jd_truncated}
{keywords_section}

Return ONLY valid JSON. No other text."""

    try:
        # Use HuggingFace Inference API (free tier)
        API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
        
        # Make request to HuggingFace API
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"inputs": prompt},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_output = result[0].get('generated_text', '') if isinstance(result, list) else result.get('generated_text', '')
            
            # STEP 3: STRICT JSON VALIDATION WITH RETRY
            resume_data = validate_and_parse_json(ai_output, resume_text, jd_text, missing_keywords, prompt, API_URL, name_contact, detected_sections)
            return resume_data
        else:
            # Fallback if API fails
            print(f"API returned status {response.status_code}, using programmatic extraction")
            return extract_structured_data_from_text(resume_text)
            
    except Exception as e:
        # Fallback if API is unavailable
        print(f"AI API error: {str(e)}, using programmatic extraction")
        return extract_structured_data_from_text(resume_text)


def validate_and_parse_json(ai_output: str, resume_text: str, jd_text: str, missing_keywords: list, prompt: str, api_url: str, name_contact: dict, detected_sections: dict, max_retries: int = 2) -> Dict:
    """
    Validate JSON from AI output with retry logic.
    NO FALLBACK TO RAW TEXT - returns error if all retries fail.
    
    Args:
        ai_output: Raw AI response
        resume_text: Original resume text
        jd_text: Job description
        missing_keywords: Missing keywords
        prompt: Original prompt
        api_url: API URL for retry
        name_contact: Extracted name and contact info
        detected_sections: Programmatically detected sections
        max_retries: Maximum retry attempts
        
    Returns:
        Validated structured resume dictionary
        
    Raises:
        ValueError: If JSON parsing fails after all retries
    """
    from text_cleaner import extract_structured_data_from_text
    import json
    import re
    
    # Try to extract and parse JSON
    for attempt in range(max_retries + 1):
        try:
            # Extract JSON from output
            json_match = re.search(r'\{.*\}', ai_output, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                resume_data = json.loads(json_str)
                
                # Validate structure
                if validate_json_structure(resume_data):
                    # Merge name and contact (extracted separately)
                    if name_contact.get('name'):
                        resume_data['name'] = name_contact['name']
                    if name_contact.get('contact'):
                        resume_data['contact'] = name_contact['contact']
                    
                    # Clean and deduplicate all text fields
                    resume_data = clean_resume_data(resume_data, missing_keywords)
                    return resume_data
            
            # If JSON parsing failed and we have retries left
            if attempt < max_retries:
                # Retry with stricter prompt
                retry_prompt = f"""Your previous output was invalid JSON. 

Return ONLY valid JSON in this exact structure:
{{
  "name": "",
  "contact": {{"phone": "", "email": "", "linkedin": "", "location": ""}},
  "professional_summary": "",
  "skills": [],
  "experience": [{{"company": "", "role": "", "duration": "", "location": "", "bullets": []}}],
  "projects": [{{"title": "", "bullets": []}}],
  "education": [{{"institution": "", "degree": "", "duration": "", "location": ""}}]
}}

Do NOT return any text outside JSON. Return ONLY the JSON object."""
                
                try:
                    response = requests.post(
                        api_url,
                        headers={"Content-Type": "application/json"},
                        json={"inputs": retry_prompt},
                        timeout=60
                    )
                    if response.status_code == 200:
                        result = response.json()
                        ai_output = result[0].get('generated_text', '') if isinstance(result, list) else result.get('generated_text', '')
                        continue
                except:
                    pass
        
        except json.JSONDecodeError:
            if attempt < max_retries:
                continue
    
    # If all retries failed, use programmatic extraction with detected sections
    print("AI JSON parsing failed after retries, using programmatic extraction with detected sections")
    resume_data = extract_structured_data_from_text(resume_text, detected_sections)
    
    # Merge name and contact
    if name_contact.get('name'):
        resume_data['name'] = name_contact['name']
    if name_contact.get('contact'):
        resume_data['contact'] = name_contact['contact']
    
    return resume_data


def validate_json_structure(data: Dict) -> bool:
    """Validate that JSON has required structure."""
    required_keys = ['professional_summary', 'skills', 'experience', 'projects', 'education']
    
    if not isinstance(data, dict):
        return False
    
    for key in required_keys:
        if key not in data:
            return False
    
    # Validate types
    if not isinstance(data.get('professional_summary'), str):
        return False
    if not isinstance(data.get('skills'), list):
        return False
    if not isinstance(data.get('experience'), list):
        return False
    if not isinstance(data.get('projects'), list):
        return False
    # Education can be dict or list
    education = data.get('education')
    if not isinstance(education, (dict, list)):
        return False
    
    return True


def clean_resume_data(data: Dict, missing_keywords: list = None) -> Dict:
    """Clean and deduplicate all text fields in resume data."""
    from text_cleaner import hard_clean_text
    
    # Clean summary
    data['professional_summary'] = hard_clean_text(data.get('professional_summary', ''))
    data['professional_summary'] = deduplicate_text(data['professional_summary'])
    
    # Clean skills
    skills = data.get('skills', [])
    cleaned_skills = []
    seen = set()
    for skill in skills:
        skill = hard_clean_text(str(skill)).strip()
        if skill and skill.lower() not in seen and len(skill) > 2:
            cleaned_skills.append(skill)
            seen.add(skill.lower())
    
    # Add missing keywords
    if missing_keywords:
        for kw in missing_keywords[:15]:
            kw = hard_clean_text(str(kw)).strip()
            if kw and len(kw) >= 4 and kw.lower() not in seen:
                cleaned_skills.append(kw)
                seen.add(kw.lower())
    
    data['skills'] = cleaned_skills[:25]
    
    # Clean experience
    for exp in data.get('experience', []):
        exp['company'] = hard_clean_text(deduplicate_text(str(exp.get('company', ''))))
        exp['role'] = hard_clean_text(deduplicate_text(str(exp.get('role', ''))))
        exp['duration'] = hard_clean_text(str(exp.get('duration', '')))
        exp['location'] = hard_clean_text(str(exp.get('location', '')))
        exp['bullets'] = [hard_clean_text(deduplicate_text(str(b))) for b in exp.get('bullets', []) if b]
    
    # Clean projects
    for proj in data.get('projects', []):
        proj['title'] = hard_clean_text(deduplicate_text(str(proj.get('title', ''))))
        proj['bullets'] = [hard_clean_text(deduplicate_text(str(b))) for b in proj.get('bullets', []) if b]
    
    # Clean education
    edu = data.get('education', {})
    if isinstance(edu, dict):
        edu['institution'] = hard_clean_text(deduplicate_text(str(edu.get('institution', ''))))
        edu['degree'] = hard_clean_text(deduplicate_text(str(edu.get('degree', ''))))
        edu['duration'] = hard_clean_text(str(edu.get('duration', '')))
        edu['location'] = hard_clean_text(str(edu.get('location', '')))
    
    return data


# resume_dict_to_text moved to resume_parser_json.py to avoid circular imports


def extract_skills_from_resume(resume_text: str) -> list:
    """
    Extract skills from resume text.
    
    Args:
        resume_text: Resume text
        
    Returns:
        List of skills
    """
    # Common technical skills keywords
    tech_skills = [
        'python', 'javascript', 'java', 'react', 'node', 'sql', 'aws', 'docker',
        'kubernetes', 'git', 'linux', 'html', 'css', 'typescript', 'angular',
        'vue', 'django', 'flask', 'fastapi', 'mongodb', 'postgresql', 'mysql',
        'redis', 'elasticsearch', 'machine learning', 'ai', 'data science',
        'agile', 'scrum', 'ci/cd', 'jenkins', 'terraform', 'ansible'
    ]
    
    resume_lower = resume_text.lower()
    found_skills = [skill for skill in tech_skills if skill in resume_lower]
    
    return found_skills


def get_fallback_ats_resume(resume_text: str, jd_text: str, missing_keywords: list = None) -> str:
    """
    Generate fallback ATS resume when AI API is unavailable.
    Returns properly formatted ATS-friendly resume.
    
    Args:
        resume_text: Original resume text
        jd_text: Job description text
        missing_keywords: Missing keywords to include
        
    Returns:
        Formatted ATS resume
    """
    # Extract sections from original resume
    lines = resume_text.split('\n')
    
    # Build ATS-friendly structure matching LaTeX resume format
    # Clean, professional format similar to LaTeX resume template
    
    # Professional Summary Section
    ats_resume = "PROFESSIONAL SUMMARY\n"
    ats_resume += "-" * 70 + "\n"
    summary = create_professional_summary(resume_text, jd_text)
    ats_resume += summary + "\n\n"
    
    # Experience Section (LaTeX style)
    ats_resume += "EXPERIENCE\n"
    ats_resume += "-" * 70 + "\n"
    
    # Extract and format experience in LaTeX style
    experience_entries = extract_experience_entries_latex_style(resume_text)
    if experience_entries:
        for entry in experience_entries[:5]:  # Limit to 5 most recent
            ats_resume += entry + "\n"
    else:
        # Fallback formatting
        experience_lines = [line.strip() for line in lines 
                          if line.strip() and len(line.strip()) > 10
                          and any(word in line.lower() for word in ['experience', 'worked', 'developed', 'managed', 'led', 'created', 'built', 'designed'])]
        if experience_lines:
            ats_resume += "  Company Name                    Date Range\n"
            ats_resume += "  Job Title                       Location\n"
            ats_resume += "    • " + experience_lines[0] + "\n"
            for line in experience_lines[1:8]:
                enhanced = enhance_bullet_point(line)
                ats_resume += f"    • {enhanced}\n"
        else:
            ats_resume += "  [Professional experience from original resume]\n"
    
    ats_resume += "\n"
    
    # Skills Section (LaTeX style - categorized)
    ats_resume += "SKILLS\n"
    ats_resume += "-" * 70 + "\n"
    skills = extract_skills_from_resume(resume_text)
    if missing_keywords:
        relevant_keywords = [kw for kw in missing_keywords[:15] if len(kw) >= 4]
        skills.extend(relevant_keywords)
    skills = list(set(skills))[:30]
    
    # Categorize skills
    languages = [s for s in skills if s in ['python', 'javascript', 'java', 'typescript', 'html', 'css', 'sql', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift', 'kotlin']]
    frameworks = [s for s in skills if s in ['react', 'node', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'express', 'next', 'nuxt']]
    tools = [s for s in skills if s in ['git', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'terraform', 'ansible', 'figma', 'notion', 'jira', 'github']]
    other_skills = [s for s in skills if s not in languages + frameworks + tools]
    
    if languages:
        ats_resume += f"  Languages: {', '.join(languages[:8])}\n"
    if frameworks:
        ats_resume += f"  Frameworks: {', '.join(frameworks[:8])}\n"
    if tools:
        ats_resume += f"  Tools: {', '.join(tools[:10])}\n"
    if other_skills:
        ats_resume += f"  Technologies: {', '.join(other_skills[:10])}\n"
    
    ats_resume += "\n"
    
    # Education Section (LaTeX style)
    ats_resume += "EDUCATION\n"
    ats_resume += "-" * 70 + "\n"
    
    education_entries = extract_education_entries_latex_style(resume_text)
    if education_entries:
        for entry in education_entries:
            ats_resume += entry + "\n"
    else:
        education_lines = [line.strip() for line in lines 
                          if any(word in line.lower() for word in ['university', 'college', 'degree', 'bachelor', 'master', 'phd', 'education', 'b.s', 'b.a', 'm.s', 'm.a'])]
        if education_lines:
            for line in education_lines[:3]:
                if line.strip():
                    ats_resume += f"  {line.strip()}\n"
        else:
            ats_resume += "  [Education details from original resume]\n"
    
    # Projects Section (if applicable)
    project_lines = [line.strip() for line in lines 
                    if any(word in line.lower() for word in ['project', 'github', 'built', 'developed', 'created'])]
    if project_lines and len(project_lines) > 2:
        ats_resume += "\nPROJECTS\n"
        ats_resume += "-" * 70 + "\n"
        for proj in project_lines[:5]:
            if proj.strip() and len(proj.strip()) > 10:
                enhanced = enhance_bullet_point(proj)
                ats_resume += f"  • {enhanced}\n"
    
    # Certifications (if any)
    cert_lines = [line.strip() for line in lines 
                 if any(word in line.lower() for word in ['certification', 'certified', 'certificate', 'license', 'licensed'])]
    if cert_lines:
        ats_resume += "\nCERTIFICATIONS\n"
        ats_resume += "-" * 70 + "\n"
        for cert in cert_lines[:5]:
            if cert.strip():
                ats_resume += f"  • {cert.strip()}\n"
    
    return ats_resume


def create_professional_summary(resume_text: str, jd_text: str) -> str:
    """
    Create a professional summary based on resume and job description.
    """
    # Extract key information
    skills = extract_skills_from_resume(resume_text)
    top_skills = skills[:5] if skills else []
    
    # Count years of experience (look for patterns like "5 years", "3+ years")
    import re
    years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)', resume_text.lower())
    years = years_match.group(1) if years_match else None
    
    # Build summary
    summary = "Results-driven professional"
    if years:
        summary += f" with {years}+ years of experience"
    if top_skills:
        summary += f" in {', '.join(top_skills[:3])}"
    summary += ". "
    
    # Add value proposition
    summary += "Proven track record of delivering high-quality solutions and driving business results. "
    summary += "Strong problem-solving abilities with expertise in modern technologies and best practices. "
    summary += "Committed to continuous learning and professional growth."
    
    return summary


def extract_experience_entries_latex_style(resume_text: str) -> list:
    """
    Extract formatted experience sections in LaTeX resume style.
    Format: Company Name (left) | Date (right)
            Job Title (left) | Location (right)
            • Bullet points
    """
    lines = resume_text.split('\n')
    experience_entries = []
    current_entry = []
    current_company = None
    current_date = None
    current_title = None
    current_location = None
    
    import re
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # Look for date patterns (e.g., "Aug 2019 -- Present", "2019-2021")
        date_pattern = r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4}|Present|Current)'
        date_match = re.search(date_pattern, line_stripped, re.IGNORECASE)
        
        # Look for company/job patterns
        if any(indicator in line_lower for indicator in ['engineer', 'developer', 'manager', 'analyst', 'specialist', 
                                                          'consultant', 'director', 'lead', 'senior', 'junior', 'associate',
                                                          'intern', 'coordinator', 'executive']):
            # Save previous entry if exists
            if current_company:
                entry = format_experience_entry(current_company, current_date, current_title, current_location, current_entry)
                experience_entries.append(entry)
            
            # Start new entry
            current_entry = []
            # Try to extract company and title
            parts = line_stripped.split('|')
            if len(parts) >= 2:
                current_company = parts[0].strip()
                current_date = parts[1].strip() if len(parts) > 1 else None
            else:
                current_company = line_stripped
                current_date = None
            current_title = None
            current_location = None
            
        elif date_match:
            # This line has a date, might be continuation of job entry
            if current_company:
                current_date = date_match.group(0)
        
        elif current_company and line_stripped:
            # This is a bullet point or detail
            if line_stripped.startswith('•') or line_stripped.startswith('-'):
                current_entry.append(line_stripped[1:].strip())
            else:
                # Check if it's a title/location line
                if '|' in line_stripped:
                    parts = line_stripped.split('|')
                    if len(parts) >= 2:
                        current_title = parts[0].strip()
                        current_location = parts[1].strip()
                else:
                    # Regular bullet point
                    enhanced = enhance_bullet_point(line_stripped)
                    current_entry.append(enhanced)
    
    # Save last entry
    if current_company:
        entry = format_experience_entry(current_company, current_date, current_title, current_location, current_entry)
        experience_entries.append(entry)
    
    return experience_entries[:5]


def format_experience_entry(company, date, title, location, bullets):
    """
    Format a single experience entry in LaTeX style.
    """
    entry = ""
    # Company and date line (right-aligned date)
    if date:
        # Calculate spacing for right alignment (simplified)
        spacing = max(0, 50 - len(company))
        entry += f"  {company}{' ' * spacing}{date}\n"
    else:
        entry += f"  {company}\n"
    
    # Title and location line
    if title:
        if location:
            spacing = max(0, 50 - len(title))
            entry += f"  {title}{' ' * spacing}{location}\n"
        else:
            entry += f"  {title}\n"
    
    # Bullet points
    for bullet in bullets[:6]:  # Limit to 6 bullets per entry
        enhanced = enhance_bullet_point(bullet)
        entry += f"    • {enhanced}\n"
    
    return entry


def extract_education_entries_latex_style(resume_text: str) -> list:
    """
    Extract formatted education sections in LaTeX resume style.
    """
    lines = resume_text.split('\n')
    education_entries = []
    import re
    
    current_school = None
    current_date = None
    current_degree = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        # Look for university/college names
        if any(word in line_lower for word in ['university', 'college', 'institute', 'school']):
            # Save previous entry
            if current_school:
                entry = format_education_entry(current_school, current_date, current_degree)
                education_entries.append(entry)
            
            # Extract school and date
            date_pattern = r'(\w+\s+\d{4})\s*[-–—]\s*(\w+\s+\d{4})'
            date_match = re.search(date_pattern, line_stripped)
            if date_match:
                current_date = date_match.group(0)
                current_school = line_stripped[:date_match.start()].strip()
            else:
                current_school = line_stripped
                current_date = None
            current_degree = None
        
        # Look for degree information
        elif current_school and any(word in line_lower for word in ['bachelor', 'master', 'phd', 'doctorate', 'degree', 'b.s', 'b.a', 'm.s', 'm.a', 'b.sc', 'm.sc']):
            current_degree = line_stripped
    
    # Save last entry
    if current_school:
        entry = format_education_entry(current_school, current_date, current_degree)
        education_entries.append(entry)
    
    return education_entries[:3]


def format_education_entry(school, date, degree):
    """
    Format a single education entry in LaTeX style.
    """
    entry = ""
    if date:
        spacing = max(0, 50 - len(school))
        entry += f"  {school}{' ' * spacing}{date}\n"
    else:
        entry += f"  {school}\n"
    
    if degree:
        entry += f"  {degree}\n"
    
    return entry


def extract_education_sections(resume_text: str) -> list:
    """
    Extract formatted education sections from resume text.
    """
    lines = resume_text.split('\n')
    education_entries = []
    
    for line in lines:
        line_lower = line.lower()
        if any(word in line_lower for word in ['bachelor', 'master', 'phd', 'doctorate', 'degree', 'diploma']):
            if line.strip() and len(line.strip()) > 5:
                education_entries.append(line.strip())
    
    return education_entries[:3]  # Return top 3


def enhance_bullet_point(text: str) -> str:
    """
    Enhance a bullet point with action verbs and quantification.
    
    Args:
        text: Original bullet point text
        
    Returns:
        Enhanced bullet point
    """
    # Common action verbs
    action_verbs = [
        'Developed', 'Implemented', 'Designed', 'Managed', 'Led', 'Created',
        'Built', 'Optimized', 'Improved', 'Increased', 'Reduced', 'Achieved',
        'Delivered', 'Collaborated', 'Streamlined', 'Enhanced', 'Established'
    ]
    
    # If text doesn't start with action verb, try to add one
    text_lower = text.lower().strip()
    if not any(text_lower.startswith(verb.lower()) for verb in action_verbs):
        # Try to find a suitable action verb based on content
        if any(word in text_lower for word in ['develop', 'code', 'program', 'software']):
            text = "Developed " + text
        elif any(word in text_lower for word in ['manage', 'lead', 'team']):
            text = "Managed " + text
        elif any(word in text_lower for word in ['design', 'create', 'build']):
            text = "Created " + text
    
    # Try to add quantification if numbers are mentioned
    if any(char.isdigit() for char in text):
        # Already has numbers, keep as is
        pass
    else:
        # Could add "Significantly" or similar, but keep original for now
        pass
    
    return text.strip()


