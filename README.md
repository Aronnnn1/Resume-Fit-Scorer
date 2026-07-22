# Resume Fit Scorer

A tool that scores how well a resume matches a job description — not a
vague percentage, but a ranked list of *specific* missing requirements
and covered requirements with evidence pulled from the actual resume text.

Built to answer honestly: "how is this different from just asking an LLM?"
Answer: there is no generative model anywhere in the scoring pipeline. It's
a deterministic, reproducible system — classical NLP (embeddings + cosine
similarity + keyword matching), not an LLM wrapper.

## Tech Stack

- **Python 3.11**, managed with **uv**
- **pdfplumber** — PDF text extraction
- **sentence-transformers** (`all-MiniLM-L6-v2`) — semantic similarity via
  sentence embeddings
- **scikit-learn** — TF-IDF fallback matching (used offline) + cosine similarity
- **reportlab** — downloadable PDF report generation
- **Flask** — web app (upload PDF → get a downloadable PDF report)
- **gunicorn** — production WSGI server for deployment
- Planned deployment target: **AWS App Runner**

## Status as of now

### ✅ Done — CLI version (fully working, tested end-to-end, pushed to GitHub)
- `src/skills_taxonomy.py` — keyword matching with word-boundary regex
  (fixed a real bug: naive substring matching let `"r"`/`"go"`
  false-positive inside words like "career"/"going")
- `src/parser.py` — PDF extraction (fixed word-squishing via
  `x_tolerance=1`), resume bullet splitting, JD requirement splitting
  (fixed sentence-fragmentation by rejoining wrapped PDF lines first),
  plus `extract_text_from_bytes()` for in-memory use (no disk writes)
- `src/matcher.py` — sentence-embedding similarity with TF-IDF fallback
  if the embedding model can't download
- `src/scorer.py` — combines keyword + semantic matching into a weighted
  score. Fixed two real bugs found through testing:
  1. Evidence was pulled from the semantic argmax even for keyword
     matches, showing irrelevant "evidence" -- fixed.
  2. One generic, broadly-worded resume bullet was getting reused as
     evidence for many unrelated requirements. Added `MAX_EVIDENCE_REUSE`
     cap. First version of the cap still had a silent fallback that reused
     the overused bullet anyway when nothing else qualified -- fixed by
     removing the fallback: if nothing under the cap clears the
     threshold, the requirement is correctly left uncovered.
- `src/report.py` — markdown report generator for CLI output
- `main.py` — CLI entry point
- `SEMANTIC_THRESHOLD = 0.45`, chosen empirically by comparing 0.42/0.45/0.5
  against real output
- Verified result after all fixes: overall fit score 13.2% (resume.pdf vs
  LSEG JD), no evidence bullet reused more than twice

### ✅ Done — web app backend logic (tested standalone, not yet wired into a running app)
- `src/report_pdf.py` — generates the downloadable PDF report, visually confirmed
- `extract_text_from_bytes()` in `parser.py` — confirmed working, nothing touches disk

### ⬜ Not done yet
- `app.py` — Flask app (upload route + analyze route tying
  parser → matcher → scorer → report_pdf together, `send_file` response)
- `templates/index.html` — upload form page
- `static/style.css` — basic styling
- Add `flask`, `reportlab`, `gunicorn` as dependencies (`uv add flask reportlab gunicorn`)
- `Dockerfile` — for AWS App Runner deployment (should pre-download the
  embedding model at build time so cold starts aren't slow)
- Actual deployment to AWS App Runner — nothing is live yet

## Known limitations (documented deliberately)

- Small embedding models are noticeably weaker at connecting **abstract
  behavioral JD language** ("you understand technology should be built
  safely and securely") to **concrete technical resume evidence**
  ("designed secure authentication architecture") than at concrete-to-concrete
  matching. A larger model would likely close this gap.
- Must-have vs. nice-to-have weighting is a keyword heuristic, not a
  trained classifier.
- No numeric requirement handling (e.g. "minimum 7.5 CGPA") -- text
  similarity only, can't extract and compare numbers.
- TF-IDF fallback (offline mode) is meaningfully weaker than embedding
  matching.

## How to run

```bash
uv run python main.py --resume resume.pdf --jd jd.pdf --out fit_report.md
```

## Next steps when picking this back up

1. Add `app.py`, `templates/index.html`, `static/style.css`.
2. Add `Dockerfile`.
3. Deploy to AWS App Runner.
4. Update this README once done.