"""
Resume parsing utilities – extracts text from PDF, DOCX, and plain text.
"""
import io
import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Safe optional imports
# ---------------------------------------------------------------------------
try:
    import PyPDF2
    _HAS_PYPDF2 = True
except ImportError:
    _HAS_PYPDF2 = False
    logger.warning("PyPDF2 not available – PDF parsing disabled")

try:
    import docx2txt
    _HAS_DOCX2TXT = True
except ImportError:
    _HAS_DOCX2TXT = False
    logger.warning("docx2txt not available – DOCX parsing disabled")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract plain text from an uploaded resume file.
    Supports PDF, DOCX, DOC, and TXT.
    Returns extracted string (may be empty if parsing fails).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    try:
        if ext == "pdf":
            return _parse_pdf(file_bytes)
        elif ext in ("docx", "doc"):
            return _parse_docx(file_bytes)
        else:
            # Attempt UTF-8, fall back to latin-1
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return file_bytes.decode("latin-1", errors="replace")
    except Exception as exc:
        logger.error("resume_parser extract_text error (%s): %s", filename, exc)
        return ""


def _parse_pdf(data: bytes) -> str:
    if not _HAS_PYPDF2:
        return "[PDF parsing unavailable – install PyPDF2]"
    reader = PyPDF2.PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        try:
            text = page.extract_text()
            if text:
                pages.append(text)
        except Exception:
            pass
    return "\n".join(pages)


def _parse_docx(data: bytes) -> str:
    if not _HAS_DOCX2TXT:
        return "[DOCX parsing unavailable – install docx2txt]"
    return docx2txt.process(io.BytesIO(data))


# ---------------------------------------------------------------------------
# Quick analysis helpers
# ---------------------------------------------------------------------------

SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "java", "c++", "go", "rust",
    "react", "vue", "angular", "node", "django", "flask", "fastapi",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "sql", "postgresql", "mysql", "mongodb", "redis",
    "machine learning", "deep learning", "nlp", "data science",
    "git", "ci/cd", "devops", "agile", "scrum",
    "html", "css", "rest api", "graphql", "microservices",
]


def extract_skills(text: str) -> list[str]:
    """Return a list of detected skill keywords found in resume text."""
    text_lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill.title())
    return found


def word_count(text: str) -> int:
    return len(text.split())


def score_resume(text: str) -> dict:
    """
    Return a simple heuristic score dict for the uploaded resume.
    """
    skills = extract_skills(text)
    wc = word_count(text)
    has_email = bool(re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text))
    has_phone = bool(re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text))
    has_linkedin = "linkedin" in text.lower()
    score = min(100, len(skills) * 5 + (20 if has_email else 0) +
                (10 if has_phone else 0) + (10 if has_linkedin else 0) +
                min(20, wc // 50))
    return {
        "score": score,
        "skills_found": skills,
        "word_count": wc,
        "has_email": has_email,
        "has_phone": has_phone,
        "has_linkedin": has_linkedin,
    }
