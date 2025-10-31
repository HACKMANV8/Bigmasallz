"""Vector store integration using ChromaDB and sentence transformers."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Iterable
from typing import Any

from sentence_transformers import SentenceTransformer

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import chromadb
    from chromadb.api.types import EmbeddingFunction
except ImportError as exc:  # pragma: no cover - dependency should exist, but guard for safety
    chromadb = None  # type: ignore[assignment]
    EmbeddingFunction = Any  # type: ignore[assignment]
    logger.error("ChromaDB dependency missing: %s", exc)


class VectorStore:
    """Chroma-backed vector store for row deduplication."""

    def __init__(self):
        config = settings.vector_store
        if chromadb is None:
            raise RuntimeError("ChromaDB is not installed")

        persist_path = config.persist_path
        persist_path.mkdir(parents=True, exist_ok=True)
        logger.info("Initialising ChromaDB persistent client at %s", persist_path)

        self._client = chromadb.PersistentClient(path=str(persist_path))
        self._collection = self._client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._model_name = config.embedding_model
        logger.info("Loading sentence transformer model: %s", self._model_name)
        self._embedder = SentenceTransformer(self._model_name)
        self._similarity_threshold = config.similarity_threshold
        self._lock = threading.Lock()

    def filter_new_rows(
        self,
        job_id: str,
        rows: list[dict[str, Any]],
        unique_fields: Iterable[str] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Filter out rows that already exist in the vector store.

        Args:
            job_id: Identifier for the dataset generation job.
            rows: Candidate rows to persist.
            unique_fields: Field names to use for deduplication. If empty, uses all fields.

        Returns:
            Tuple of (accepted_rows, duplicate_rows)
        """
        if not rows:
            return [], []

        unique_fields = list(unique_fields or [])
        accepted: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []

        for row in rows:
            content = self._build_content(row, unique_fields)
            if not content:
                accepted.append(row)
                continue

            embedding = self._encode_text(content)
            if self._is_duplicate(embedding):
                duplicates.append(row)
                continue

            self._add_embedding(job_id, content, embedding)
            accepted.append(row)

        if duplicates:
            logger.info(
                "Vector store removed %s duplicate rows (job_id=%s)",
                len(duplicates),
                job_id,
            )

        return accepted, duplicates

    def _encode_text(self, text: str) -> list[float]:
        vector = self._embedder.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def _is_duplicate(self, embedding: list[float]) -> bool:
        with self._lock:
            results = self._collection.query(
                query_embeddings=[embedding],
                n_results=1,
            )

        distances = results.get("distances") or []
        if distances and distances[0]:
            distance = distances[0][0]
            if distance <= self._similarity_threshold:
                return True
        return False

    def _add_embedding(self, job_id: str, content: str, embedding: list[float]):
        metadata = {"job_id": str(job_id)}
        with self._lock:
            self._collection.add(
                ids=[f"{job_id}-{uuid.uuid4()}"],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[content],
            )

    @staticmethod
    def _build_content(row: dict[str, Any], unique_fields: Iterable[str]) -> str:
        fields = list(unique_fields)
        if not fields:
            fields = sorted(row.keys())
        parts = []
        for field in fields:
            value = row.get(field)
            if value is None:
                return ""
            parts.append(f"{field}:{value}")
        return " | ".join(parts)


_vector_store: VectorStore | None = None
_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    """Get the singleton vector store instance."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    if not settings.vector_store.enabled:
        raise RuntimeError("Vector store requested but disabled in configuration")

    with _lock:
        if _vector_store is None:
            _vector_store = VectorStore()
    return _vector_store
