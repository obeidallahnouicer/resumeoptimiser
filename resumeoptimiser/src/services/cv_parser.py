"""
CV Parser: Extract and structure text from PDF documents.

Handles PDF parsing, section detection, and text normalization.
Supports both text-based and scanned (image-based) PDFs with OCR.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
except ImportError:
    convert_from_path = None
    pytesseract = None
    Image = None

logger = logging.getLogger("cv_parser")

# Common CV section headers (case-insensitive)
COMMON_SECTIONS = {
    "experience": [
        "work experience", "professional experience", "employment history",
        "career history", "experience", "professional background"
    ],
    "skills": [
        "skills", "technical skills", "core competencies", "competencies",
        "expertise", "areas of expertise"
    ],
    "education": [
        "education", "academic background", "qualification", "qualifications",
        "degrees", "certification", "certifications"
    ],
    "projects": [
        "projects", "selected projects", "key projects", "notable projects"
    ],
    "summary": [
        "summary", "professional summary", "objective", "about me", "profile",
        "executive summary"
    ],
    "languages": [
        "languages", "language skills"
    ],
    "certifications": [
        "certifications", "certificates", "licenses"
    ]
}


class CVParser:
    """Parse and structure CV content from PDF."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize CV parser.
        
        Args:
            pdf_path: Path to PDF file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If not a valid PDF or pdfplumber not available
        """
        self.pdf_path = Path(pdf_path)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if pdfplumber is None:
            raise ValueError("pdfplumber is not installed")
        
        logger.info(f"📄 Parsing CV: {self.pdf_path.name}")
    
    def extract_text(self) -> str:
        """
        Extract all text from PDF.
        Tries text extraction first, falls back to OCR for scanned PDFs.
        
        Returns:
            Full PDF text
        """
        try:
            # First try text extraction
            with pdfplumber.open(self.pdf_path) as pdf:
                text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        logger.debug(f"✓ Extracted text from page {page_num}")
            
            if text.strip():
                logger.info(f"✓ Successfully extracted text from {len(pdf.pages)} pages")
                return text
            
            # If no text found, try OCR
            logger.warning("⚠️  No text found in PDF - attempting OCR...")
            return self._extract_text_with_ocr()
            
        except Exception as e:
            logger.error(f"✗ Error in text extraction: {str(e)}")
            # Try OCR as fallback
            try:
                return self._extract_text_with_ocr()
            except Exception as ocr_error:
                logger.error(f"✗ OCR also failed: {str(ocr_error)}")
                raise
    
    def _extract_text_with_ocr(self) -> str:
        """
        Extract text from scanned PDF using OCR.
        
        Returns:
            Extracted text via Tesseract OCR
            
        Raises:
            RuntimeError: If OCR libraries not installed
        """
        if convert_from_path is None or pytesseract is None:
            raise RuntimeError(
                "OCR libraries not installed. Install with: "
                "pip install pytesseract pillow pdf2image"
            )
        
        try:
            logger.info("🔄 Converting PDF to images for OCR...")
            images = convert_from_path(str(self.pdf_path))
            
            full_text = ""
            for page_num, image in enumerate(images, 1):
                logger.debug(f"🔄 Running OCR on page {page_num}...")
                page_text = pytesseract.image_to_string(image)
                full_text += page_text + "\n"
                logger.debug(f"✓ OCR completed for page {page_num}")
            
            logger.info(f"✓ Successfully extracted text via OCR from {len(images)} pages")
            return full_text
            
        except Exception as e:
            logger.error(f"✗ OCR extraction failed: {str(e)}")
            raise RuntimeError(f"Failed to extract text via OCR: {str(e)}")
    
    def parse_sections(self) -> Dict[str, str]:
        """
        Parse CV into structured sections.
        
        Returns:
            Dict mapping section names to content
        """
        full_text = self.extract_text()
        return self._segment_text(full_text)
    
    def _segment_text(self, text: str) -> Dict[str, str]:
        """
        Segment text into CV sections.
        
        Args:
            text: Full CV text
            
        Returns:
            Dict of {section_name: section_text}
        """
        lines = text.split('\n')
        sections = {}
        current_section = "header"
        current_content = []
        
        for line in lines:
            detected_section = self._detect_section_header(line)
            
            if detected_section:
                # Save previous section
                if current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        sections[current_section] = content_text
                        logger.debug(f"✓ Parsed section: {current_section} ({len(content_text)} chars)")
                
                current_section = detected_section
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                sections[current_section] = content_text
        
        # If no sections detected, treat entire text as content
        if not sections or len(sections) == 1 and "header" in sections:
            logger.warning("⚠️  No CV sections detected - using full text as fallback")
            sections = {"content": text}
        
        logger.info(f"✓ CV segmented into {len(sections)} sections")
        return sections
    
    def _detect_section_header(self, line: str) -> Optional[str]:
        """
        Detect if line is a section header.
        
        Args:
            line: Line to check
            
        Returns:
            Section name if header detected, None otherwise
        """
        line_lower = line.strip().lower()
        
        # Skip empty lines or very long lines (likely content)
        if not line.strip() or len(line) > 100:
            return None
        
        # Check against known section headers
        for section_name, patterns in COMMON_SECTIONS.items():
            for pattern in patterns:
                # More flexible matching - check if line contains pattern
                if line_lower == pattern or pattern in line_lower:
                    return section_name
        
        return None
    
    def extract_bullets(self, section_text: str) -> List[str]:
        """
        Extract bullet points from section text.
        
        Args:
            section_text: Text content of a section
            
        Returns:
            List of bullet point strings
        """
        bullets = []
        lines = section_text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Check for common bullet point markers
            if re.match(r'^[•\-\*\s]+', line) or re.match(r'^\d+\.\s', line):
                # Remove bullet marker
                clean_line = re.sub(r'^[•\-\*\d\.\s]+', '', line).strip()
                if clean_line:
                    bullets.append(clean_line)
        
        logger.debug(f"Extracted {len(bullets)} bullet points")
        return bullets
    
    def extract_contact_info(self, header_text: str) -> Dict[str, str]:
        """
        Extract contact information from header.
        
        Args:
            header_text: Header/summary section text
            
        Returns:
            Dict with extracted contact info
        """
        info = {}
        
        # Extract email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', header_text)
        if email_match:
            info['email'] = email_match.group(1)
        
        # Extract phone
        phone_match = re.search(r'(\+?[\d\s\-\(\)]{10,})', header_text)
        if phone_match:
            info['phone'] = phone_match.group(1).strip()
        
        # Extract URL/LinkedIn
        url_match = re.search(r'(?:https?://)?(?:www\.)?(?:linkedin\.com/in/)?[\w\-]+', header_text)
        if url_match:
            info['url'] = url_match.group(0)
        
        return info
    
    def get_structured_cv(self) -> Dict[str, any]:
        """
        Get fully structured CV data.
        
        Returns:
            Dict with sections, bullets, and metadata
        """
        sections = self.parse_sections()
        
        structured = {
            "raw_text": self.extract_text(),
            "sections": sections,
            "bullets": {},
            "contact_info": self.extract_contact_info(
                sections.get("header", "") + "\n" + sections.get("summary", "")
            )
        }
        
        # Extract bullets from key sections
        for section_name in ["experience", "projects", "skills"]:
            if section_name in sections:
                structured["bullets"][section_name] = self.extract_bullets(
                    sections[section_name]
                )
        
        logger.info("✓ CV structure complete")
        return structured
