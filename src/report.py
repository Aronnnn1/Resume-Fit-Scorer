"""Generate a human-readable markdown fit report."""

from .scorer import FitReport


def generate_markdown(report: FitReport, resume_name: str, jd_name: str) -> str:
    lines = []
    lines.append("# Resume Fit Report")
    lines.append("")
    lines.append(f"**Resume:** {resume_name}  ")
    lines.append(f"**Job Description:** {jd_name}")
    lines.append("")
    lines.append(f"## Overall Fit Score: {report.overall_score * 100:.1f}%")
    lines.append("")
    lines.append(f"- Keyword-matched requirements: {report.keyword_coverage * 100:.1f}%")
    lines.append(f"- Semantically-matched requirements (no shared keywords): "
                 f"{report.semantic_coverage * 100:.1f}%")
    lines.append("")

    lines.append("## Missing Requirements (ranked by importance)")
    lines.append("")
    missing = report.missing_requirements(top_n=15)
    if not missing:
        lines.append("_None -- strong coverage across all detected requirements._")
    else:
        for r in missing:
            tag = "MUST-HAVE" if r.weight >= 1.5 else (
                "nice-to-have" if r.weight <= 0.6 else "standard"
            )
            lines.append(f"- **[{tag}]** {r.requirement}")
    lines.append("")

    lines.append("## Covered Requirements (with evidence)")
    lines.append("")
    for r in report.covered_requirements():
        lines.append(f"- **{r.requirement}**")
        lines.append(f"  - matched via: `{r.method}` (score: {r.score:.2f})")
        if r.evidence:
            lines.append(f"  - evidence: \"{r.evidence}\"")
    lines.append("")

    return "\n".join(lines)