import logging
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts and returns the text content from a PDF file using PyPDF2.
    Includes validation to check if the text is readable and raises errors appropriately.
    """
    text_content = ""
    try:
        logger.info(f"Initiating text extraction from PDF: {pdf_path}")
        reader = PdfReader(pdf_path)
        
        if getattr(reader, "is_encrypted", False):
            raise ValueError(
                "The uploaded PDF is password-protected or encrypted. Please upload an unprotected PDF."
            )

        if not reader.pages:
            raise ValueError("The PDF file contains no pages.")

        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
        
        cleaned_text = text_content.strip()
        if not cleaned_text:
            logger.warning("Extracted text is empty. The PDF may be scanned or blank.")
            raise ValueError(
                "Could not extract readable text from the uploaded PDF. "
                "Please make sure it is a text-based PDF rather than a scanned image."
            )
            
        logger.info("PDF text extraction completed successfully.")
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
