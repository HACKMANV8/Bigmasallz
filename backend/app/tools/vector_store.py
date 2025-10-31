"""Vector store wrapper for ChromaDB."""

import logging
from typing import List, Optional
import chromadb
from chromadb.config import Settings
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Wrapper for ChromaDB vector database.

    Provides embedding storage and similarity search for deduplication.
    """

    def __init__(self):
        """Initialize ChromaDB client."""
        # Ensure data directory exists
        chromadb_path = Path(settings.CHROMADB_PATH)
        chromadb_path.mkdir(parents=True, exist_ok=True)

        # Initialize persistent client
        self.client = chromadb.PersistentClient(
            path=str(chromadb_path),
            settings=Settings(
                anonymized_telemetry=False, allow_reset=True
            ),
        )

        logger.info(f"Initialized ChromaDB at {chromadb_path}")

    def get_or_create_collection(self, collection_name: str):
        """
        Get or create a collection.

        Args:
            collection_name: Name of collection

        Returns:
            ChromaDB collection
        """
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.debug(f"Got/created collection: {collection_name}")
            return collection

        except Exception as e:
            logger.error(f"Error accessing collection: {str(e)}")
            raise

    def add_embeddings(
        self,
        collection_name: str,
        embeddings: List[List[float]],
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[dict]] = None,
    ):
        """
        Add embeddings to collection.

        Args:
            collection_name: Collection name
            embeddings: List of embedding vectors
            documents: List of document strings
            ids: List of unique IDs
            metadatas: Optional metadata for each document
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            collection.add(
                embeddings=embeddings,
                documents=documents,
                ids=ids,
                metadatas=metadatas,
            )

            logger.debug(
                f"Added {len(embeddings)} embeddings to {collection_name}"
            )

        except Exception as e:
            logger.error(f"Error adding embeddings: {str(e)}")
            raise

    def query_similar(
        self,
        collection_name: str,
        query_embeddings: List[List[float]],
        n_results: int = 1,
        threshold: Optional[float] = None,
    ) -> List[List[float]]:
        """
        Query for similar embeddings.

        Args:
            collection_name: Collection name
            query_embeddings: Query embedding vectors
            n_results: Number of results per query
            threshold: Optional similarity threshold

        Returns:
            List of distances (one list per query)
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            results = collection.query(
                query_embeddings=query_embeddings, n_results=n_results
            )

            # Extract distances
            distances = results.get("distances", [])

            # Apply threshold if specified
            if threshold is not None:
                # Convert distance to similarity (1 - distance for cosine)
                filtered_distances = []
                for dist_list in distances:
                    filtered = [d for d in dist_list if (1 - d) >= threshold]
                    filtered_distances.append(filtered)
                return filtered_distances

            return distances

        except Exception as e:
            logger.error(f"Error querying embeddings: {str(e)}")
            return [[] for _ in query_embeddings]

    def delete_collection(self, collection_name: str):
        """
        Delete a collection.

        Args:
            collection_name: Collection to delete
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")

        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")

    def collection_count(self, collection_name: str) -> int:
        """
        Get count of items in collection.

        Args:
            collection_name: Collection name

        Returns:
            Number of items
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            return collection.count()

        except Exception as e:
            logger.error(f"Error getting collection count: {str(e)}")
            return 0
