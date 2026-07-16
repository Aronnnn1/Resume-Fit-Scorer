"""
Curated technical skill taxonomy used for exact keyword matching.

Kept separate from semantic matching: keyword matching catches ATS-style
exact requirements ("must know Docker"), while semantic matching (see
matcher.py) catches paraphrased requirements that don't share exact words.
"""

import re

TECH_SKILLS = [
    # Languages
    "python", "java", "c++", "c#", "javascript", "typescript", "go", "rust",
    "scala", "kotlin", "swift", "sql", "bash", "r",

    # ML / Data
    "machine learning", "deep learning", "scikit-learn", "pytorch",
    "tensorflow", "pandas", "numpy", "lightgbm", "xgboost", "bert",
    "nlp", "computer vision", "opencv", "data science", "statistics",

    # Databases
    "mongodb", "postgresql", "mysql", "oracle", "mssql", "firestore",
    "redis", "sqlite", "dynamodb", "elasticsearch",

    # Cloud / Infra
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "terraform",
    "jenkins", "github actions", "lambda", "ec2", "s3",

    # Web / Backend
    "flask", "fastapi", "django", "rest api", "graphql", "microservices",
    "react", "node.js",

    # Systems / Fundamentals
    "linux", "unix", "operating systems", "networking", "distributed systems",
    "data structures", "algorithms", "oop", "git", "reliability engineering",
    "security", "authentication", "authorization",

    # Finance-specific (useful for LSEG-style JDs)
    "financial engineering", "quantitative analytics", "risk management",
    "trading systems", "market data",
]

_SKILL_PATTERNS = {
    skill: re.compile(r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])")
    for skill in TECH_SKILLS
}


def extract_skills(text: str) -> set:
    """Return the set of taxonomy skills found in text via word-boundary matching."""
    text_lower = text.lower()
    found = set()
    for skill, pattern in _SKILL_PATTERNS.items():
        if pattern.search(text_lower):
            found.add(skill)
    return found