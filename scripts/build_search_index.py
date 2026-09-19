"""
build_search_index.py
----------------------
Run this once (or whenever data/labelled_examples.json changes) to
(re)build the local FAISS similarity index that the app searches at
classification time.

Usage:
    python scripts/build_search_index.py
"""

import sys
import os

# Allow running this script directly from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.similarity_search import build_index_from_labelled_examples

if __name__ == "__main__":
    build_index_from_labelled_examples()
