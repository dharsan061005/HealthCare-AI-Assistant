"""
PDF text extraction utility for Healthcare AI Assistant.
Uses pdfplumber for reliable text extraction from medical reports.
"""

import logging
from typing import Optional
import io

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF given its raw bytes.

    Args:
        file_bytes: Raw bytes of the uploaded PDF file.

    Returns:
        Extracted text as a single string, or an error message string on failure.
    """
    try:
        import pdfplumber
    except ImportError:
        return "⚠️ pdfplumber is not installed. Run: pip install pdfplumber"

    try:
        pages_text = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if len(pdf.pages) == 0:
                return "⚠️ The uploaded PDF has no pages."

            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(f"--- Page {i + 1} ---\n{text}")

        if not pages_text:
            return (
                "⚠️ No text could be extracted from this PDF. "
                "The file may be a scanned image PDF. "
                "OCR-based extraction is not supported in this version."
            )

        full_text = "\n\n".join(pages_text)
        logger.info("Extracted %d characters from %d pages.", len(full_text), len(pages_text))
        return full_text

    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        return f"⚠️ Failed to read PDF: {str(e)}"


def extract_text_from_uploaded_file(uploaded_file) -> str:
    """
    Extract text from a Streamlit UploadedFile object.

    Args:
        uploaded_file: A Streamlit UploadedFile (has .read() and .name).

    Returns:
        Extracted text string.
    """
    if uploaded_file is None:
        return "⚠️ No file provided."

    if not uploaded_file.name.lower().endswith(".pdf"):
        return "⚠️ Only PDF files are supported. Please upload a .pdf file."

    try:
        file_bytes = uploaded_file.read()
        if len(file_bytes) == 0:
            return "⚠️ The uploaded file is empty."
        return extract_text_from_pdf(file_bytes)
    except Exception as e:
        logger.error("Failed to read uploaded file: %s", e)
        return f"⚠️ Error reading file: {str(e)}"
