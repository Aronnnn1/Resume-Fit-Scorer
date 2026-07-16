"""
Combines keyword coverage and semantic coverage into a single fit report.

Design decisions:
- SEMANTIC_THRESHOLD: a requirement counts as "covered" if its best-matching
  bullet has similarity above this threshold.
- Requirement weight (must-have vs nice-to-have) multiplies into scoring,
  so missing a "must-have" hurts more than missing a "nice to have".
- MAX_EVIDENCE_REUSE: caps how many times a single resume bullet can be
  shown as "evidence" across the whole report. Without this, one generic,
  broadly-worded bullet (e.g. a summary line mentioning "engineering" and
  "systems") ends up winning the similarity comparison against many
  unrelated requirements, because it's vaguely related to everything
  without strongly supporting any one claim. Found by inspecting real
  report output during testing -- the same bullet was showing up as
  "evidence" for 6+ unrelated requirements. Capping reuse forces the
  report to surface more specific bullets instead.
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
    method: str          # "keyword", "semantic", or "none"
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

        if bullets:
            top_score = float(sim_matrix[row_idx].max())
        else:
            top_score = 0.0
        semantic_hit = top_score >= SEMANTIC_THRESHOLD

        if keyword_hit:
            method = "keyword"
            covered = True
        elif semantic_hit:
            method = "semantic"
            covered = True
        else:
            method = "none"
            covered = False

        if covered:
            covered_weight += req.weight

        evidence = ""
        if keyword_hit:
            for b in bullets:
                b_lower = b.lower()
                if any(skill in b_lower for skill in shared_skills):
                    evidence = b
                    break
        elif semantic_hit:
            # Rank bullets by score for this requirement, descending.
            ranked = sorted(
                range(len(bullets)),
                key=lambda i: sim_matrix[row_idx][i],
                reverse=True,
            )
            chosen_idx = None
            # Prefer the best bullet that hasn't hit the reuse cap and
            # still clears the threshold on its own.
            for idx in ranked:
                score_here = sim_matrix[row_idx][idx]
                if score_here < SEMANTIC_THRESHOLD:
                    break  # remaining candidates are worse, stop looking
                if evidence_usage[idx] < MAX_EVIDENCE_REUSE:
                    chosen_idx = idx
                    break
            if chosen_idx is None:
                # Nothing under the cap clears the threshold -- fall back
                # to the single best match anyway, overused or not.
                chosen_idx = ranked[0]

            evidence_usage[chosen_idx] += 1
            evidence = bullets[chosen_idx]
            top_score = float(sim_matrix[row_idx][chosen_idx])

        results.append(RequirementResult(
            requirement=req.text,
            weight=req.weight,
            covered=covered,
            method=method,
            evidence=evidence,
            score=top_score,
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