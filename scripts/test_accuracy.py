"""
test_accuracy.py
-----------------
A diagnostic script (not part of the live app). Runs the full
classification pipeline against the holdout set - labelled examples the
similarity search has never seen before - and checks: when Feedy says
it's more confident, is it actually more often correct?

Usage:
    python scripts/test_accuracy.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import settings
from app.similarity_search import load_index
from app.ai_classifier import classify_feedback
from app.confidence_score import fuse_confidence

BUCKET_EDGES = [0.0, 0.5, 0.7, 0.85, 1.01]
BUCKET_LABELS = ["0.00-0.49", "0.50-0.69", "0.70-0.84", "0.85-1.00"]


def bucket_for(confidence):
    for i in range(len(BUCKET_EDGES) - 1):
        if BUCKET_EDGES[i] <= confidence < BUCKET_EDGES[i + 1]:
            return BUCKET_LABELS[i]
    return BUCKET_LABELS[-1]


def main():
    with open(settings.HOLDOUT_EXAMPLES_FILE, "r", encoding="utf-8") as f:
        holdout_examples = json.load(f)

    vector_store = load_index()

    bucket_totals = {label: 0 for label in BUCKET_LABELS}
    bucket_correct = {label: 0 for label in BUCKET_LABELS}
    overall_correct = 0

    for example in holdout_examples:
        result, neighbours, agreement = classify_feedback(vector_store, example["text"])
        final_confidence = fuse_confidence(result.confidence, agreement)

        is_correct = result.category == example["label"]
        bucket = bucket_for(final_confidence)
        bucket_totals[bucket] += 1
        if is_correct:
            bucket_correct[bucket] += 1
            overall_correct += 1

        status = "OK  " if is_correct else "MISS"
        print(f"[{status}] predicted={result.category:<18} "
              f"actual={example['label']:<18} confidence={final_confidence:.2f}")

    print("\nAccuracy by confidence bucket:")
    for label in BUCKET_LABELS:
        total = bucket_totals[label]
        if total == 0:
            print(f"  {label}: no examples in this bucket")
            continue
        accuracy = bucket_correct[label] / total
        print(f"  {label}: {bucket_correct[label]}/{total} correct ({accuracy:.0%})")

    overall_total = len(holdout_examples)
    print(f"\nOverall: {overall_correct}/{overall_total} correct "
          f"({overall_correct / overall_total:.0%})")


if __name__ == "__main__":
    main()
