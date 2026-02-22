"""
Semantic embedding service using SentenceTransformers.

Provides deterministic, reproducible embeddings for CV and job description content.
Uses bge-base-en-v1.5 model for semantic similarity computation.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer, CrossEncoder

logger = logging.getLogger("embedder")

# Fixed model versions for reproducibility
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"  # High-quality semantic embeddings from BAAI
CROSS_ENCODER_MODEL = "cross-encoder/mmarco-MiniLMv2-L12-H384"  # For ranking similarity


class EmbeddingService:
    """Manages semantic embeddings with caching and determinism."""
    
    _instance = None
    _model = None
    _cross_encoder = None
    
    def __new__(cls):
        """Singleton pattern for embedding service."""
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize embedding service with models."""
        if self._model is None:
            logger.info(f"🔄 Loading embedding model: {EMBEDDING_MODEL}")
            self._model = SentenceTransformer(EMBEDDING_MODEL)
            # Set deterministic mode
            self._model.eval()
            logger.info("✓ Embedding model loaded successfully")
        
        if self._cross_encoder is None:
            try:
                logger.info(f"🔄 Loading cross-encoder model: {CROSS_ENCODER_MODEL}")
                self._cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
                self._cross_encoder.eval()
                logger.info("✓ Cross-encoder model loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load cross-encoder model: {e}")
                logger.warning("⚠️  Cross-encoder will be unavailable, but embeddings will work")
                self._cross_encoder = None
    
    def embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings with shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])
        
        logger.debug(f"Embedding {len(texts)} text segments")
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings
    
    def embed_sections(self, sections: Dict[str, str]) -> Dict[str, np.ndarray]:
        """
        Embed multiple sections with labels.
        
        Args:
            sections: Dict of {label: text}
            
        Returns:
            Dict of {label: embedding}
        """
        logger.debug(f"Embedding {len(sections)} sections")
        embeddings = {}
        for label, text in sections.items():
            if text and text.strip():
                embeddings[label] = self._model.encode(
                    text,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
        return embeddings
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        if len(embedding1) == 0 or len(embedding2) == 0:
            return 0.0
        
        # Normalize vectors
        v1 = embedding1 / (np.linalg.norm(embedding1) + 1e-8)
        v2 = embedding2 / (np.linalg.norm(embedding2) + 1e-8)
        
        similarity = float(np.dot(v1, v2))
        # Clamp to [0, 1] to handle numerical precision issues
        return max(0.0, min(1.0, similarity))
    
    def batch_cosine_similarity(
        self,
        query_embedding: np.ndarray,
        target_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and multiple targets.
        
        Args:
            query_embedding: Single query embedding
            target_embeddings: Array of target embeddings (N, D)
            
        Returns:
            Array of similarity scores (N,)
        """
        # Normalize
        q = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        targets = target_embeddings / (np.linalg.norm(target_embeddings, axis=1, keepdims=True) + 1e-8)
        
        # Compute similarities
        similarities = np.dot(targets, q)
        return np.clip(similarities, 0.0, 1.0)
    
    def semantic_search(
        self,
        query_text: str,
        candidates: List[str],
        top_k: int = 5
    ) -> List[Tuple[int, str, float]]:
        """
        Find top-k most similar candidates for query.
        
        Args:
            query_text: Query string
            candidates: List of candidate strings
            top_k: Number of top results to return
            
        Returns:
            List of (index, candidate_text, similarity_score)
        """
        if not candidates:
            return []
        
        query_embedding = self._model.encode(query_text, convert_to_numpy=True)
        candidate_embeddings = self._model.encode(candidates, convert_to_numpy=True)
        
        similarities = self.batch_cosine_similarity(query_embedding, candidate_embeddings)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [
            (int(idx), candidates[idx], float(similarities[idx]))
            for idx in top_indices
            if similarities[idx] > 0.0
        ]
        return results
    
    def cross_encode_similarity(self, pairs: List[Tuple[str, str]]) -> np.ndarray:
        """
        Compute similarity scores using cross-encoder (more accurate but slower).
        Falls back to cosine similarity if cross-encoder unavailable.
        
        Args:
            pairs: List of (text1, text2) tuples
            
        Returns:
            Array of similarity scores (0-1)
        """
        if not pairs:
            return np.array([])
        
        if self._cross_encoder is None:
            logger.debug("Cross-encoder unavailable, using cosine similarity fallback")
            # Fallback: use cosine similarity
            scores = []
            for text1, text2 in pairs:
                emb1 = self._model.encode(text1, convert_to_numpy=True)
                emb2 = self._model.encode(text2, convert_to_numpy=True)
                sim = self.cosine_similarity(emb1, emb2)
                scores.append(sim)
            return np.array(scores)
        
        logger.debug(f"Cross-encoding {len(pairs)} pairs")
        scores = self._cross_encoder.predict(pairs)
        # Normalize to 0-1 range
        return np.clip((scores + 1) / 2, 0.0, 1.0)
    
    def embed_query_document_pairs(
        self,
        queries: List[str],
        documents: List[str]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Embed queries and documents separately for efficient similarity computation.
        
        Args:
            queries: List of query strings
            documents: List of document strings
            
        Returns:
            Tuple of (query_embeddings, document_embeddings)
        """
        query_embeddings = self._model.encode(queries, convert_to_numpy=True)
        doc_embeddings = self._model.encode(documents, convert_to_numpy=True)
        return query_embeddings, doc_embeddings


# Singleton instance
_embedder = None


def get_embedder() -> EmbeddingService:
    """Get or create embedder singleton."""
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingService()
    return _embedder
