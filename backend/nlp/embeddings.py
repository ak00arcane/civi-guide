from __future__ import annotations

import hashlib
import math
import re

DIM = 384


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def embed_text(text: str) -> list[float]:
    """Deterministic 384-d hashed bag-of-words. Optional transformers elsewhere."""
    vec = [0.0] * DIM
    toks = _tokenize(text)
    if not toks:
        return vec
    for tok in toks:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % DIM
        sign = 1.0 if (h // DIM) % 2 == 0 else -1.0
        vec[idx] += sign
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / n for x in vec]


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return float(sum(x * y for x, y in zip(a, b)))


def embed_with_optional_model(text: str) -> tuple[list[float], str]:
    from app.config import settings

    if settings.use_transformers:
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(settings.embedding_model)
            vec = model.encode([text], normalize_embeddings=True)[0].tolist()
            return vec, settings.embedding_model
        except Exception:
            pass
    return embed_text(text), "hash-bow-384"
