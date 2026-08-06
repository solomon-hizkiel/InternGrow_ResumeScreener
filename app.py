import io
import re

import pdfplumber
import streamlit as st
from docx import Document

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "you",
    "your",
    "we",
    "our",
    "this",
    "these",
    "those",
    "they",
    "their",
    "have",
    "had",
    "been",
    "being",
    "can",
    "may",
    "must",
    "shall",
    "should",
    "would",
    "could",
    "not",
    "no",
    "but",
    "if",
    "than",
    "then",
    "so",
    "such",
    "into",
    "about",
    "over",
    "under",
    "also",
    "all",
    "any",
    "each",
    "other",
    "more",
    "most",
    "some",
    "who",
    "what",
    "which",
    "when",
    "where",
    "how",
    "do",
    "does",
    "did",
    "etc",
    # Common job-description filler that should not affect the score
    "seeking",
    "looking",
    "responsibilities",
    "requirements",
    "qualifications",
    "preferred",
    "required",
    "ability",
    "familiarity",
    "understanding",
    "background",
    "experience",
    "strong",
    "using",
    "help",
    "work",
    "role",
    "position",
    "candidate",
    "candidates",
    "job",
    "description",
    "related",
    "field",
    "environment",
    "including",
    "across",
    "within",
    "based",
    "well",
    "good",
    "excellent",
    "plus",
    "year",
    "years",
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(io.BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)


def extract_keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9+#.\-]+", text.lower())
    keywords = set()
    for token in tokens:
        cleaned = token.strip(".-")
        if len(cleaned) > 2 and cleaned not in STOP_WORDS:
            keywords.add(cleaned)
    return keywords


def calculate_match(resume_text: str, job_description: str) -> tuple[float, list[str], list[str]]:
    """Match JD keywords against resume text using substring search.

    Exact token intersection fails on many PDFs because words get glued together
    (e.g. resume has 'ModernJavaScript' while JD has 'javascript').
    """
    jd_keywords = extract_keywords(job_description)
    resume_lower = resume_text.lower()

    if not jd_keywords:
        return 0.0, [], []

    matched = sorted(kw for kw in jd_keywords if kw in resume_lower)
    missing = sorted(kw for kw in jd_keywords if kw not in resume_lower)
    score = (len(matched) / len(jd_keywords)) * 100
    return score, matched, missing


def score_color(score: float) -> str:
    if score >= 70:
        return "#22c55e"  # green
    if score >= 40:
        return "#f59e0b"  # amber
    return "#ef4444"  # red


def render_colored_progress(score: float) -> None:
    color = score_color(score)
    clamped = max(0.0, min(score, 100.0))
    st.markdown(
        f"""
        <div style="margin: 0.5rem 0 1.25rem 0;">
            <div style="display:flex; justify-content:space-between; margin-bottom:0.35rem;">
                <span style="font-weight:600;">Match Score</span>
                <span style="font-weight:700; color:{color};">{clamped:.1f}%</span>
            </div>
            <div style="background:#e5e7eb; border-radius:999px; height:18px; overflow:hidden;">
                <div style="width:{clamped}%; background:{color}; height:100%; border-radius:999px;
                            transition: width 0.4s ease;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="AI Score Dashboard", page_icon="📊", layout="wide")

# GitHub-green primary button; hide Ctrl+Enter hint (shortcut still submits the form)
st.markdown(
    """
    <style>
    [data-testid="InputInstructions"] {
        display: none !important;
    }
    button[kind="primary"],
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primaryFormSubmit"] {
        background-color: #238636 !important;
        border-color: #238636 !important;
        color: #ffffff !important;
    }
    button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover,
    button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
        background-color: #2ea043 !important;
        border-color: #2ea043 !important;
        color: #ffffff !important;
    }
    button[kind="primary"]:focus,
    button[data-testid="stBaseButton-primary"]:focus,
    button[data-testid="stBaseButton-primaryFormSubmit"]:focus {
        box-shadow: 0 0 0 0.2rem rgba(46, 160, 67, 0.35) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI Score Dashboard")
st.caption("Upload a resume, submit a job description, and review keyword match results.")

if "analysis" not in st.session_state:
    st.session_state.analysis = None

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("Inputs")
    with st.form("analyze_form", enter_to_submit=True):
        uploaded_file = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])
        job_description = st.text_area(
            "Paste job description",
            height=240,
            placeholder="Paste the job description here...",
            key="job_description",
        )
        submitted = st.form_submit_button(
            "Submit & Analyze",
            type="primary",
            use_container_width=True,
        )

with right:
    st.subheader("Results")

    if submitted:
        if uploaded_file is None:
            st.warning("Please upload a resume first.")
            st.session_state.analysis = None
        elif not job_description.strip():
            st.warning("Please paste a job description before submitting.")
            st.session_state.analysis = None
        else:
            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name.lower()

            try:
                if filename.endswith(".pdf"):
                    resume_text = extract_text_from_pdf(file_bytes)
                elif filename.endswith(".docx"):
                    resume_text = extract_text_from_docx(file_bytes)
                else:
                    st.error("Unsupported file type. Please upload a PDF or DOCX file.")
                    st.stop()
            except Exception as exc:
                st.error(f"Could not extract text from the resume: {exc}")
                st.stop()

            if not resume_text.strip():
                st.warning("No text could be extracted from the resume.")
                st.session_state.analysis = None
            else:
                jd_keywords = sorted(extract_keywords(job_description))
                score, matched, missing = calculate_match(resume_text, job_description)

                print("=" * 60)
                print("RAW EXTRACTED RESUME TEXT")
                print("=" * 60)
                print(resume_text)
                print("=" * 60)
                print("JOB DESCRIPTION KEYWORDS")
                print("=" * 60)
                print(jd_keywords)
                print("=" * 60)
                print(f"KEYWORDS FOUND ({len(matched)})")
                print("=" * 60)
                print(matched)
                print("=" * 60)
                print(f"KEYWORDS NOT FOUND ({len(missing)})")
                print("=" * 60)
                print(missing)
                print("=" * 60)
                print(f"MATCH SCORE: {score:.1f}%")
                print("=" * 60)

                rows = [{"Keyword": kw, "Status": "Found"} for kw in matched]
                rows += [{"Keyword": kw, "Status": "Missing"} for kw in missing]
                st.session_state.analysis = {
                    "score": score,
                    "matched": matched,
                    "missing": missing,
                    "rows": rows,
                    "resume_text": resume_text,
                }

    analysis = st.session_state.analysis
    if analysis is None:
        st.info("Upload a resume, paste a job description, then click **Submit & Analyze**.")
    else:
        m1, m2, m3 = st.columns(3)
        m1.metric("Match Score", f"{analysis['score']:.1f}%")
        m2.metric("Keywords Found", len(analysis["matched"]))
        m3.metric("Keywords Missing", len(analysis["missing"]))

        render_colored_progress(analysis["score"])

        st.markdown("#### Keyword Results")
        st.dataframe(
            analysis["rows"],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Keyword": st.column_config.TextColumn("Keyword", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="small"),
            },
        )

        with st.expander("View extracted resume text"):
            st.text(analysis["resume_text"])
