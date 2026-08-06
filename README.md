# InternGrow Resume Screener

A Streamlit app that matches resume keywords against a job description and produces a match score.

Upload a resume (PDF or DOCX), paste a job description, and the app extracts keywords from the job description, checks which ones appear in the resume, and shows:

- An overall match score (%)
- A colored progress bar
- A results table of found vs missing keywords

## Tech Stack

- **Streamlit** — web UI
- **pdfplumber** — PDF text extraction
- **python-docx** — DOCX text extraction

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv venv
```

**Windows (PowerShell):**

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal (usually `http://localhost:8501`).
