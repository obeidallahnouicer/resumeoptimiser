"""CV Rewriter - Uses LLM + profile.md to create polished LaTeX resume."""

import json
import logging
import re
from typing import Optional
from dataclasses import dataclass

from src.services.llm_service import get_llm_service

logger = logging.getLogger("cv_rewriter")


def sanitize_for_latex(text: str) -> str:
    """Sanitize text for LaTeX - escape special characters and handle Unicode."""
    if not text:
        return ""
    
    # Remove markdown code fences and other problematic markers
    text = re.sub(r'```\w*\n?', '', text)  # Remove ```python, ```json, ``` etc
    text = text.replace('`', '')  # Remove single backticks
    
    # Remove emoji and other problematic Unicode characters
    # Keep only ASCII printable chars + common accented chars used in names
    cleaned = []
    for c in text:
        code = ord(c)
        # Keep ASCII printables, newlines, tabs, common accents (À-ÿ for European names)
        if (code >= 32 and code < 127) or c in '\n\t\r' or (code >= 192 and code <= 255):
            cleaned.append(c)
        elif code < 32:  # Remove control characters
            continue
        else:  # Skip other Unicode (emoji, symbols, etc)
            continue
    text = ''.join(cleaned)
    
    # Escape LaTeX special characters
    replacements = {
        '\\': '\\textbackslash{}',
        '{': '\\{',
        '}': '\\}',
        '$': '\\$',
        '&': '\\&',
        '#': '\\#',
        '^': '\\textasciicircum{}',
        '_': '\\_',
        '~': '\\textasciitilde{}',
        '%': '\\%',
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text


def sanitize_latex_output(latex_text: str) -> str:
    """
    Sanitize LaTeX output from LLM to escape unescaped special characters.
    This ensures the LLM's LaTeX is valid and can be compiled.
    """
    if not latex_text:
        return ""
    
    # Remove any markdown code fences the LLM might have added
    latex_text = re.sub(r'```[a-z]*\n?', '', latex_text)
    latex_text = latex_text.rstrip('`')
    
    # Remove problematic Unicode characters and emoji (keep only ASCII + European accents)
    latex_text = ''.join(c for c in latex_text if ord(c) < 128 or (192 <= ord(c) <= 255))
    
    # Escape ampersands that aren't already escaped
    # Match & that aren't preceded by \ and aren't part of escaped sequences
    latex_text = re.sub(r'(?<!\\)&', r'\\&', latex_text)
    
    return latex_text


@dataclass
class CVSection:
    """Represents a section of a rewritten CV."""
    title: str
    content: str  # LaTeX formatted content


class CVRewriter:
    """Rewrites CV using LLM for professional polish."""

    def __init__(self):
        """Initialize CV rewriter."""
        self.llm = get_llm_service()
        logger.info("✓ CV rewriter initialized")

    def rewrite_cv(
        self,
        profile_md: str,
        job_description: Optional[str] = None
    ) -> str:
        """
        Rewrite CV using LLM to create polished LaTeX resume.
        
        Args:
            profile_md: Profile markdown content
            job_description: Optional JD to tailor CV
            
        Returns:
            LaTeX formatted CV content
        """
        logger.info("🧠 Starting CV rewrite with LLM...")
        
        # Step 1: Extract structured data from profile
        structured_data = self._extract_structured_data(profile_md)
        logger.info("✓ Extracted structured data from profile")
        
        # Step 2: Use LLM to polish and enhance each section
        polished_sections = self._polish_sections(structured_data, job_description)
        logger.info(f"✓ Polished {len(polished_sections)} sections with LLM")
        
        # Step 3: Generate LaTeX template
        latex_content = self._generate_latex_template(polished_sections, structured_data)
        logger.info("✓ Generated LaTeX template")
        
        return latex_content

    def _extract_structured_data(self, profile_md: str) -> dict:
        """
        Extract structured data from profile.md.
        
        Returns dict with sections: education, experience, skills, projects, etc.
        """
        prompt = f"""Extract structured data from this profile markdown.
Return a JSON object with these sections (include only sections that exist):
{{
    "name": "Full name",
    "contact": {{"email": "...", "phone": "..."}},
    "education": [
        {{"degree": "...", "institution": "...", "focus": "..."}}
    ],
    "experience": [
        {{
            "title": "...",
            "company": "...",
            "duration": "...",
            "description": "...",
            "achievements": ["...", "..."]
        }}
    ],
    "skills": {{
        "technical": ["...", "..."],
        "soft": ["...", "..."],
        "tools": ["...", "..."]
    }},
    "projects": [
        {{
            "name": "...",
            "description": "...",
            "technologies": ["...", "..."],
            "achievements": ["...", "..."]
        }}
    ]
}}

Profile Markdown:
{profile_md}

Return ONLY valid JSON."""

        try:
            logger.info("🔧 Calling LLM to extract structured data...")
            response = self.llm.generate(prompt, max_tokens=3000, temperature=0.2)
            logger.info(f"📝 LLM response length: {len(response) if response else 0} chars")
            
            # Try to parse JSON
            if not response or not response.strip():
                logger.warning("⚠️  LLM returned empty response - using defaults")
                return self._default_structured_data()
            
            logger.info(f"📝 Response preview: {response[:200]}...")
            
            # First try direct parsing
            try:
                data = json.loads(response)
                logger.info("✓ Parsed profile structure successfully")
                return data
            except json.JSONDecodeError:
                logger.debug("Direct JSON parse failed, trying extraction...")
            
            # Try to extract JSON from markdown code blocks or wrapped text
            # Remove markdown code fences first
            cleaned = response.replace('```json', '').replace('```', '')
            cleaned = cleaned.strip()
            
            if cleaned:
                try:
                    data = json.loads(cleaned)
                    logger.info("✓ Extracted JSON from markdown-wrapped response")
                    return data
                except json.JSONDecodeError:
                    logger.debug("Cleaned JSON parse failed, trying regex...")
            
            # Try regex to find JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    logger.info("✓ Extracted JSON via regex from response")
                    return data
                except json.JSONDecodeError as ex:
                    logger.warning(f"Regex extraction failed: {ex}")
            
            logger.warning("Returning default structured data due to extraction failure")
            logger.error(f"Could not parse response: {response[:500]}")
            return self._default_structured_data()
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}", exc_info=True)
            return self._default_structured_data()
    
    def _default_structured_data(self) -> dict:
        """Return default/empty structured data."""
        return {
            "name": "Professional",
            "contact": {"email": "", "phone": ""},
            "education": [],
            "experience": [],
            "skills": {"technical": [], "soft": [], "tools": []},
            "projects": []
        }

    def _polish_sections(
        self,
        structured_data: dict,
        job_description: Optional[str] = None
    ) -> list:
        """
        Use LLM to polish each section for professional presentation.
        
        Returns list of CVSection objects.
        """
        sections = []
        
        if "education" in structured_data:
            education_latex = self._polish_education(structured_data["education"])
            sections.append(CVSection("EDUCATION", sanitize_latex_output(education_latex)))
        
        if "experience" in structured_data:
            experience_latex = self._polish_experience(
                structured_data["experience"],
                job_description
            )
            sections.append(CVSection("PROFESSIONAL EXPERIENCE", sanitize_latex_output(experience_latex)))
        
        if "projects" in structured_data:
            projects_latex = self._polish_projects(structured_data["projects"])
            sections.append(CVSection("PROJECTS", sanitize_latex_output(projects_latex)))
        
        if "skills" in structured_data:
            skills_latex = self._polish_skills(structured_data["skills"])
            sections.append(CVSection("SKILLS", sanitize_latex_output(skills_latex)))
        
        return sections

    def _polish_education(self, education_list: list) -> str:
        """Polish education section using LLM."""
        prompt = f"""Format this education data into professional LaTeX bullet points.
Use strong action verbs and highlight achievements. Each entry should be 1-2 lines max.

Education data:
{json.dumps(education_list, indent=2)}

Return LaTeX code (bullet points using \\item) that looks professional and concise.
Only return the LaTeX code, no other text."""

        try:
            latex = self.llm.generate(prompt, max_tokens=500, temperature=0.3)
            return latex
        except Exception as e:
            logger.error(f"Error polishing education: {e}")
            return self._fallback_education_latex(education_list)

    def _polish_experience(
        self,
        experience_list: list,
        job_description: Optional[str] = None
    ) -> str:
        """Polish experience section using LLM."""
        jd_context = f"\nFocus on these job requirements:\n{job_description}" if job_description else ""
        
        prompt = f"""Rewrite this professional experience into powerful LaTeX bullet points.
Use strong action verbs. Quantify achievements where possible.
Each job should have 3-5 bullet points highlighting impact and skills.
Format: Use \\item for bullets under each position.{jd_context}

Experience data:
{json.dumps(experience_list, indent=2)}

Return only the LaTeX code with properly formatted bullet points."""

        try:
            latex = self.llm.generate(prompt, max_tokens=1000, temperature=0.3)
            return latex
        except Exception as e:
            logger.error(f"Error polishing experience: {e}")
            return self._fallback_experience_latex(experience_list)

    def _polish_projects(self, projects_list: list) -> str:
        """Polish projects section using LLM."""
        prompt = f"""Format these projects into professional LaTeX entries.
Highlight impact, technologies, and achievements.
Each project: Title, brief description, key achievements.
Format: Use \\item for each entry.

Projects data:
{json.dumps(projects_list, indent=2)}

Return only the LaTeX code."""

        try:
            latex = self.llm.generate(prompt, max_tokens=1000, temperature=0.3)
            return latex
        except Exception as e:
            logger.error(f"Error polishing projects: {e}")
            return self._fallback_projects_latex(projects_list)

    def _polish_skills(self, skills_dict: dict) -> str:
        """Polish skills section using LLM."""
        prompt = f"""Format these skills into professional LaTeX entries.
Group by category (Technical, Soft Skills, Tools).
Format each group as: \\textbf{{Category:}} skill1, skill2, skill3

Skills data:
{json.dumps(skills_dict, indent=2)}

Return only the LaTeX code."""

        try:
            latex = self.llm.generate(prompt, max_tokens=500, temperature=0.2)
            return latex
        except Exception as e:
            logger.error(f"Error polishing skills: {e}")
            return self._fallback_skills_latex(skills_dict)

    def _generate_latex_template(self, sections: list, structured_data: dict) -> str:
        """Generate complete LaTeX resume template."""
        # DON'T sanitize section.content - it's already valid LaTeX from LLM
        # Only sanitize the title which is plain text
        sections_content = "\n\n".join([
            f"\\section{{{sanitize_for_latex(section.title)}}}\n{section.content}"
            for section in sections
        ])

        name = sanitize_for_latex(structured_data.get("name", "Obeid Allahnouicer"))
        email = sanitize_for_latex(structured_data.get("contact", {}).get("email", "obeidallahnouicer@gmail.com"))

        latex = f"""\\documentclass[11pt]{{article}}
\\usepackage[margin=0.5in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{xcolor}}

\\definecolor{{darkblue}}{{rgb}}{{0.1, 0.2, 0.4}}
\\definecolor{{accent}}{{rgb}}{{0.2, 0.4, 0.8}}

\\pagestyle{{empty}}

\\newcommand{{\\sectiontitle}}[1]{{%
    \\vspace{{8pt}}%
    {{\\fontsize{{13}}{{15}}\\selectfont \\textbf{{\\textcolor{{darkblue}}{{#1}}}}}}%
    \\vspace{{6pt}}%
    {{\\color{{accent}}\\rule{{\\textwidth}}{{0.5pt}}}}%
    \\vspace{{4pt}}%
}}

\\renewcommand{{\\section}}[1]{{\\sectiontitle{{#1}}}}

\\begin{{document}}

\\begin{{center}}
{{\\fontsize{{18}}{{20}}\\selectfont \\textbf{{\\textcolor{{darkblue}}{{{name}}}}}}}\\\\
\\vspace{{2pt}}
Full Stack AI Software Engineer | Data Scientist | LLM Systems\\\\
\\vspace{{2pt}}
\\href{{mailto:{email}}}{{Email: {email}}} | LinkedIn
\\end{{center}}

\\vspace{{8pt}}

{sections_content}

\\end{{document}}"""

        return latex

    def _fallback_education_latex(self, education_list: list) -> str:
        """Fallback education formatting."""
        lines = ["\\begin{itemize}"]
        for edu in education_list:
            degree = sanitize_for_latex(str(edu.get('degree', 'Degree')))
            institution = sanitize_for_latex(str(edu.get('institution', 'Institution')))
            lines.append(f"\\item \\textbf{{{degree}}} -- {institution}")
            if edu.get('focus'):
                focus = sanitize_for_latex(str(edu.get('focus')))
                lines.append(f"  Focus: {focus}")
        lines.append("\\end{itemize}")
        return "\n".join(lines)

    def _fallback_experience_latex(self, experience_list: list) -> str:
        """Fallback experience formatting."""
        lines = ["\\begin{itemize}"]
        for exp in experience_list:
            title = sanitize_for_latex(str(exp.get('title', 'Position')))
            company = sanitize_for_latex(str(exp.get('company', '')))
            lines.append(f"\\item \\textbf{{{title}}} at {company}")
            if exp.get('achievements'):
                for achievement in exp.get('achievements', []):
                    achievement_text = sanitize_for_latex(str(achievement))
                    lines.append(f"  \\item {achievement_text}")
        lines.append("\\end{itemize}")
        return "\n".join(lines)

    def _fallback_projects_latex(self, projects_list: list) -> str:
        """Fallback projects formatting."""
        lines = ["\\begin{itemize}"]
        for proj in projects_list:
            name = sanitize_for_latex(str(proj.get('name', 'Project')))
            description = sanitize_for_latex(str(proj.get('description', '')))
            lines.append(f"\\item \\textbf{{{name}}} -- {description}")
            if proj.get('technologies'):
                tech_list = ", ".join(sanitize_for_latex(str(t)) for t in proj.get('technologies', []))
                lines.append(f"  Tech: {tech_list}")
        lines.append("\\end{itemize}")
        return "\n".join(lines)

    def _fallback_skills_latex(self, skills_dict: dict) -> str:
        """Fallback skills formatting."""
        lines = []
        for category, skills in skills_dict.items():
            if isinstance(skills, list):
                category_text = sanitize_for_latex(str(category.title()))
                skills_text = ", ".join(sanitize_for_latex(str(s)) for s in skills)
                lines.append(f"\\textbf{{{category_text}:}} {skills_text}")
        return "\n\n".join(lines)


_cv_rewriter: Optional[CVRewriter] = None


def get_cv_rewriter() -> CVRewriter:
    """Get or create CV rewriter instance."""
    global _cv_rewriter
    if _cv_rewriter is None:
        _cv_rewriter = CVRewriter()
    return _cv_rewriter
