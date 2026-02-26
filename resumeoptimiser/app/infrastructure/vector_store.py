"""Vector store abstraction backed by PostgreSQL + pgvector.

Responsibilities:
- Persist embedding vectors keyed by a document ID
- Retrieve the top-k nearest neighbours by cosine similarity
- No business logic – pure storage operations

This is a stub/skeleton. Full SQLAlchemy + pgvector wiring can be
completed once the DB layer is set up.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class VectorRecord:
    """A stored vector with its associated document ID."""

    doc_id: UUID
    vector: NDArray[np.float32]
    metadata: dict[str, str]


@runtime_checkable
class VectorStoreProtocol(Protocol):
    """Structural protocol for any vector store backend."""

    def upsert(self, record: VectorRecord) -> None:
        """Insert or update a vector record."""
        ...

    def query(self, vector: NDArray[np.float32], top_k: int = 5) -> list[VectorRecord]:
        """Return the top_k most similar records to the given vector."""
        ...


class InMemoryVectorStore:
    """Simple in-memory vector store for testing and development.

    NOT suitable for production – use PgVectorStore in production.
    """

    def __init__(self) -> None:
        self._records: list[VectorRecord] = []

    def upsert(self, record: VectorRecord) -> None:
        """Insert or replace a record with the same doc_id."""
        self._records = [r for r in self._records if r.doc_id != record.doc_id]
        self._records.append(record)

    def query(self, vector: NDArray[np.float32], top_k: int = 5) -> list[VectorRecord]:
        """Return top_k records ordered by cosine similarity (descending)."""
        if not self._records:
            return []
        scored = [(self._cosine(vector, r.vector), r) for r in self._records]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    @staticmethod
    def _cosine(a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
        """Compute cosine similarity between two normalised vectors."""
        return float(np.dot(a, b))
