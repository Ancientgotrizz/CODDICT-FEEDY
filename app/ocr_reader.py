"""
ocr_reader.py
-------------
Fallback path for feedback PDFs that are really just photos/scans with
no real text layer. Turns each page into an image and runs OCR
(Optical Character Recognition) on it.

Needs two system packages that pip cannot install on its own:
  - tesseract-ocr  (the OCR engine itself)
  - poppler-utils  (lets pdf2image rasterise PDF pages into images)

If those two tools are not installed on the machine, this file will
raise an error when called - the code path is real, it just needs
those system tools present to work.
"""
import os
from pdf2image import convert_from_bytes
import pytesseract


def extract_text_with_ocr(pdf_bytes):
    """Rasterises every page of a PDF into an image and runs Tesseract OCR on each one."""
    pages = convert_from_bytes(pdf_bytes)
    all_text = ""
    for page_image in pages:
        page_text = pytesseract.image_to_string(page_image)
        if page_text:
            all_text = all_text + page_text + "\n"
    return all_text
