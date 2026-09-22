"""Persistence for the latest accuracy evaluation summary."""

import json
import os
from datetime import datetime
from app import settings
def load_accuracy_results():
    """Loads persisted accuracy-test results, returning zero-values when absent."""
    default_results = {
        "overall_accuracy": 0.0,
        "correct": 0,
        "total": 0,
        "per_category": {
            "Excellent": {"correct": 0, "total": 0, "accuracy": 0.0},
            "Good": {"correct": 0, "total": 0, "accuracy": 0.0},
            "Need Improvements": {"correct": 0, "total": 0, "accuracy": 0.0},
            "Poor": {"correct": 0, "total": 0, "accuracy": 0.0},
        },
        "generated_at": None,
    }

    if not os.path.exists(settings.TEST_RESULTS_FILE):
        return default_results

    try:
        with open(settings.TEST_RESULTS_FILE, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        for category in default_results["per_category"]:
            loaded.setdefault("per_category", {}).setdefault(category, {"correct": 0, "total": 0, "accuracy": 0.0})
        loaded.setdefault("overall_accuracy", 0.0)
        loaded.setdefault("correct", 0)
        loaded.setdefault("total", 0)
        loaded.setdefault("generated_at", None)
        return loaded
    except (json.JSONDecodeError, OSError):
        return default_results


def save_accuracy_results(results):
    """Stores the latest accuracy-test results so the dashboard can read them."""
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    with open(settings.TEST_RESULTS_FILE, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
