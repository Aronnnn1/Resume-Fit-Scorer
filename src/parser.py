"""
Parsing utilities.

Responsibilities:
- Extract raw text from PDF or plain text files.
- Split resume text into discrete "bullets" (units of evidence).
- Split JD text into discrete "requirement sentences", tagged with a rough
  importance weight based on section context (must-have vs nice-to-have).
"""

import re
from dataclasses import dataclass


@dataclass
class Requirement:
    text: str
    weight: float = 1.0  # 1.0 = standard, 1.5 = must-have, 0.6 = nice-to-have


CONTACT_LINE_PATTERN = re.compile(
    r"(github|linkedin|@\S+\.\S+|\+?\d[\d\s-]{8,}\d)", re.IGNORECASE
)


def extract_text(path: str) -> str:
    """Extract raw text from a .pdf or .txt file."""
    if path.lower().endswith(".pdf"):
        import pdfplumber
        # Default x_tolerance (3) merges adjacent words with no space on
        # some resume fonts/templates. Tighter tolerance fixes it.
        text_chunks = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=1) or ""
                text_chunks.append(page_text)
        return "\n".join(text_chunks)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def split_resume_bullets(text: str) -> list:
    """
    Split resume text into bullet-level chunks.

    Drops the contact-info line -- it's not evidence of any skill and
    otherwise pollutes similarity matches.
    """
    normalized = re.sub(r"[•▪●∙·]", "\n", text)
    lines = [ln.strip() for ln in normalized.split("\n")]

    bullets = []
    for line in lines:
        if len(line) < 25:
            continue
        if re.match(r"^\d{4}", line):
            continue
        if CONTACT_LINE_PATTERN.search(line):
            continue
        bullets.append(line)

    return bullets


MUST_HAVE_MARKERS = [
    "required", "must have", "must-have", "essential", "you should be",
    "eligibility", "should be", "minimum",
]
NICE_TO_HAVE_MARKERS = [
    "nice to have", "preferred", "will be helpful", "helpful", "a plus",
    "bonus",
]


def split_jd_requirements(text: str) -> list:
    """
    Split a job description into requirement-level sentences.

    PDF text-extraction hard-wraps lines mid-sentence, so we first rejoin
    lines into paragraphs (blank line = paragraph break) before splitting on
    sentence punctuation. Splitting on raw newlines fragments sentences into
    meaningless clauses (e.g. "and business needs evolve." as its own
    "requirement").
    """
    paragraphs = re.split(r"\n\s*\n", text)
    joined = []
    for para in paragraphs:
        single_line = re.sub(r"\s*\n\s*", " ", para).strip()
        if single_line:
            joined.append(single_line)
    full_text = "\n".join(joined)

    # Split into sentences on punctuation, and also on bullet markers
    # (checkmarks, bullets) which JDs use instead of full sentences
    full_text = re.sub(r"[•▪●∙·✓]", "\n", full_text)
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n", full_text)

    requirements = []
    for sent in raw_sentences:
        sent_clean = sent.strip(" -•\u2022\t")
        if len(sent_clean.split()) < 4:  # drop bare headings/fragments
            continue
        if len(sent_clean) < 20:
            continue

        lower = sent_clean.lower()
        weight = 1.0
        if any(marker in lower for marker in MUST_HAVE_MARKERS):
            weight = 1.5
        elif any(marker in lower for marker in NICE_TO_HAVE_MARKERS):
            weight = 0.6

        requirements.append(Requirement(text=sent_clean, weight=weight))

    return requirements

def extract_text_from_bytes(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes held in memory -- used by the web app so
    uploaded files are never written to disk. Assumes PDF input, since
    that's the only upload type the web form accepts.
    """
    import io
    import pdfplumber

    text_chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=1) or ""
            text_chunks.append(page_text)
    return "\n".join(text_chunks)