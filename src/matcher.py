"""
Semantic matching between JD requirements and resume bullets.

Primary method: sentence-transformer embeddings + cosine similarity.
Catches paraphrased matches that keyword overlap alone would miss (e.g.
JD: "distributed systems experience" vs resume: "scalable backend
synchronization across concurrent clients").

Fallback method: TF-IDF vectorization + cosine similarity, used when the
embedding model can't be downloaded. Keeps the tool usable offline, at the
cost of missing paraphrased matches TF-IDF can't catch.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Matcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.mode = "embedding"
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            print(f"[matcher] Falling back to TF-IDF similarity "
                  f"(embedding model unavailable: {e})")
            self.mode = "tfidf"

    def similarity_matrix(self, requirements: list, bullets: list) -> np.ndarray:
        """
        Return an (n_requirements x n_bullets) matrix of similarity scores.
        """
        if not requirements or not bullets:
            return np.zeros((len(requirements), len(bullets)))

        if self.mode == "embedding":
            req_emb = self.model.encode(requirements)
            bullet_emb = self.model.encode(bullets)
            sim = cosine_similarity(req_emb, bullet_emb)
        else:
            vectorizer = TfidfVectorizer(stop_words="english")
            corpus = requirements + bullets
            tfidf = vectorizer.fit_transform(corpus)
            req_vecs = tfidf[: len(requirements)]
            bullet_vecs = tfidf[len(requirements):]
            sim = cosine_similarity(req_vecs, bullet_vecs)

        return np.clip(sim, 0, 1)

    def best_match(self, requirements: list, bullets: list):
        """
        For each requirement, find the best-matching bullet and its score.
        Returns a list of (requirement_index, best_bullet_index, score).
        """
        sim = self.similarity_matrix(requirements, bullets)
        results = []
        for i in range(len(requirements)):
            if sim.shape[1] == 0:
                results.append((i, None, 0.0))
                continue
            j = int(np.argmax(sim[i]))
            score = float(sim[i, j])
            results.append((i, j, score))
        return results