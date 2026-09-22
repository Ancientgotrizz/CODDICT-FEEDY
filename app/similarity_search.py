"""
similarity_search.py
---------------------
Turns text into numbers (embeddings), stores those numbers in a
searchable local index (FAISS), and later finds the labelled examples
whose numbers are closest to a new piece of feedback's numbers.

Plain-English idea: an embedding is a list of 384 numbers that
represents the *meaning* of a sentence - like GPS coordinates, but for
meaning instead of location. Two sentences that mean similar things end
up with number-lists that are close together.

This is the "R" (Retrieval) in RAG: before asking the AI to classify
new feedback, we first fetch a few similar, already-labelled examples
and hand them to the AI as reference context.
"""

import os
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app import settings


def get_embeddings_model():
    """Loads the local MiniLM model that turns any text into a 384-number embedding."""
    return HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)


def build_index_from_labelled_examples():
    with open(settings.LABELLED_EXAMPLES_FILE, "r", encoding="utf-8") as f:
        examples = json.load(f)

    documents = []
    for example in examples:
        document = Document(
            page_content=example["text"],
            metadata={"label": example["label"]},
        )
        documents.append(document)

    embeddings_model = get_embeddings_model()
    vector_store = FAISS.from_documents(documents, embeddings_model)

    os.makedirs(settings.VECTOR_INDEX_DIR, exist_ok=True)
    vector_store.save_local(settings.VECTOR_INDEX_DIR)

    print(f"Saved a FAISS index with {len(documents)} labelled examples "
          f"to '{settings.VECTOR_INDEX_DIR}'")


def load_index():
    """Loads the FAISS index already saved to disk."""
    embeddings_model = get_embeddings_model()
    vector_store = FAISS.load_local(
        settings.VECTOR_INDEX_DIR,
        embeddings_model,
        allow_dangerous_deserialization=True,  # safe: we build this file ourselves
    )
    return vector_store


def find_similar_examples(vector_store, feedback_text, k=None):
    """
    Returns the k labelled examples most similar in meaning to feedback_text.
    Each result is a dict: {"text": ..., "label": ..., "score": ...}
    """
    if k is None:
        k = settings.RETRIEVAL_K

    results = vector_store.similarity_search_with_score(feedback_text, k=k)

    neighbours = []
    for document, score in results:
        neighbours.append({
            "text": document.page_content,
            "label": document.metadata.get("label", "Good"),
            "score": float(score),
        })
    return neighbours
