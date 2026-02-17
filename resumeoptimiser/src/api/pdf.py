"""API routes for PDF compilation."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from src.models.schemas import CompilePDFRequest
from src.services.pdf_compiler import compile_latex_to_pdf

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.post("/compile")
async def compile_pdf_endpoint(request: CompilePDFRequest):
    """
    Compile LaTeX content to PDF.
    Returns PDF file or error details.
    """
    try:
        success, pdf_path, error_msg = compile_latex_to_pdf(request.latex_content)

        if not success:
            raise HTTPException(status_code=500, detail=f"LaTeX compilation failed: {error_msg}")

        return FileResponse(pdf_path, media_type="application/pdf", filename="cv.pdf")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compiling PDF: {str(e)}")