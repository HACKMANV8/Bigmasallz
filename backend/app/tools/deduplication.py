"""FastMCP Deduplication Tool using ChromaDB."""

import logging
import json
import hashlib
from typing import List, Dict, Any

from app.tools.vector_store import VectorStore
from app.utils.llm_client import LLMClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class DeduplicationTool:
    """
    FastMCP Deduplication Tool.

    Uses vector embeddings and ChromaDB for intelligent deduplication
    of synthetic data based on semantic similarity.

    This is the key differentiator from standard GPT - it guarantees
    unique, high-quality data at scale.
    """

    def __init__(self):
        """Initialize deduplication tool."""
        self.vector_store = VectorStore()
        self.llm_client = LLMClient()
        logger.info("Initialized DeduplicationTool")

    async def initialize_collection(self, collection_name: str):
        """
        Initialize a collection for a new job.

        Args:
            collection_name: Unique collection name for the job
        """
        try:
            # Clear any existing collection (for new jobs)
            try:
                self.vector_store.delete_collection(collection_name)
            except:
                pass  # Collection might not exist

            # Create new collection
            self.vector_store.get_or_create_collection(collection_name)

            logger.info(f"Initialized collection: {collection_name}")

        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise

    async def check_duplicates(
        self,
        rows: List[Dict[str, Any]],
        collection_name: str,
        threshold: float = 0.85,
    ) -> List[bool]:
        """
        Check if rows are duplicates based on vector similarity.

        Args:
            rows: List of data rows to check
            collection_name: Collection to check against
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            List of boolean flags (True = duplicate, False = unique)
        """
        try:
            if not rows:
                return []

            # Convert rows to strings for embedding
            row_strings = [self._row_to_string(row) for row in rows]

            # Generate embeddings
            embeddings = await self.llm_client.generate_embeddings(
                texts=row_strings, model=settings.EMBEDDING_MODEL
            )

            # Query vector store for similar entries
            distances_list = self.vector_store.query_similar(
                collection_name=collection_name,
                query_embeddings=embeddings,
                n_results=1,
            )

            # Determine duplicates based on threshold
            is_duplicate = []
            for distances in distances_list:
                if distances:
                    # Convert distance to similarity (for cosine: similarity = 1 - distance)
                    min_distance = min(distances)
                    similarity = 1 - min_distance

                    # If similarity exceeds threshold, it's a duplicate
                    is_duplicate.append(similarity >= threshold)
                else:
                    # No similar items found, it's unique
                    is_duplicate.append(False)

            duplicates_found = sum(is_duplicate)
            logger.debug(
                f"Checked {len(rows)} rows, found {duplicates_found} duplicates"
            )

            return is_duplicate

        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}", exc_info=True)
            # Return all False if deduplication fails
            return [False] * len(rows)

    async def add_to_store(
        self, rows: List[Dict[str, Any]], collection_name: str
    ):
        """
        Add rows to the vector store.

        Args:
            rows: Data rows to add
            collection_name: Collection to add to
        """
        try:
            if not rows:
                return

            # Convert rows to strings
            row_strings = [self._row_to_string(row) for row in rows]

            # Generate embeddings
            embeddings = await self.llm_client.generate_embeddings(
                texts=row_strings, model=settings.EMBEDDING_MODEL
            )

            # Generate unique IDs
            ids = [self._generate_id(row) for row in rows]

            # Add to vector store
            self.vector_store.add_embeddings(
                collection_name=collection_name,
                embeddings=embeddings,
                documents=row_strings,
                ids=ids,
                metadatas=[{"row_data": json.dumps(row)} for row in rows],
            )

            logger.debug(f"Added {len(rows)} rows to {collection_name}")

        except Exception as e:
            logger.error(f"Error adding to store: {str(e)}", exc_info=True)

    def _row_to_string(self, row: Dict[str, Any]) -> str:
        """
        Convert a data row to a string representation.

        Args:
            row: Data row

        Returns:
            String representation
        """
        # Sort keys for consistency
        sorted_items = sorted(row.items())

        # Create a string representation
        parts = [f"{k}: {v}" for k, v in sorted_items]

        return " | ".join(parts)

    def _generate_id(self, row: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a row.

        Args:
            row: Data row

        Returns:
            Unique ID
        """
        # Create hash of row content
        row_string = self._row_to_string(row)
        hash_object = hashlib.sha256(row_string.encode())

        return hash_object.hexdigest()[:16]

    async def get_statistics(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            collection_name: Collection name

        Returns:
            Statistics dictionary
        """
        try:
            count = self.vector_store.collection_count(collection_name)

            return {
                "collection_name": collection_name,
                "total_entries": count,
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {"error": str(e)}
