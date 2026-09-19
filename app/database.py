"""
database.py
------------
Feedy's entire database is one CSV file on disk. This module knows how
to read it and append a new row to it.

NOTE: the original prototype displayed the AI's flagged keywords on
screen but never saved them to the CSV, so they were lost as soon as
you left that screen. This version fixes that by adding a
flagged_keywords column, so the dashboard and history can show them too.
"""

import os
from datetime import datetime
import pandas as pd
from app import settings

COLUMN_NAMES = [
    "timestamp", "source_file", "feedback_text", "category",
    "llm_confidence", "neighbour_agreement", "final_confidence",
    "rationale", "flagged_keywords", "needs_review",
]


def load_records():
    """
    Returns all saved records as a pandas DataFrame. If the file does not
    exist yet, returns an empty DataFrame with the right columns so the
    rest of the app never has to special-case a missing file.
    """
    if not os.path.exists(settings.FEEDBACK_RECORDS_FILE):
        return pd.DataFrame(columns=COLUMN_NAMES)
    return pd.read_csv(settings.FEEDBACK_RECORDS_FILE)


def save_record(source_file, feedback_text, category, llm_confidence,
                 neighbour_agreement, final_confidence, rationale, flagged_keywords):
    """Appends one new row to data/feedback_records.csv."""
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    existing_records = load_records()

    new_row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source_file": source_file,
        "feedback_text": feedback_text,
        "category": category,
        "llm_confidence": llm_confidence,
        "neighbour_agreement": neighbour_agreement,
        "final_confidence": final_confidence,
        "rationale": rationale,
        "flagged_keywords": ", ".join(flagged_keywords) if flagged_keywords else "",
        "needs_review": final_confidence < settings.REVIEW_THRESHOLD,
    }

    new_row_df = pd.DataFrame([new_row])
    updated_records = pd.concat([existing_records, new_row_df], ignore_index=True)
    updated_records.to_csv(settings.FEEDBACK_RECORDS_FILE, index=False)

    return new_row
