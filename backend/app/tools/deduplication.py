"""
FastMCP Deduplication Tool using ChromaDB for vector-based duplicate detection.
"""

import hashlib
import json
from typing import List, Dict, Any, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class DeduplicationTool:
    """
    Vector-based deduplication tool using ChromaDB.
    Generates embeddings for data rows and detects semantic duplicates.
    """
    
    def __init__(self, collection_name: str = None):
        """
        Initialize the deduplication tool.
        
        Args:
            collection_name: Name of the ChromaDB collection (defaults to config)
        """
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use default embedding function (sentence transformers)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except ValueError:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        self.total_checks = 0
        self.total_duplicates = 0
    
    def _row_to_text(self, row: Dict[str, Any]) -> str:
        """
        Convert a data row to a text representation for embedding.
        
        Args:
            row: Dictionary representing a data row
            
        Returns:
            String representation of the row
        """
        # Sort keys for consistent ordering
        sorted_items = sorted(row.items())
        return " | ".join([f"{k}: {v}" for k, v in sorted_items])
    
    def _row_to_id(self, row: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a row based on its content.
        
        Args:
            row: Dictionary representing a data row
            
        Returns:
            Unique hash string
        """
        row_str = json.dumps(row, sort_keys=True)
        return hashlib.sha256(row_str.encode()).hexdigest()
    
    def check_duplicates(
        self, 
        rows: List[Dict[str, Any]], 
        n_results: int = 5
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Check for duplicates and return only unique rows.
        
        Args:
            rows: List of data rows to check
            n_results: Number of similar results to check per row
            
        Returns:
            Tuple of (unique_rows, duplicate_count)
        """
        unique_rows = []
        duplicate_count = 0
        
        for row in rows:
            self.total_checks += 1
            
            # Convert row to text for embedding
            row_text = self._row_to_text(row)
            row_id = self._row_to_id(row)
            
            try:
                # Query collection for similar rows
                collection_count = self.collection.count()
                
                # Skip query if collection is empty
                if collection_count == 0:
                    unique_rows.append(row)
                    # Add to collection
                    self.collection.add(
                        documents=[row_text],
                        ids=[row_id],
                        metadatas=[{"row": json.dumps(row)}]
                    )
                    continue
                
                results = self.collection.query(
                    query_texts=[row_text],
                    n_results=min(n_results, collection_count),
                    include=["distances"]
                )
                
                # Check if any result is above similarity threshold
                is_duplicate = False
                if results["distances"] and results["distances"][0]:
                    # ChromaDB returns distances (lower = more similar)
                    # Convert to similarity: similarity = 1 - distance
                    for distance in results["distances"][0]:
                        similarity = 1 - distance
                        if similarity >= self.similarity_threshold:
                            is_duplicate = True
                            duplicate_count += 1
                            self.total_duplicates += 1
                            logger.debug(
                                f"Duplicate detected with similarity: {similarity:.3f}",
                                extra={"extra_fields": {"row_id": row_id}}
                            )
                            break
                
                if not is_duplicate:
                    unique_rows.append(row)
                    
                    # Add to collection
                    self.collection.add(
                        documents=[row_text],
                        ids=[row_id],
                        metadatas=[{"row": json.dumps(row)}]
                    )
            
            except Exception as e:
                logger.error(
                    f"Error checking duplicate: {str(e)}",
                    extra={"extra_fields": {"row_id": row_id}}
                )
                # On error, assume not duplicate to avoid data loss
                unique_rows.append(row)
        
        return unique_rows, duplicate_count
    
    def add_rows(self, rows: List[Dict[str, Any]]) -> None:
        """
        Add rows to the collection without duplicate checking.
        
        Args:
            rows: List of data rows to add
        """
        if not rows:
            return
        
        documents = [self._row_to_text(row) for row in rows]
        ids = [self._row_to_id(row) for row in rows]
        metadatas = [{"row": json.dumps(row)} for row in rows]
        
        try:
            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            logger.info(f"Added {len(rows)} rows to collection")
        except Exception as e:
            logger.error(f"Error adding rows to collection: {str(e)}")
    
    def reset_collection(self) -> None:
        """Reset the collection (clear all data)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            self.total_checks = 0
            self.total_duplicates = 0
            logger.info(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get deduplication statistics.
        
        Returns:
            Dictionary with statistics
        """
        collection_count = self.collection.count()
        deduplication_rate = (
            self.total_duplicates / self.total_checks 
            if self.total_checks > 0 
            else 0.0
        )
        
        return {
            "total_checks": self.total_checks,
            "total_duplicates": self.total_duplicates,
            "unique_rows": collection_count,
            "deduplication_rate": deduplication_rate,
            "similarity_threshold": self.similarity_threshold
        }
