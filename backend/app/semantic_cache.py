import time
import math
import re
from typing import Dict, Any, Optional, Tuple
import numpy as np


EMBEDDING_DIM = 256


def compute_embedding(text: str) -> np.ndarray:
    """
    Computes a deterministic, L2-normalized 256-dimensional semantic vector
    combining normalized word tokens and character 3/4-grams via signed feature hashing.
    Zero external ML runtime dependencies, <1ms latency, captures lexical & paraphrase overlap.
    """
    cleaned = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    tokens = [t for t in cleaned.split() if len(t) > 1]

    # Stopwords reduction so content words dominate similarity
    stopwords = {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "of", "to",
        "in", "for", "with", "me", "tell", "what", "please", "can", "you",
        "o", "a", "os", "as", "de", "do", "da", "em", "um", "uma", "que", "qual"
    }
    content_tokens = [t for t in tokens if t not in stopwords] or tokens

    vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)

    # 1. Word-level features (high weight)
    for tok in content_tokens:
        h = hash(f"w:{tok}")
        idx = abs(h) % EMBEDDING_DIM
        sign = 1.0 if (h & 1) == 0 else -1.0
        vec[idx] += sign * 2.2

    # 2. Character 3-grams and 4-grams (captures morphological variants & phrasing)
    joined = " ".join(content_tokens)
    for n in (3, 4):
        if len(joined) >= n:
            for i in range(len(joined) - n + 1):
                gram = joined[i : i + n]
                h = hash(f"g{n}:{gram}")
                idx = abs(h) % EMBEDDING_DIM
                sign = 1.0 if (h & 1) == 0 else -1.0
                vec[idx] += sign * 0.65

    norm = float(np.linalg.norm(vec))
    if norm > 0:
        vec /= norm
    return vec


class SemanticCache:
    def __init__(self, default_threshold: float = 0.72, ttl_seconds: int = 3600):
        self.default_threshold = default_threshold
        self.ttl_seconds = ttl_seconds
        self._entries: list[Dict[str, Any]] = []

    def lookup(
        self, prompt: str, threshold: Optional[float] = None
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        if not self._entries:
            return None, 0.0

        now = time.time()
        # Prune expired entries
        self._entries = [e for e in self._entries if (now - e["created_at"]) < self.ttl_seconds]
        if not self._entries:
            return None, 0.0

        query_vec = compute_embedding(prompt)
        best_score = -1.0
        best_entry = None

        for entry in self._entries:
            sim = float(np.dot(query_vec, entry["embedding"]))
            if sim > best_score:
                best_score = sim
                best_entry = entry

        effective_threshold = threshold if threshold is not None else self.default_threshold
        if best_entry is not None and best_score >= effective_threshold:
            best_entry["hits"] += 1
            return best_entry, round(best_score, 4)

        return None, round(max(0.0, best_score), 4)

    def store(self, prompt: str, response_text: str, model: str, provider: str, usage: Dict[str, int]):
        vec = compute_embedding(prompt)
        # Update if near-exact match already exists
        for entry in self._entries:
            if float(np.dot(vec, entry["embedding"])) > 0.98:
                entry["response_text"] = response_text
                entry["created_at"] = time.time()
                return

        self._entries.append({
            "prompt": prompt,
            "embedding": vec,
            "response_text": response_text,
            "model": model,
            "provider": provider,
            "usage": usage,
            "created_at": time.time(),
            "hits": 0,
        })
        # Cap memory footprint at 500 entries
        if len(self._entries) > 500:
            self._entries.pop(0)

    def clear(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        return {
            "entries_count": len(self._entries),
            "default_threshold": self.default_threshold,
            "ttl_seconds": self.ttl_seconds,
            "total_cache_hits": sum(e["hits"] for e in self._entries),
        }


semantic_cache = SemanticCache()
