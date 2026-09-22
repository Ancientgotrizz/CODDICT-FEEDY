# Feedy — AI-Powered Satisfaction Analysis from PDF Feedback Forms

Feedy is a local web app that reads a customer feedback PDF, classifies
it into one of four categories, explains its reasoning, and shows a
confidence score — all running on your own machine, with no cloud AI
and no API key.

**Categories:** Excellent · Good · Need Improvements · Poor

## How it works (short version)

1. You upload a feedback PDF.
2. Feedy reads the text out of it (with an OCR fallback for scans).
3. The messy text is cleaned into one clear block of customer feedback.
4. Feedy searches a small local library of already-labelled examples
   for the 3 most similar ones (this is "RAG" — Retrieval-Augmented
   Generation).
5. A local AI model (Ollama, running Llama 3.1) reads the new feedback
   plus those 3 examples, and returns a category, a confidence score,
   a plain-language reason, and a few evidence phrases.
6. Three confidence signals are blended into one final trust score.
7. The result is saved to a CSV file, and shown on a dashboard with
   charts and trends.

## Project structure

```
feedy/
├── app/
│   ├── main.py               # the Streamlit app (2 pages: Upload, Dashboard)
│   ├── settings.py           # every configurable value, in one place
│   ├── schemas.py            # the strict shape the AI's answer must fit
│   ├── pdf_reader.py         # gets text out of a PDF (digital-text path)
│   ├── ocr_reader.py         # OCR fallback for scanned PDFs
│   ├── text_cleaner.py       # strips form labels, keeps real answers
│   ├── similarity_search.py  # FAISS + embeddings similarity search
│   ├── ai_classifier.py      # builds the prompt, calls the AI model
│   ├── confidence_score.py   # blends 3 signals into 1 confidence number
│   └── database.py           # persists the latest evaluation summary
├── scripts/
│   ├── build_search_index.py    # (re)builds the FAISS index
│   └── generate_sample_pdfs.py  # makes synthetic demo PDFs
├── tests/
│   └── test_accuracy.py         # measures confidence vs. real accuracy
├── data/
│   ├── labelled_examples.json   # 300 unique generic examples for search
│   └── sample_pdfs/             # created by generate_sample_pdfs.py
├── vector_index/              # the saved FAISS index (created by build_search_index.py)
├── requirements.txt
├── .env.example
├── STARTUP_COMMANDS.md        # every command you need, in order
└── README.md
```

## Getting started

See **STARTUP_COMMANDS.md** for the exact commands to run, in order.

## Honest limitations

- This is a local prototype with no user accounts or cloud services.
- The confidence score is an engineering estimate, not a statistically
  calibrated probability.
- OCR needs Tesseract and Poppler installed separately as system tools
  — without them, only PDFs with a real text layer will work.
