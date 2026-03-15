"""
PDF Generator Module
Converts structured ATS resume data to professional PDF format.
Uses reportlab.platypus for proper formatting.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib import colors
import io
import json
from typing import Dict, Optional


def generate_pdf_from_structured_data(resume_data: Dict, output_path: str = None) -> bytes:
    """
    Generate PDF from structured resume data (preferred method).
    
    Args:
        resume_data: Structured resume dictionary
        output_path: Optional path to save PDF file
        
    Returns:
        PDF bytes
    """
    # Create a BytesIO buffer to hold PDF in memory
    buffer = io.BytesIO()
    
    # Create PDF document with 1 inch margins
    doc = SimpleDocTemplate(
        buffer if output_path is None else output_path,
        pagesize=letter,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Name style (larger, bold)
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#000000'),
        spaceAfter=6,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    # Contact style
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        fontName='Helvetica',
        alignment=TA_LEFT
    )
    
    # Section heading style
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#000000'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    # Normal text style
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        leading=12,
        fontName='Helvetica',
        alignment=TA_LEFT
    )
    
    # Bullet style
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4,
        leading=12,
        leftIndent=20,
        fontName='Helvetica',
        alignment=TA_LEFT
    )
    
    # Company/Role style
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#000000'),
        spaceAfter=2,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    # Date/Location style (right-aligned)
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceAfter=2,
        fontName='Helvetica',
        alignment=TA_RIGHT
    )
    
    # NAME (extract from structured data)
    name = resume_data.get('name', 'Professional Resume')
    if name:
        story.append(Paragraph(escape_html(name), name_style))
    
    # CONTACT (render separately - NOT in summary)
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
            contact_text = ' | '.join(contact_parts)
            story.append(Paragraph(escape_html(contact_text), contact_style))
    
    story.append(Spacer(1, 12))
    
    # PROFESSIONAL SUMMARY
    summary = resume_data.get('professional_summary', '')
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
        story.append(Paragraph(escape_html(summary), normal_style))
        story.append(Spacer(1, 12))
    
    # SKILLS
    skills = resume_data.get('skills', [])
    if skills:
        story.append(Paragraph("SKILLS", section_style))
        skills_text = ", ".join(skills[:25])
        story.append(Paragraph(escape_html(skills_text), normal_style))
        story.append(Spacer(1, 12))
    
    # EXPERIENCE
    experience = resume_data.get('experience', [])
    if experience:
        story.append(Paragraph("EXPERIENCE", section_style))
        
        for exp in experience[:5]:
            company = exp.get('company', '')
            role = exp.get('role', '')
            duration = exp.get('duration', '')
            location = exp.get('location', '')
            
            # Company and Date row
            if company:
                # Create table for company/date alignment
                company_data = [[
                    Paragraph(escape_html(company), company_style),
                    Paragraph(escape_html(duration), date_style) if duration else Paragraph("", date_style)
                ]]
                company_table = Table(company_data, colWidths=[4*inch, 2*inch])
                company_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(company_table)
            
            # Role and Location row
            if role:
                role_data = [[
                    Paragraph(escape_html(role), normal_style),
                    Paragraph(escape_html(location), date_style) if location else Paragraph("", date_style)
                ]]
                role_table = Table(role_data, colWidths=[4*inch, 2*inch])
                role_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(role_table)
            
            # Bullet points
            bullets = exp.get('bullets', [])
            if bullets:
                bullet_items = []
                for bullet in bullets[:6]:
                    bullet_text = escape_html(bullet)
                    bullet_items.append(ListItem(Paragraph(bullet_text, bullet_style), leftIndent=20))
                
                if bullet_items:
                    bullet_list = ListFlowable(bullet_items, bulletType='bullet', start='•')
                    story.append(bullet_list)
            
            story.append(Spacer(1, 8))
    
    # PROJECTS
    projects = resume_data.get('projects', [])
    if projects:
        story.append(Paragraph("PROJECTS", section_style))
        
        for proj in projects[:3]:
            title = proj.get('title', '')
            if title:
                story.append(Paragraph(escape_html(title), company_style))
            
            bullets = proj.get('bullets', [])
            if bullets:
                bullet_items = []
                for bullet in bullets[:4]:
                    bullet_text = escape_html(bullet)
                    bullet_items.append(ListItem(Paragraph(bullet_text, bullet_style), leftIndent=20))
                
                if bullet_items:
                    bullet_list = ListFlowable(bullet_items, bulletType='bullet', start='•')
                    story.append(bullet_list)
            
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 6))
    
    # EDUCATION (can be dict or list)
    education = resume_data.get('education', {})
    if education:
        story.append(Paragraph("EDUCATION", section_style))
        
        # Handle both dict (single education) and list (multiple)
        if isinstance(education, list):
            edu_list = education
        else:
            edu_list = [education]
        
        for edu in edu_list[:3]:  # Limit to 3 education entries
            institution = edu.get('institution', '')
            degree = edu.get('degree', '')
            duration = edu.get('duration', '')
            location = edu.get('location', '')
            
            if institution:
                # Institution and Date row
                edu_data = [[
                    Paragraph(escape_html(institution), company_style),
                    Paragraph(escape_html(duration), date_style) if duration else Paragraph("", date_style)
                ]]
                edu_table = Table(edu_data, colWidths=[4*inch, 2*inch])
                edu_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                story.append(edu_table)
            
            if degree:
                story.append(Paragraph(escape_html(degree), normal_style))
            
            if location and not duration:
                story.append(Paragraph(escape_html(location), normal_style))
            
            story.append(Spacer(1, 6))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF bytes
    if output_path is None:
        buffer.seek(0)
        pdf_bytes = buffer.read()
        buffer.close()
        return pdf_bytes
    else:
        return None


def generate_pdf_from_text(resume_text: str, output_path: str = None, resume_data: Dict = None) -> bytes:
    """
    Generate PDF from structured resume data ONLY.
    Does NOT use raw text - only structured data.
    
    Args:
        resume_text: ATS-optimized resume text (ignored if resume_data provided)
        output_path: Optional path to save PDF file
        resume_data: Structured resume dictionary (REQUIRED)
        
    Returns:
        PDF bytes
    """
    # STEP 4: REBUILD FROM STRUCTURED DATA ONLY
    # Never use raw text - only structured data
    if not resume_data:
        raise ValueError("resume_data is required. PDF generation requires structured data, not raw text.")
    
    return generate_pdf_from_structured_data(resume_data, output_path)
    # Create a BytesIO buffer to hold PDF in memory
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer if output_path is None else output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles for resume
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        spaceBefore=16,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        borderWidth=0,
        borderPadding=0
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        leading=14,
        fontName='Helvetica',
        alignment=TA_LEFT
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4,
        leading=14,
        leftIndent=20,
        fontName='Helvetica',
        alignment=TA_LEFT
    )
    
    # Parse resume text and convert to PDF elements
    lines = resume_text.split('\n')
    current_section = None
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        # Skip empty lines (but add small spacing)
        if not line:
            story.append(Spacer(1, 4))
            continue
        
        # Check if line is a separator (equals signs)
        if line.startswith('=') and len(line) > 10:
            # Skip separator lines, they're just visual
            continue
        
        # Check if line is a section heading (all caps, reasonable length, no bullets)
        if (line.isupper() and len(line) > 3 and len(line) < 50 and 
            not line.startswith('•') and 
            any(keyword in line for keyword in ['SUMMARY', 'SKILLS', 'EXPERIENCE', 'EDUCATION', 'CERTIFICATION', 'PROFESSIONAL'])):
            # Section heading
            story.append(Spacer(1, 12))
            story.append(Paragraph(line, heading_style))
            story.append(Spacer(1, 6))
            current_section = line
        
        # Check if line is a bullet point
        elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
            # Remove bullet character and format
            bullet_text = line[1:].strip()
            # Escape HTML special characters
            bullet_text = escape_html(bullet_text)
            story.append(Paragraph(f"• {bullet_text}", bullet_style))
        
        # Regular paragraph (but check if it looks like a heading)
        else:
            # Escape HTML special characters
            escaped_line = escape_html(line)
            # Use normal style for regular text
            story.append(Paragraph(escaped_line, normal_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF bytes
    if output_path is None:
        buffer.seek(0)
        pdf_bytes = buffer.read()
        buffer.close()
        return pdf_bytes
    else:
        return None


def escape_html(text: str) -> str:
    """
    Escape HTML special characters for ReportLab.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    # ReportLab uses XML/HTML-like syntax, so we need to escape special chars
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def create_pdf_file(resume_text: str, filename: str = "ats_resume.pdf") -> str:
    """
    Create PDF file from resume text.
    
    Args:
        resume_text: ATS-optimized resume text
        filename: Output filename
        
    Returns:
        Path to created PDF file
    """
    import tempfile
    import os
    
    # Create temporary file
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    # Generate PDF
    generate_pdf_from_text(resume_text, file_path)
    
    return file_path


