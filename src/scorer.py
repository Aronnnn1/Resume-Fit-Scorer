"""
Combines keyword coverage and semantic coverage into a single fit report.

Design decisions:
- SEMANTIC_THRESHOLD: a requirement counts as "covered" if its best-matching
  bullet has similarity above this threshold.
- MAX_EVIDENCE_REUSE: caps how many times a single resume bullet can be
  shown as evidence. If a requirement's only semantic match is a bullet
  that's already hit its reuse cap, and no other bullet clears the
  threshold, the requirement is now correctly left uncovered rather than
  falling back to reuse the same overused bullet again -- an earlier
  version of this fell back silently, which defeated the point of the cap.
"""

from dataclasses import dataclass, field

from .skills_taxonomy import extract_skills
from .matcher import Matcher
from .parser import Requirement

SEMANTIC_THRESHOLD = 0.45
MAX_EVIDENCE_REUSE = 2


@dataclass
class RequirementResult:
    requirement: str
    weight: float
    covered: bool
    method: str
    evidence: str = ""
    score: float = 0.0


@dataclass
class FitReport:
    overall_score: float
    keyword_coverage: float
    semantic_coverage: float
    results: list = field(default_factory=list)

    def missing_requirements(self, top_n: int = 10):
        missing = [r for r in self.results if not r.covered]
        missing.sort(key=lambda r: -r.weight)
        return missing[:top_n]

    def covered_requirements(self):
        return [r for r in self.results if r.covered]


def score_fit(requirements: list, bullets: list, matcher: Matcher) -> FitReport:
    resume_text = " ".join(bullets)
    resume_skills = extract_skills(resume_text)

    req_texts = [r.text for r in requirements]
    sim_matrix = matcher.similarity_matrix(req_texts, bullets)

    evidence_usage = {i: 0 for i in range(len(bullets))}

    results = []
    total_weight = 0.0
    covered_weight = 0.0

    for row_idx, req in enumerate(requirements):
        total_weight += req.weight

        req_skills = extract_skills(req.text)
        shared_skills = req_skills & resume_skills
        keyword_hit = bool(shared_skills)

        method = "none"
        covered = False
        evidence = ""
        score = 0.0

        if keyword_hit:
            method = "keyword"
            covered = True
            for b in bullets:
                if any(skill in b.lower() for skill in shared_skills):
                    evidence = b
                    break
            score = float(sim_matrix[row_idx].max()) if bullets else 0.0
        elif bullets:
            ranked = sorted(
                range(len(bullets)),
                key=lambda i: sim_matrix[row_idx][i],
                reverse=True,
            )
            chosen_idx = None
            for idx in ranked:
                score_here = sim_matrix[row_idx][idx]
                if score_here < SEMANTIC_THRESHOLD:
                    break
                if evidence_usage[idx] < MAX_EVIDENCE_REUSE:
                    chosen_idx = idx
                    break
            if chosen_idx is not None:
                evidence_usage[chosen_idx] += 1
                evidence = bullets[chosen_idx]
                score = float(sim_matrix[row_idx][chosen_idx])
                method = "semantic"
                covered = True
            else:
                score = float(sim_matrix[row_idx].max())

        if covered:
            covered_weight += req.weight

        results.append(RequirementResult(
            requirement=req.text,
            weight=req.weight,
            covered=covered,
            method=method,
            evidence=evidence,
            score=score,
        ))

    overall = covered_weight / total_weight if total_weight > 0 else 0.0
    keyword_covered = sum(1 for r in results if r.method == "keyword")
    semantic_covered = sum(1 for r in results if r.method == "semantic")
    n = len(results) if results else 1

    return FitReport(
        overall_score=overall,
        keyword_coverage=keyword_covered / n,
        semantic_coverage=semantic_covered / n,
        results=results,
    )