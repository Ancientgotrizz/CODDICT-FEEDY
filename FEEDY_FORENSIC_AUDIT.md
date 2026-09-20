# FEEDY FORENSIC REPOSITORY AUDIT

**Audit date:** 2026-09-20  
**Mode:** Read-only forensic audit  
**Repository changes during audit:** No application code, dependencies, prompts, models, production data, CSV, FAISS files, or configuration were intentionally modified.

## Evidence Labels

- **[PROVEN]** Verified directly from source, installed metadata, command output, or controlled runtime testing.
- **[OBSERVED]** Seen during execution but not established as a universal source invariant.
- **[INFERRED]** Technical conclusion derived from evidence.
- **[UNKNOWN]** Not established by the available repository/environment.

## 1. Executive Summary

**[PROVEN]** Feedy is a local Streamlit prototype that ingests PDFs, extracts digital text with pypdf, falls back to Tesseract OCR, segments reviews, embeds them with `sentence-transformers/all-MiniLM-L6-v2`, retrieves three labelled examples from FAISS, calls Ollama `llama3.1` through LangChain, validates structured output with Pydantic, computes an engineering confidence estimate, persists results to CSV, and renders a Plotly dashboard.

**[PROVEN]** The existing 16-example holdout evaluation produced 13/16 correct classifications (81%). All three misses were `Need Improvements` predicted as `Good`.

**[PROVEN]** Digital extraction and segmentation passed generated workloads through 500 reviews, eight supported boundary styles, and multi-page cases. OCR fails in the normal current process when Tesseract is not resolvable through PATH, but passed when its executable path was explicit.

**[PROVEN]** Llama generation is the dominant latency cost. The application also rewrites the entire CSV for every result.

**[UNKNOWN]** A safe maximum full-LLM batch size, peak memory, multi-user CSV safety, and live navigation during a blocking LLM call were not established.

## 2. Repository Inventory

| Path/group | Purpose | Runtime classification |
|---|---|---|
| `app/main.py` | Streamlit orchestration, upload, multi-PDF processing, session state, dashboard | Core runtime |
| `app/settings.py` | Environment variables, paths, thresholds, model settings | Supporting runtime |
| `app/pdf_reader.py` | pypdf extraction and OCR decision | Core runtime |
| `app/ocr_reader.py` | pdf2image and pytesseract fallback | Optional runtime path |
| `app/text_cleaner.py` | Form cleanup and review segmentation | Core runtime |
| `app/similarity_search.py` | MiniLM embeddings, FAISS load/build/retrieval | Core runtime |
| `app/ai_classifier.py` | Prompt, LangChain chain, Ollama call, parser | Core runtime |
| `app/schemas.py` | Four categories and structured result contract | Core runtime |
| `app/confidence_score.py` | Weighted confidence estimate | Core runtime |
| `app/database.py` | CSV read/full rewrite | Core runtime |
| `app/__init__.py` | Empty package marker | Supporting runtime |
| `scripts/build_search_index.py` | Intentional FAISS rebuild | Operational/test support |
| `scripts/generate_sample_pdfs.py` | Synthetic PDF generator | Test/demo only |
| `scripts/test_accuracy.py` | 16-example holdout evaluation | Test-only |
| `data/labelled_examples.json` | 40 labelled examples, 10 per category | Runtime/index input |
| `data/holdout_examples.json` | 16 balanced holdout examples | Test-only |
| `data/feedback_records.csv` | 5,698 rows observed during audit | Runtime persistence |
| `data/sample_pdfs/` | 400 supplied PDFs | Test/demo input |
| `vector_index/index.faiss` | 384-dimensional FAISS index | Runtime asset |
| `vector_index/index.pkl` | FAISS docstore/metadata | Runtime asset |
| `.env` / `.env.example` | Local settings/template | Configuration |
| `.streamlit/config.toml` | `server.fileWatcherType = "none"` | Streamlit configuration |
| `requirements.txt` | Declared dependencies | Installation input |
| `README.md` / `STARTUP.md` | Documentation | Documentation-only |

**[PROVEN]** The README references an absent `STARTUP_COMMANDS.md`; the repository contains `STARTUP.md` instead.

## 3. Architecture and Pipeline

```text
Streamlit browser
  -> app/main.py
     -> multiple PDF uploader
        -> sequential PDF loop
           -> pypdf digital extraction
           -> if text < 20 chars: pdf2image + Tesseract OCR
           -> text_cleaner.extract_feedback_sections
           -> cached FAISS index and MiniLM embedding query
           -> ThreadPoolExecutor(max_workers=4)
              -> retrieve top 3 examples
              -> build RAG prompt
              -> LangChain ChatOllama
              -> Ollama llama3.1
              -> Pydantic structured parsing
              -> neighbour agreement
           -> confidence formula
           -> save_record -> CSV
           -> st.session_state analysis_state
     -> Dashboard: CSV -> pandas filters -> Plotly charts/tables/alerts
```

**[PROVEN]** The application is a modular monolith, local/hybrid, batch-oriented, synchronous at the Streamlit script level, and multithreaded for review classification. There is no asyncio, multiprocessing, queue, Redis, Celery, or background worker.

## 4. Technology and Dependency Audit

Installed versions observed:

- Streamlit 1.64.0
- Python 3.13.14
- Plotly 7.1.0
- pandas 3.0.6
- pypdf 6.19.0
- pdf2image 1.17.0
- pytesseract 0.3.13
- Pillow 12.3.0
- sentence-transformers 6.1.0
- transformers 5.17.0
- torch 2.14.0+cpu
- langchain-huggingface 1.2.2
- langchain-community 0.4.2
- langchain-ollama 1.1.0
- langchain-core 1.6.3
- faiss-cpu 1.15.1
- pydantic 2.13.5
- python-dotenv 1.2.3
- reportlab 5.0.1

**[PROVEN]** PyTorch is required by the observed sentence-transformers/MiniLM stack. Torchvision is not directly imported, was not installed, and is not required by Feedy functionality. OCR uses Tesseract/Poppler, not PyTorch.

## 5. Model Audit

**Embeddings [PROVEN]:** `sentence-transformers/all-MiniLM-L6-v2`, 384-dimensional output, CPU execution in the observed environment, queried through LangChain HuggingFace embeddings. Exact normalization configuration was not established.

**LLM [PROVEN]:** Ollama local service, model `llama3.1:latest`, configured string `llama3.1`, temperature 0, `num_predict=160`. No explicit retry, timeout, batch API, or reasoning-token setting is configured.

**OCR [PROVEN]:** `pdf2image.convert_from_bytes` rasterizes every page and `pytesseract.image_to_string` calls Tesseract sequentially. Poppler and Tesseract are external system dependencies.

## 6. RAG Audit

**[PROVEN]** The saved FAISS index contains 40 documents, dimension 384, FAISS metric type 1, and top-k is 3. Documents contain source text plus label metadata. Retrieved labels are placed in the LLM user message.

**[OBSERVED]** Clear Excellent retrieval returned labels `Need Improvements`, `Good`, `Good`; clear Poor retrieval returned `Poor`, `Poor`, `Good`. Retrieval is semantic similarity, not a category guarantee.

**RAG A/B [PROVEN]:** Four clear cases were run with and without retrieved context. Categories were unchanged in all four. RAG changed confidence/context: Good final confidence 0.95 with agreement 1.0; Need Improvements final 0.70 with agreement 0.33; Excellent final 0.70 with agreement 0.0; Poor final 0.90 with agreement 0.67.

## 7. Classification Audit

Prompt category definitions:

- Excellent: strong satisfaction, delight, loyalty, advocacy, enthusiasm.
- Good: clearly satisfied overall with minor reservations.
- Need Improvements: specific/meaningful problems in a mixed or moderately negative experience without strong churn/frustration.
- Poor: strong dissatisfaction, serious problems, disappointment, frustration, or churn intent.

**[PROVEN]** Pydantic restricts category values and confidence to 0.0–1.0. Invalid JSON, missing fields, invalid category, and out-of-range confidence produce `OutputParserException`; no retry/fallback exists.

**[PROVEN]** Clear examples for all four categories classified correctly. The main tested boundary weakness is Good versus Need Improvements. The existing holdout result is 13/16.

## 8. Confidence Audit

```text
final_confidence = round(
    0.50 * clamp(llm_confidence)
  + 0.30 * clamp(neighbour_agreement)
  + 0.20 * clamp(extraction_quality),
  2
)
```

Digital extraction quality is 1.0; OCR quality is 0.75. Neighbour agreement is the fraction of retrieved labels matching the prediction, or 0.5 without neighbours. Poor alerts require confidence strictly greater than 0.80. This is an engineering estimate, not a calibrated probability.

## 9. Flagged Keywords Audit

**[PROVEN]** The prompt requests evidence copied from source text and the field is persisted/displayed. The schema only enforces `list[str]`; no source-string validator exists.

**[OBSERVED]** All eight controlled outputs in the audit were found verbatim in their source reviews. Universal exactness is unknown.

## 10. Limits and Stress Results

**PDF/review extraction [PROVEN]:** generated digital PDFs with 1, 4, 5, 15, 20, 50, 100, 200, and 500 reviews all produced exact counts. Eight boundary styles and multi-page review cases passed. A formal maximum was not established.

**Multi-PDF [PROVEN]:** `accept_multiple_files=True`; files loop sequentially; review classification uses four worker threads; filename is preserved; upload signature uses filename, byte length, and SHA-256; session state retains combined results. A mixed valid/corrupt/valid/zero-byte/valid extraction batch retained 26 valid reviews and two failures.

**OCR [PROVEN]:** Normal process tests failed with TesseractNotFoundError. Explicit executable-path tests passed scanned one-page, multiple-review, multi-page, noisy, rotated, and small-font cases. A handwriting-style font was partly recognized but not reliable.

**[UNKNOWN]** Full 500-review LLM processing, 1,000/10,000 review limits, maximum uploaded files/pages/bytes, and peak memory were not established because the UI path writes production CSV records and would create long-running unsafe stress jobs.

## 11. Concurrency and Performance

**[PROVEN]** PDF extraction and file iteration are sequential. Unique review classifications are submitted to `ThreadPoolExecutor(max_workers=4)`. Results and CSV saves are processed sequentially afterward.

Measured non-LLM work:

| Reviews | Total extraction/segmentation/embedding/FAISS |
|---:|---:|
| 1 | 0.031 s |
| 5 | 0.104 s |
| 20 | 0.403 s |
| 50 | 0.991 s |
| 100 | 2.036 s |
| 200 | 4.399 s |
| 500 | 10.514 s |

Prior warm LLM measurement was about 17.35 seconds per single review; eight concurrent classification calls took 39.5 seconds wall-clock. Llama generation is the dominant bottleneck.

## 12. Failure Handling

- Corrupt/zero-byte PDFs raise pypdf errors and are caught by the per-file batch path.
- Missing Tesseract raises `TesseractNotFoundError`.
- Missing Poppler raises a pdf2image error.
- Ollama refusal raises `ConnectError`.
- Malformed LLM output raises `OutputParserException` without retry.
- Mixed valid/invalid files retain valid extraction results in tested cases.
- CSV write failures are caught inside the per-review path, but no atomic rollback exists.

## 13. Session State and Dashboard

**[PROVEN]** `st.session_state['analysis_state']` stores status, upload signature, uploader key, file/review counts, combined results, failed files, category counts, and timestamps. External Streamlit AppTest restored a completed result after Dashboard -> Upload navigation with zero exceptions.

**[WARNING]** Active LLM processing is synchronous; live navigation during a blocking call remains unknown.

**[PROVEN]** Dashboard reads CSV data per script run, applies category/review filters, shows four Plotly charts, KPIs, records, and high-confidence Poor alerts. It is CSV-backed/session-driven, not a real-time database.

## 14. Persistence and Security

**[PROVEN]** CSV schema: timestamp, source_file, feedback_text, category, llm_confidence, neighbour_agreement, final_confidence, rationale, flagged_keywords, needs_review.

**[PROVEN]** `save_record` rereads and rewrites the complete CSV for every row. There is no lock, deduplication key, transaction, or append-only write. Temporary 1/100/1000-row tests with quotes, commas, newlines, and Unicode passed; production CSV hash was unchanged.

**[PROVEN]** LLM inference is local Ollama. Initial package/model/embedding downloads may require network. After assets are cached, complete offline operation is likely but was not proven by disabling networking.

**[UNKNOWN]** Authentication, encryption at rest, retention, access control, multi-user isolation, and formal threat-model properties were not established. `.env` exists; secrets were not printed.

## 15. Cognizant Gap Mapping

| Requirement | Status |
|---|---|
| PDF ingestion | VERIFIED |
| Batch/multi-PDF ingestion | VERIFIED; full LLM scale unknown |
| OCR | VERIFIED with Tesseract/Poppler PATH prerequisite |
| Handwriting | NOT PROVEN; imperfect OCR evidence |
| Structured forms | VERIFIED for tested layouts |
| Preprocessing/segmentation | VERIFIED for tested cases |
| Deduplication | Within-run unique review text only |
| Embeddings | VERIFIED MiniLM 384-dimensional |
| FAISS/vector store | VERIFIED local persisted index |
| RAG | VERIFIED top-k 3 labelled examples |
| Llama/Ollama/LangChain | VERIFIED |
| Four categories | VERIFIED |
| Confidence/rationale/keywords | VERIFIED, with keyword exactness not enforced |
| Dashboard/trends/alerts | VERIFIED |
| Cloud storage | NOT IMPLEMENTED |
| Message queue | NOT IMPLEMENTED |
| Cloud Document AI | NOT IMPLEMENTED |
| Enterprise vector DB | NOT IMPLEMENTED |
| Data warehouse | NOT IMPLEMENTED |
| CRM/ticket integration | NOT IMPLEMENTED |

## 16. Architecture Classification

- Modular monolith: PROVEN
- Local/hybrid: PROVEN
- Synchronous/concurrent hybrid: PROVEN
- Stateful per Streamlit session: PROVEN
- Batch-oriented, not streaming: PROVEN
- CPU embedding in observed environment: PROVEN
- CSV/FAISS persistent plus session/in-memory uploaded files: PROVEN

## 17. Confirmed Strengths

- Local Llama inference without a cloud API key.
- Structured four-category Pydantic output.
- Persisted FAISS/RAG index.
- Digital extraction and segmentation through tested 500-review corpus.
- Multi-PDF filename preservation and per-file error isolation.
- Four-worker review concurrency.
- CSV special-character round trips.
- Explicit confidence formula and verified alerts.
- Dashboard and completed-session navigation tests pass.

## 18. Confirmed Weaknesses and Risks

- Tesseract PATH is not reliably available to the application process.
- Holdout classification errors cluster at Good/Need Improvements boundaries.
- Llama generation dominates latency.
- CSV is rewritten for every result and has no lock/deduplication.
- Parser failures have no retry/fallback.
- Handwriting recognition is not supported/proven.
- Retrieved labels may influence predictions even when neighbours differ in category.
- Full workload limits and concurrent-user safety are unknown.

## 19. Improvement Roadmap — Not Implemented

### P0

- Make Tesseract resolution explicit or validate it at startup.
- Add parser retry/failure diagnostics.
- Add focused Good versus Need Improvements evaluation.

### P1

- Add CSV locking/atomic persistence tests before multi-user use.
- Add formal batch and failure test harnesses.

### P2

- Reduce full CSV rewrites after data-integrity validation.
- Benchmark Ollama keep-alive/output settings with accuracy checks.

### P3–P5

- Establish safe workload limits.
- Reconcile README's stale `STARTUP_COMMANDS.md` reference with `STARTUP.md`.
- Consider enterprise storage, queues, Document AI, warehouse, CRM, or vector infrastructure only as future architecture work.

## 20. Final Verdict

**[PROVEN]** Feedy is an operational local prototype for digital PDF feedback classification with RAG, FAISS, local Llama 3.1, confidence scoring, CSV persistence, and a dashboard.

**[PROVEN]** Core digital/RAG/LLM/dashboard functionality passed the tested checks. OCR requires Tesseract to be visible to the process PATH. Holdout accuracy is 81% on 16 examples, with a meaningful Good/Need Improvements boundary weakness.

**[UNKNOWN]** Production-scale maximums, multi-user reliability, formal handwriting support, calibrated confidence, and live navigation during an active blocking call.

## Appendix — Evidence

Source evidence: `app/main.py`, `app/settings.py`, `app/pdf_reader.py`, `app/ocr_reader.py`, `app/text_cleaner.py`, `app/similarity_search.py`, `app/ai_classifier.py`, `app/schemas.py`, `app/confidence_score.py`, `app/database.py`, the three scripts, `requirements.txt`, `.env.example`, and `.streamlit/config.toml`.

Runtime evidence: Streamlit 1.64.0; Python 3.13.14; Ollama 0.17.1 with `llama3.1:latest`; FAISS 40 documents/384 dimensions/top-k 3; Torch 2.14.0+cpu; holdout 13/16; digital scale exact through 500 reviews; explicit-path OCR success; RAG A/B category stability; session navigation zero exceptions.

Detailed temporary artifacts remain at:

`C:\Users\Tigps\AppData\Local\Temp\feedy_max_stress_20260920`

The original longer external audit remains at:

`C:\Users\Tigps\AppData\Local\Temp\FEEDY_FORENSIC_AUDIT.md`
