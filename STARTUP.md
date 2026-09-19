# Feedy Startup Guide

This guide is based on the current repository. Feedy is a Streamlit application whose entry point is `app/main.py`.

## Quick Start

For a machine that is already configured:

```powershell
Set-Location "C:\Users\Tigps\Downloads\feedy"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
ollama list
streamlit run app/main.py
```

The current configuration expects Ollama to be running locally and to have `llama3.1` installed. If this project is in a different directory, change the `Set-Location` path.

## Part A: Already-Configured Machine

Use this procedure when the project, its working virtual environment, Python packages, Ollama, OCR tools, and local assets have already been configured successfully.

1. Open Windows PowerShell.
2. Navigate to the project directory:

   ```powershell
   Set-Location "C:\Users\Tigps\Downloads\feedy"
   ```

3. Activate the existing virtual environment:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   .\.venv\Scripts\Activate.ps1
   ```

4. Verify that the activated interpreter is the expected one:

   ```powershell
   python --version
   python -c "import sys; print(sys.executable)"
   ```

   The current working environment uses Python 3.13.14. The repository does not pin a Python version in a project metadata file, so use the already-working environment on an already-configured machine.

5. Verify Ollama and the required model:

   ```powershell
   ollama --version
   ollama list
   ollama list | Select-String "llama3.1"
   Invoke-WebRequest -UseBasicParsing http://localhost:11434/api/tags
   ```

6. If the API check fails, start Ollama in a separate PowerShell window and leave that window running:

   ```powershell
   ollama serve
   ```

   Then return to the project terminal and repeat the API check.

7. No initialization is required during normal startup. The checked-in FAISS files already exist in `vector_index`.

8. Start the application:

   ```powershell
   streamlit run app/main.py
   ```

9. Streamlit normally opens a browser automatically. The expected local address is:

   ```text
   http://localhost:8501
   ```

   If it does not open automatically, browse to that address. The app should show the `Upload & Classify` page and a `Dashboard` page.

## Part B: First Start After Receiving the Project as a ZIP

A copied Python virtual environment is machine-specific and must not be reused on another Windows computer. The current repository contains `.venv`, `app/__pycache__`, `scripts/__pycache__`, and `.pyc` files. It does not currently contain a separate `venv`, `env`, `.streamlit` directory, or temporary/log files.

### Extract and enter the project

Extract the ZIP to a normal writable folder. Then open PowerShell and change to the extracted project directory. For example, replace the path below with the actual extraction path:

```powershell
Set-Location "C:\path\to\feedy"
```

### Safe cleanup

Run this only after confirming that the current directory is the extracted project root:

```powershell
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force env -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force app\__pycache__ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force scripts\__pycache__ -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Force -File -Filter *.pyc -ErrorAction SilentlyContinue |
    Remove-Item -Force
```

#### SAFE TO DELETE / RECREATE

- A copied `.venv`, `venv`, or `env` directory.
- Python `__pycache__` directories.
- `.pyc` files.
- Other temporary files only when they are clearly temporary and not project assets. None were found in the current repository.
- A new `.venv` created on the receiving machine.

#### DO NOT DELETE

- `app/` source files.
- `requirements.txt`.
- `.env.example`.
- `.env`; preserve it if it was supplied and contains the intended local configuration.
- `data/labelled_examples.json`.
- `data/holdout_examples.json`.
- `data/feedback_records.csv`; it is the application's CSV persistence file.
- `data/sample_pdfs/`; these are supplied test PDFs.
- `vector_index/index.faiss` and `vector_index/index.pkl`; both are required by the saved FAISS store.
- `README.md`, `scripts/`, or any other source/project asset.

## Fresh Windows Setup

### 1. Verify Python

Python 3.13.14 is the version detected in the current working environment and is the recommended version for reproducing it. Python 3.11.9 is also installed on the current machine, but the existing project environment was created with Python 3.13.14.

Verify the installed Python launcher entries:

```powershell
py -0p
py -3.13 --version
```

If Python 3.13 is not installed, install Python 3.13 for Windows from python.org, then open a new PowerShell window. The repository has no `pyproject.toml`, `setup.py`, or Python-version pin to select another version automatically.

### 2. Create and activate a fresh environment

From the project root:

```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python --version
python -c "import sys; print(sys.executable)"
```

### 3. Install the repository dependencies

The only dependency manifest is `requirements.txt`:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Do not upgrade individual packages beyond this command merely because newer versions exist.

### 4. Configure environment variables

Create `.env` from the repository template if `.env` was not preserved from the supplied project:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Do not put secrets in this file. The current application uses a local Ollama server and does not require an API key.

### 5. Install and verify OCR system software

The Python packages `pdf2image` and `pytesseract` are installed through `requirements.txt`, but they are wrappers and do not include the required Windows executables.

Install both of these separately on Windows:

- Tesseract OCR, including the `tesseract.exe` executable.
- Poppler, including the command-line tools used by `pdf2image`.

On Windows with WinGet, install Tesseract with the verified package ID:

```powershell
winget install --id UB-Mannheim.TesseractOCR --exact --accept-source-agreements --accept-package-agreements
```

After installation, add the directories containing `tesseract.exe` and Poppler's `pdftoppm.exe`/related tools to the system or user `PATH`, then open a new PowerShell window. Verify them with:

```powershell
tesseract --version
pdftoppm -h
pdfinfo -h
```

On the audited machine, Poppler (`pdftoppm` and `pdfinfo`) and Tesseract are installed and available on `PATH`. If WinGet is unavailable on another machine, use an approved Windows Tesseract installer and then verify the commands above.

### 6. Set up Ollama

Follow the [Ollama Setup](#ollama-setup) section below. The required model is `llama3.1`.

### 7. Preserve or verify the vector store

The supplied repository already contains the saved FAISS store:

```text
vector_index/index.faiss
vector_index/index.pkl
```

Verify both files from the project root:

```powershell
if (-not (Test-Path vector_index\index.faiss)) { throw "Missing vector_index\index.faiss" }
if (-not (Test-Path vector_index\index.pkl)) { throw "Missing vector_index\index.pkl" }
```

**Do not rebuild the vector store during normal startup.**

If the index is genuinely missing, or if `data/labelled_examples.json` has intentionally changed, rebuild it with the repository's script:

```powershell
python scripts/build_search_index.py
```

This reads the labelled examples, downloads/loads the configured Hugging Face embedding model as needed, and overwrites the saved index files. Do not run it merely because the script exists.

Do not run `scripts/generate_sample_pdfs.py` during setup. It generates synthetic PDFs and writes into `data/sample_pdfs/`; the repository already supplies test PDFs. Do not run `scripts/test_accuracy.py` as a startup step; it performs a classification evaluation rather than initialization.

### 8. Run the application

```powershell
streamlit run app/main.py
```

## Ollama Setup

The application reads `OLLAMA_MODEL` and `OLLAMA_BASE_URL` from `.env` through `app/settings.py`. The defaults are:

```text
OLLAMA_MODEL=llama3.1
OLLAMA_BASE_URL=http://localhost:11434
```

The exact required model is `llama3.1`. The application uses LangChain's Ollama integration and connects to the local Ollama HTTP API. No cloud API key is required.

Verify that Ollama is installed:

```powershell
ollama --version
```

Verify that the Ollama server is running:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:11434/api/tags
```

If the request fails, start the local service in a separate PowerShell window:

```powershell
ollama serve
```

List installed models and check for the required one:

```powershell
ollama list
ollama list | Select-String "llama3.1"
```

Pull the required model if it is missing:

```powershell
ollama pull llama3.1
```

Test the model independently:

```powershell
$body = @{ model = "llama3.1"; prompt = "Reply with exactly OK"; stream = $false } | ConvertTo-Json
Invoke-WebRequest -UseBasicParsing `
    -Uri http://localhost:11434/api/generate `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

The response should contain an `OK` response. The configured base URL is `http://localhost:11434`; if a different local Ollama address is required, set `OLLAMA_BASE_URL` in `.env` to that address without changing application code.

## OCR Setup

OCR is a fallback for PDFs whose digital text layer is empty or too short. The implementation in `app/ocr_reader.py` uses:

- Python package `pdf2image`, installed from `requirements.txt`, to rasterize PDF pages.
- Python package `pytesseract`, installed from `requirements.txt`, to call Tesseract.
- The Windows Tesseract executable, which is not included in `pytesseract`.
- Poppler executables, which are not included in `pdf2image`.

Verify the Python packages inside the activated environment:

```powershell
python -c "import pdf2image, pytesseract; print('OCR Python packages available')"
```

Verify the system executables:

```powershell
tesseract --version
pdftoppm -h
pdfinfo -h
```

If `tesseract` is not recognized, install Tesseract and add the directory containing `tesseract.exe` to `PATH`. If `pdftoppm` is not recognized, install Poppler and add its `bin` directory to `PATH`. Open a new terminal after changing `PATH`.

Digital PDFs do not require OCR tools because the normal path uses `pypdf`. Scanned/image-only PDFs require both Tesseract and Poppler.

## RAG / Vector Store Setup

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
- Vector store: local FAISS.
- Location: `vector_index/`.
- Required files: `index.faiss` and `index.pkl`.
- Label source: `data/labelled_examples.json`.
- Existing index: included in the current repository.
- Automatic startup rebuild: none. The app loads the existing index when needed.

**Do not rebuild the vector store during normal startup.**

If the files are missing, run this from the project root after dependencies are installed and the environment is activated:

```powershell
python scripts/build_search_index.py
```

The app will fail when it tries to load the index if the required files are missing. Rebuilding is also appropriate after an intentional change to `data/labelled_examples.json`.

## Environment Variables

These are the only variables read by the current application through `app/settings.py`:

| Variable | Purpose | Required/Optional | Default |
|---|---|---|---|
| `OLLAMA_MODEL` | Ollama model passed to LangChain | Optional | `llama3.1` |
| `OLLAMA_BASE_URL` | Local Ollama HTTP service URL | Optional | `http://localhost:11434` |
| `OLLAMA_NUM_PREDICT` | Maximum number of generated output tokens | Optional | `160` |
| `EMBEDDING_MODEL_NAME` | Hugging Face sentence-transformer used for FAISS queries/index creation | Optional | `sentence-transformers/all-MiniLM-L6-v2` |

`.env` is loaded automatically by `python-dotenv`. The current local LLM setup requires no secrets or API keys.

## Run the Application

From the project root, with `.venv` activated and Ollama available:

```powershell
streamlit run app/main.py
```

The browser should open to `http://localhost:8501`. The first page is `Upload & Classify`; the second page is `Dashboard`.

## Verify the System Is Working

Use one of the supplied PDFs in `data/sample_pdfs/` for a smoke test:

- The Streamlit application opens at `http://localhost:8501`.
- The `Upload & Classify` page accepts a PDF.
- A digital PDF is read through the `pypdf` text-extraction path.
- If an image-only PDF is used, the app reports that OCR was used and Tesseract/Poppler are available.
- One or more reviews are detected from the uploaded form.
- The existing FAISS store loads and similar historical feedback is displayed.
- Ollama responds using `llama3.1`.
- Classification completes without an exception.
- A category appears and is one of the four supported categories.
- Estimated confidence appears.
- A rationale appears.
- Flagged keywords appear when the model returns them.
- A row is written to `data/feedback_records.csv`.
- The `Dashboard` page loads the CSV and displays its metrics, charts, and records.

This is a startup smoke test, not a full accuracy evaluation. Do not run the evaluation script as part of normal startup.

## Common Startup Problems

| Symptom | Likely cause | Exact fix |
|---|---|---|
| Packages fail after moving the project from another computer | The copied virtual environment contains machine-specific paths | Delete the copied `.venv` and create a new one with `py -3.13 -m venv .venv`, then reinstall `requirements.txt` |
| The Python version is unexpected | A different interpreter or old environment is active | Activate `.venv`, then run `python --version` and `python -c "import sys; print(sys.executable)"` |
| `ModuleNotFoundError` | The virtual environment is not active or dependencies were not installed | Run `.\.venv\Scripts\Activate.ps1`, then `python -m pip install -r requirements.txt` |
| `ollama` is not recognized | Ollama is not installed or is not on `PATH` | Install Ollama for Windows, open a new PowerShell window, and run `ollama --version` |
| `llama3.1` is missing from `ollama list` | The required model has not been pulled | Run `ollama pull llama3.1` |
| Connection refused at `localhost:11434` | Ollama is not running or `.env` points to another address | Start `ollama serve` in another terminal, then verify `http://localhost:11434/api/tags` and `OLLAMA_BASE_URL` |
| `TesseractNotFoundError` or `tesseract` is not recognized | Tesseract is not installed, the directory is absent from `PATH`, or the application was started before `PATH` changed | Install Tesseract or add `C:\Program Files\Tesseract-OCR` to `PATH`, open a new terminal, restart Streamlit, and run `tesseract --version` |
| `pdf2image` cannot find Poppler or `pdftoppm` is not recognized | Poppler is not installed or its `bin` directory is absent from `PATH` | Install Poppler, add its `bin` directory to `PATH`, open a new terminal, and run `pdftoppm -h` |
| FAISS load fails or the index is missing | `vector_index/index.faiss` or `vector_index/index.pkl` was not copied | Restore both files from the project ZIP, or intentionally run `python scripts/build_search_index.py` from the project root |
| `streamlit` is not recognized | The virtual environment is not active or the package is missing | Activate `.venv`; if needed run `python -m pip install -r requirements.txt`; then use `python -m streamlit run app/main.py` |
| The app cannot find `data/` or `vector_index/` | The command was run outside the project root | Run `Set-Location "C:\path\to\feedy"` before starting Streamlit |
| Port 8501 is already in use | Another Streamlit process owns the default port | Run `streamlit run app/main.py --server.port 8502` and open `http://localhost:8502` |

## Repository-Specific Safety Notes

- Do not modify application code, prompts, classification behavior, confidence logic, OCR behavior, or RAG behavior as part of startup.
- Do not regenerate the supplied sample PDFs.
- Do not rebuild the vector store during normal startup.
- Do not delete the supplied datasets, CSV, sample PDFs, `.env.example`, or FAISS files.
- `scripts/build_search_index.py` is an intentional rebuild operation, not a routine startup command.

## Final Detected Configuration

- `STARTUP.md` created: YES
- Detected Python version: 3.13.14 in the existing `.venv` (`py -3.13` is available)
- Detected application entry point: `app/main.py`
- Detected dependency file: `requirements.txt`
- Detected Ollama model: `llama3.1`
- Detected embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Detected vector-store location: `vector_index/` containing `index.faiss` and `index.pkl`
- OCR system dependencies: Tesseract executable and Poppler executables; both are installed and available on `PATH` on the audited machine
- Environment variables found: `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_NUM_PREDICT`, `EMBEDDING_MODEL_NAME`
- Startup requirement not verified: none for the currently audited machine
