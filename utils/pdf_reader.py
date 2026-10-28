import logging
from typing import Tuple
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

logger = logging.getLogger(__name__)

# Constants for document processing limits
MAX_PDF_PAGES = 10
MAX_RESUME_TEXT_CHARS = 25000
MIN_RESUME_TEXT_CHARS = 50
MIN_RESUME_WORD_COUNT = 10


def validate_resume_text(text: str) -> Tuple[bool, str]:
    """
    Validates whether resume text satisfies length, word count, and content criteria.
    Returns (is_valid, error_message).
    """
    if not text or not text.strip():
        return False, "Resume content cannot be empty. Please provide your resume details."

    cleaned = text.strip()
    if len(cleaned) < MIN_RESUME_TEXT_CHARS:
        return False, f"Resume content is too short (minimum {MIN_RESUME_TEXT_CHARS} characters required for analysis)."

    words = [w for w in cleaned.split() if w.strip()]
    if len(words) < MIN_RESUME_WORD_COUNT:
        return False, f"Resume content must contain at least {MIN_RESUME_WORD_COUNT} words (education, skills, or experience)."

    return True, ""


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts and returns text content from a PDF file using PyPDF2.
    Enforces maximum page limits, verifies encryption status, and validates extracted text.
    """
    text_content = ""
    try:
        logger.info(f"Initiating text extraction from PDF: {pdf_path}")
        reader = PdfReader(pdf_path)
        
        if getattr(reader, "is_encrypted", False):
            raise ValueError(
                "The uploaded PDF is password-protected or encrypted. Please upload an unprotected PDF."
            )

        num_pages = len(reader.pages)
        if num_pages == 0:
            raise ValueError("The PDF file contains no readable pages.")

        if num_pages > MAX_PDF_PAGES:
            raise ValueError(
                f"The uploaded PDF contains {num_pages} pages, exceeding the {MAX_PDF_PAGES}-page limit for resumes. "
                "Please upload a standard concise campus placement resume."
            )

        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
        
        cleaned_text = text_content.strip()
        is_valid, validation_msg = validate_resume_text(cleaned_text)
        if not is_valid:
            logger.warning(f"Extracted PDF text validation failed: {validation_msg}")
            raise ValueError(
                f"Could not extract sufficient text from PDF: {validation_msg} "
                "Ensure your document is a text-based PDF rather than a scanned image."
            )

        # Enforce maximum character boundary to avoid excessive token consumption
        if len(cleaned_text) > MAX_RESUME_TEXT_CHARS:
            logger.warning(
                f"PDF text length ({len(cleaned_text)} chars) exceeded limit. Truncating to {MAX_RESUME_TEXT_CHARS} chars."
            )
            cleaned_text = cleaned_text[:MAX_RESUME_TEXT_CHARS]
            
        logger.info(f"PDF text extraction completed successfully ({len(cleaned_text)} characters).")
        return cleaned_text

    except FileNotFoundError:
        logger.error(f"File not found: {pdf_path}")
        raise FileNotFoundError(f"Resume file was not found at path: {pdf_path}")
    except ValueError as ve:
        logger.error(f"Validation error reading PDF: {str(ve)}")
        raise ve
    except PdfReadError as pre:
        logger.error(f"PyPDF2 ReadError encountered: {str(pre)}")
        raise ValueError(f"Could not read PDF file (corrupted or malformed): {str(pre)}")
    except Exception as e:
        logger.error(f"Unexpected error reading PDF: {str(e)}")
        raise RuntimeError(f"Failed to parse PDF file: {str(e)}")
