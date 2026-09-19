"""
settings.py
-----------
One single place that holds every configurable value for the whole app.
Every other file imports from this one instead of hard-coding values.
"""

import os
from dotenv import load_dotenv

# Load the .env file into memory as soon as this module is imported.
load_dotenv()

# --- Ollama (local LLM) settings ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "160"))

# --- Local embedding model (sentence-transformers, no API key needed) ---
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)

# --- File locations ---
DATA_DIR = "data"
VECTOR_INDEX_DIR = "vector_index"
LABELLED_EXAMPLES_FILE = os.path.join(DATA_DIR, "labelled_examples.json")
HOLDOUT_EXAMPLES_FILE = os.path.join(DATA_DIR, "holdout_examples.json")
FEEDBACK_RECORDS_FILE = os.path.join(DATA_DIR, "feedback_records.csv")
SAMPLE_PDFS_DIR = os.path.join(DATA_DIR, "sample_pdfs")

# --- Behaviour settings ---
RETRIEVAL_K = 3            # how many similar labelled examples to retrieve
REVIEW_THRESHOLD = 0.6     # confidence below this gets flagged "needs review"
ALERT_THRESHOLD = 0.8      # high-confidence Poor results trigger an alert
MIN_DIGITAL_TEXT_CHARS = 20  # below this, assume the PDF is a scan and use OCR
OCR_EXTRACTION_QUALITY = 0.75   # trust penalty applied when OCR text was used
DIGITAL_EXTRACTION_QUALITY = 1.0  # full trust when the PDF had a real text layer
