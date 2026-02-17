"""PDF compilation service."""

import subprocess
from pathlib import Path
from typing import Tuple

from src.core.config import BUILD_DIR, LATEX_TIMEOUT, LATEX_INTERACTION_MODE, ensure_build_dir


def compile_latex_to_pdf(
    latex_content: str,
    output_name: str = "cv"
) -> Tuple[bool, str, str]:
    """
    Compile LaTeX content to PDF using pdflatex.

    Args:
        latex_content: LaTeX document content
        output_name: Name for output PDF file

    Returns:
        Tuple of (success, pdf_path, error_message)
    """
    ensure_build_dir()

    # Write LaTeX to file
    latex_file = BUILD_DIR / f"{output_name}.tex"
    latex_file.write_text(latex_content)

    try:
        # Run pdflatex
        result = subprocess.run(
            [
                "pdflatex",
                f"-interaction={LATEX_INTERACTION_MODE}",
                "-output-directory", str(BUILD_DIR),
                str(latex_file)
            ],
            capture_output=True,
            text=True,
            timeout=LATEX_TIMEOUT
        )

        if result.returncode != 0:
            return False, "", result.stderr or result.stdout

        pdf_path = BUILD_DIR / f"{output_name}.pdf"
        if pdf_path.exists():
            return True, str(pdf_path), ""
        else:
            return False, "", "PDF file not generated"

    except subprocess.TimeoutExpired:
        return False, "", "LaTeX compilation timed out"
    except FileNotFoundError:
        return False, "", "pdflatex not found. Install TeX Live to compile LaTeX."
    except Exception as e:
        return False, "", str(e)


def validate_pdf_content(pdf_path: str, keywords: list) -> Tuple[bool, list]:
    """
    Validate PDF content contains emphasized keywords.

    Args:
        pdf_path: Path to PDF file
        keywords: Keywords to search for

    Returns:
        Tuple of (all_keywords_found, missing_keywords)
    """
    try:
        result = subprocess.run(
            ["pdftotext", pdf_path, "-"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return False, ["Could not extract text from PDF"]

        pdf_text = result.stdout.lower()
        missing_keywords = [
            kw for kw in keywords
            if kw.lower() not in pdf_text
        ]

        return len(missing_keywords) == 0, missing_keywords

    except FileNotFoundError:
        return True, []  # Skip validation if pdftotext not available
    except Exception as e:
        return False, [str(e)]