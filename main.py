"""
CLI entry point.

Usage:
    uv run python main.py --resume path/to/resume.pdf --jd path/to/jd.pdf --out report.md
"""

import argparse

from src.parser import extract_text, split_resume_bullets, split_jd_requirements
from src.matcher import Matcher
from src.scorer import score_fit
from src.report import generate_markdown


def main():
    parser = argparse.ArgumentParser(description="Resume-to-JD fit scorer")
    parser.add_argument("--resume", required=True, help="Path to resume (.pdf or .txt)")
    parser.add_argument("--jd", required=True, help="Path to job description (.pdf or .txt)")
    parser.add_argument("--out", default="report.md", help="Output markdown report path")
    args = parser.parse_args()

    resume_text = extract_text(args.resume)
    jd_text = extract_text(args.jd)

    bullets = split_resume_bullets(resume_text)
    requirements = split_jd_requirements(jd_text)

    print(f"Parsed {len(bullets)} resume bullets and "
          f"{len(requirements)} JD requirements.")

    matcher = Matcher()
    report = score_fit(requirements, bullets, matcher)

    md = generate_markdown(report, args.resume, args.jd)
    with open(args.out, "w") as f:
        f.write(md)

    print(f"\nOverall fit score: {report.overall_score * 100:.1f}%")
    print(f"Report written to {args.out}")


if __name__ == "__main__":
    main()