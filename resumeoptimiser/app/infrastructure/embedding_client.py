"""Embedding client abstraction.

Wraps HuggingFace sentence-transformers to produce deterministic dense vectors.

Design constraints:
- Completely separated from LLM logic (different class, different file)
- Deterministic: same text always returns same vector (no sampling)
- Synchronous (embeddings are CPU/GPU batch ops, not async-friendly in this setup)
- Returns numpy arrays – similarity math stays in the scoring layer

BGE models note:
  BAAI/bge-* models work best when query texts are prefixed with
  "Represent this sentence: " for retrieval.  We apply this automatically.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from app.core.config import EmbeddingSettings
from app.core.exceptions import EmbeddingError
from app.core.logging import get_logger

logger = get_logger(__name__)

# BGE models need a query prefix for asymmetric retrieval.
# It is safe to apply to all BGE variants and harmless for others.
_BGE_PREFIX = "Represent this sentence: "


def _needs_prefix(model_name: str) -> bool:
    return "bge" in model_name.lower()


@runtime_checkable
class EmbeddingClientProtocol(Protocol):
    """Structural protocol for any embedding backend."""

    def embed(self, text: str) -> NDArray[np.float32]:
        """Return a 1-D float32 vector for the given text."""
        ...

    def embed_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Return a 2-D array of shape (len(texts), dim)."""
        ...


class SentenceTransformerEmbeddingClient:
    """Deterministic embedding client using sentence-transformers."""

    def __init__(self, settings: EmbeddingSettings) -> None:
        self._settings = settings
        self._use_prefix = _needs_prefix(settings.model)
        self._model = self._load_model(settings)
        logger.info("embedding_client.loaded", model=settings.model, prefix=self._use_prefix)

    def _load_model(self, settings: EmbeddingSettings) -> SentenceTransformer:
        """Load the model once at construction time."""
        try:
            return SentenceTransformer(settings.model, device=settings.device)
        except Exception as exc:
            raise EmbeddingError(f"Failed to load embedding model: {exc}") from exc

    def _apply_prefix(self, text: str) -> str:
        if self._use_prefix:
            return f"{_BGE_PREFIX}{text}"
        return text

    def embed(self, text: str) -> NDArray[np.float32]:
        """Embed a single string into a 1-D float32 vector."""
        if not text.strip():
            raise EmbeddingError("Cannot embed empty text.")
        result = self._model.encode(
            self._apply_prefix(text),
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return result.astype(np.float32)

    def embed_batch(self, texts: list[str]) -> NDArray[np.float32]:
        """Embed a list of strings into a 2-D (N, dim) float32 array."""
        if not texts:
            raise EmbeddingError("Cannot embed an empty list of texts.")
        prefixed = [self._apply_prefix(t) for t in texts]
        result = self._model.encode(
            prefixed,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return result.astype(np.float32)
