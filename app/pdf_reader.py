"""
pdf_reader.py
-------------
Step 1 of the pipeline: get text out of an uploaded PDF.

Tries the fast path first - reading the PDF's own built-in text layer
with pypdf. Only falls back to slow OCR (see ocr_reader.py) if that
fast path found basically nothing, which usually means the PDF is a
scanned photo instead of a real digital document.
"""

from pypdf import PdfReader
from app.ocr_reader import extract_text_with_ocr
from app import settings


def extract_digital_text(file_path_or_bytes):
    """Reads every page of a PDF and returns all the text as one string."""
    reader = PdfReader(file_path_or_bytes)
    all_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            all_text = all_text + page_text + "\n\f\n"
    return all_text


def extract_text(uploaded_file):
    """
    Tries the fast path first: read the PDF's own text layer with pypdf.
    If that comes back empty or suspiciously short, falls back to OCR.

    Returns a tuple: (extracted_text, used_ocr).
    """
    digital_text = extract_digital_text(uploaded_file)

    if len(digital_text.strip()) >= settings.MIN_DIGITAL_TEXT_CHARS:
        return digital_text, False

    # getvalue() reads the whole underlying buffer regardless of where
    # extract_digital_text() left the read position.
    pdf_bytes = uploaded_file.getvalue()
    ocr_text = extract_text_with_ocr(pdf_bytes)
    return ocr_text, True
