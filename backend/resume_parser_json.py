"""
JSON Parser for ATS Resume
Parses AI output and extracts structured resume data.
"""

import json
import re
from typing import Dict, List, Optional


def parse_json_from_ai_output(ai_output: str, original_resume: str, jd_text: str, missing_keywords: list = None) -> Dict:
    """
    Parse JSON from AI output, with fallback to structured generation.
    
    Args:
        ai_output: Raw AI response
        original_resume: Original resume text
        jd_text: Job description text
        missing_keywords: Missing keywords to include
        
    Returns:
        Structured resume dictionary
    """
    # Try to extract JSON from AI output
    json_match = re.search(r'\{.*\}', ai_output, re.DOTALL)
    
    if json_match:
        try:
            json_str = json_match.group(0)
            resume_data = json.loads(json_str)
            
            # Validate and clean the data
            resume_data = validate_and_clean_resume_data(resume_data, original_resume, missing_keywords)
            return resume_data
        except json.JSONDecodeError:
            pass
    
    # Fallback: generate structured resume from text
    return generate_structured_resume_from_text(original_resume, jd_text, missing_keywords)


def validate_and_clean_resume_data(data: Dict, original_resume: str, missing_keywords: list = None) -> Dict:
    """
    Validate and clean resume data structure.
    
    Args:
        data: Parsed resume data
        original_resume: Original resume for reference
        missing_keywords: Missing keywords to include
        
    Returns:
        Validated and cleaned resume data
    """
    # Import here to avoid circular dependency
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from resume_generator import deduplicate_text, extract_skills_from_resume
    from text_cleaner import hard_clean_text
    
    # Ensure all required fields exist
    education = data.get('education', {})
    # Ensure education is a list
    if isinstance(education, dict):
        education = [education] if education else []
    elif not isinstance(education, list):
        education = []
    
    validated = {
        'name': hard_clean_text(data.get('name', '')),
        'contact': data.get('contact', {}),
        'professional_summary': deduplicate_text(data.get('professional_summary', '')),
        'skills': list(set(data.get('skills', []))),
        'experience': data.get('experience', []),
        'projects': data.get('projects', []),
        'education': education
    }
    
    # Add missing keywords to skills
    if missing_keywords:
        validated['skills'].extend([kw for kw in missing_keywords[:15] if len(kw) >= 4])
        validated['skills'] = list(set(validated['skills']))[:25]
    
    # Ensure skills list has items
    if not validated['skills']:
        validated['skills'] = extract_skills_from_resume(original_resume)[:20]
    
    # Clean and deduplicate all text fields
    validated['professional_summary'] = deduplicate_text(validated['professional_summary'])
    
    for exp in validated['experience']:
        exp['company'] = deduplicate_text(exp.get('company', ''))
        exp['role'] = deduplicate_text(exp.get('role', ''))
        exp['bullets'] = [deduplicate_text(b) for b in exp.get('bullets', [])]
    
    for proj in validated['projects']:
        proj['title'] = deduplicate_text(proj.get('title', ''))
        proj['bullets'] = [deduplicate_text(b) for b in proj.get('bullets', [])]
    
    # Clean education (handle both dict and list)
    education = validated.get('education', [])
    if isinstance(education, dict):
        education = [education]
    
    for edu in education:
        if isinstance(edu, dict):
            edu['institution'] = hard_clean_text(deduplicate_text(str(edu.get('institution', ''))))
            edu['degree'] = hard_clean_text(deduplicate_text(str(edu.get('degree', ''))))
            edu['duration'] = hard_clean_text(str(edu.get('duration', '')))
            edu['location'] = hard_clean_text(str(edu.get('location', '')))
    
    validated['education'] = education
    
    return validated


def generate_structured_resume_from_text(resume_text: str, jd_text: str, missing_keywords: list = None) -> Dict:
    """
    Generate structured resume data from text (fallback when AI fails).
    Uses programmatic extraction - does NOT trust AI formatting.
    
    Args:
        resume_text: Original resume text (should already be cleaned)
        jd_text: Job description text
        missing_keywords: Missing keywords to include
        
    Returns:
        Structured resume dictionary
    """
    # Use programmatic extraction from text_cleaner
    from text_cleaner import extract_structured_data_from_text, hard_clean_text
    from resume_generator import deduplicate_text, extract_skills_from_resume, create_professional_summary
    
    # Ensure text is cleaned
    resume_text = hard_clean_text(resume_text)
    resume_text = deduplicate_text(resume_text)
    
    # Use programmatic extraction (does NOT trust AI formatting)
    structured_data = extract_structured_data_from_text(resume_text)
    
    # Enhance with missing keywords
    if missing_keywords:
        existing_skills = set(s.lower() for s in structured_data.get('skills', []))
        for kw in missing_keywords[:15]:
            kw_clean = hard_clean_text(str(kw)).strip()
            if kw_clean and len(kw_clean) >= 4 and kw_clean.lower() not in existing_skills:
                structured_data['skills'].append(kw_clean)
                existing_skills.add(kw_clean.lower())
    
    # Limit skills
    structured_data['skills'] = structured_data['skills'][:25]
    
    # Enhance summary if empty
    if not structured_data.get('professional_summary'):
        summary = create_professional_summary(resume_text, jd_text)
        structured_data['professional_summary'] = deduplicate_text(summary)
    
    return structured_data


def resume_dict_to_text(resume_data: Dict) -> str:
    """
    Convert structured resume dictionary to formatted text.
    
    Args:
        resume_data: Structured resume dictionary
        
    Returns:
        Formatted text resume
    """
    text = ""
    
    # Name (if available)
    name = resume_data.get('name', '')
    if name:
        text += name + "\n"
    
    # Contact (if available) - render separately, NOT in summary
    contact = resume_data.get('contact', {})
    if isinstance(contact, dict):
        contact_parts = []
        if contact.get('phone'):
            contact_parts.append(contact['phone'])
        if contact.get('email'):
            contact_parts.append(contact['email'])
        if contact.get('linkedin'):
            contact_parts.append(contact['linkedin'])
        if contact.get('location'):
            contact_parts.append(contact['location'])
        
        if contact_parts:
            text += " | ".join(contact_parts) + "\n\n"
    
    # Professional Summary
    text += "PROFESSIONAL SUMMARY\n"
    text += "-" * 70 + "\n"
    text += resume_data.get('professional_summary', '') + "\n\n"
    
    # Skills
    text += "SKILLS\n"
    text += "-" * 70 + "\n"
    skills = resume_data.get('skills', [])
    if skills:
        text += ", ".join(skills[:25]) + "\n\n"
    
    # Experience
    text += "EXPERIENCE\n"
    text += "-" * 70 + "\n"
    experience = resume_data.get('experience', [])
    for exp in experience[:5]:
        company = exp.get('company', 'Company')
        role = exp.get('role', 'Role')
        duration = exp.get('duration', '')
        location = exp.get('location', '')
        
        # Format: Company                    Date
        if duration:
            spacing = max(0, 50 - len(company))
            text += f"  {company}{' ' * spacing}{duration}\n"
        else:
            text += f"  {company}\n"
        
        # Format: Role                       Location
        if role:
            if location:
                spacing = max(0, 50 - len(role))
                text += f"  {role}{' ' * spacing}{location}\n"
            else:
                text += f"  {role}\n"
        
        # Bullets
        bullets = exp.get('bullets', [])
        for bullet in bullets[:6]:
            text += f"    • {bullet}\n"
        text += "\n"
    
    # Projects
    projects = resume_data.get('projects', [])
    if projects:
        text += "PROJECTS\n"
        text += "-" * 70 + "\n"
        for proj in projects[:3]:
            title = proj.get('title', 'Project')
            text += f"  {title}\n"
            bullets = proj.get('bullets', [])
            for bullet in bullets[:4]:
                text += f"    • {bullet}\n"
            text += "\n"
    
    # Education (handle both dict and list)
    text += "EDUCATION\n"
    text += "-" * 70 + "\n"
    education = resume_data.get('education', [])
    
    # Ensure education is a list
    if isinstance(education, dict):
        education = [education] if education else []
    elif not isinstance(education, list):
        education = []
    
    for edu in education[:3]:  # Limit to 3 education entries
        if isinstance(edu, dict):
            institution = edu.get('institution', '')
            degree = edu.get('degree', '')
            duration = edu.get('duration', '')
            location = edu.get('location', '')
            
            if institution:
                if duration:
                    spacing = max(0, 50 - len(institution))
                    text += f"  {institution}{' ' * spacing}{duration}\n"
                else:
                    text += f"  {institution}\n"
                
                if degree:
                    text += f"  {degree}\n"
                
                if location and not duration:
                    text += f"  {location}\n"
                text += "\n"
    
    return text

