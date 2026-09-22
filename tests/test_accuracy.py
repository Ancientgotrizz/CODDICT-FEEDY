"""
test_accuracy.py
-----------------
Runs the classification pipeline against the generated sample PDFs and
compares the predicted category to the true category encoded in each PDF
filename. It prints the same summary to the terminal and persists the
latest result set so the dashboard can read it.

Usage:
    python tests/test_accuracy.py
"""

import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import settings
from app.database import save_accuracy_results
from app.similarity_search import load_index
from app.ai_classifier import classify_feedback
from app.confidence_score import fuse_confidence
from app.pdf_reader import extract_text

BUCKET_EDGES = [0.0, 0.5, 0.7, 0.85, 1.01]
BUCKET_LABELS = ["0.00-0.49", "0.50-0.69", "0.70-0.84", "0.85-1.00"]


def bucket_for(confidence):
    for i in range(len(BUCKET_EDGES) - 1):
        if BUCKET_EDGES[i] <= confidence < BUCKET_EDGES[i + 1]:
            return BUCKET_LABELS[i]
    return BUCKET_LABELS[-1]


def true_label_from_filename(filename):
    match = re.search(r"feedback_(.+?)_\d+\.pdf$", filename, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not parse category from filename: {filename}")
    return match.group(1).replace("_", " ")


def main():
    pdf_dir = settings.SAMPLE_PDFS_DIR
    vector_store = load_index()

    bucket_totals = {label: 0 for label in BUCKET_LABELS}
    bucket_correct = {label: 0 for label in BUCKET_LABELS}
    overall_correct = 0
    results = []

    for filename in sorted(os.listdir(pdf_dir)):
        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(pdf_dir, filename)
        text, _ = extract_text(pdf_path)
        if not text or not text.strip():
            print(f"[WARN] no text extracted from {filename}")
            continue

        result, neighbours, agreement = classify_feedback(vector_store, text)
        final_confidence = fuse_confidence(result.confidence, agreement)
        actual_label = true_label_from_filename(filename)
        is_correct = result.category == actual_label

        bucket = bucket_for(final_confidence)
        bucket_totals[bucket] += 1
        if is_correct:
            bucket_correct[bucket] += 1
            overall_correct += 1

        status = "OK  " if is_correct else "MISS"
        print(f"[{status}] predicted={result.category:<18} actual={actual_label:<18} confidence={final_confidence:.2f}")
        results.append({
            "filename": filename,
            "predicted": result.category,
            "actual": actual_label,
            "correct": is_correct,
            "confidence": final_confidence,
        })

    print("\nAccuracy by confidence bucket:")
    for label in BUCKET_LABELS:
        total = bucket_totals[label]
        if total == 0:
            print(f"  {label}: no examples in this bucket")
            continue
        accuracy = bucket_correct[label] / total
        print(f"  {label}: {bucket_correct[label]}/{total} correct ({accuracy:.0%})")

    overall_total = len(results)
    overall_accuracy = (overall_correct / overall_total) if overall_total else 0.0
    print(f"\nOverall: {overall_correct}/{overall_total} correct ({overall_accuracy:.0%})")

    per_category = {}
    categories = ["Excellent", "Good", "Need Improvements", "Poor"]
    for category in categories:
        category_results = [item for item in results if item["actual"] == category]
        correct = sum(1 for item in category_results if item["correct"])
        total = len(category_results)
        per_category[category] = {
            "correct": correct,
            "total": total,
            "accuracy": (correct / total) if total else 0.0,
        }

    latest_results = {
        "overall_accuracy": overall_accuracy,
        "correct": overall_correct,
        "total": overall_total,
        "per_category": per_category,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    save_accuracy_results(latest_results)

    print(f"\nSaved latest results to {settings.TEST_RESULTS_FILE}")


if __name__ == "__main__":
    main()