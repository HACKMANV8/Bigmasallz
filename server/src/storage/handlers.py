"""Storage handlers for chunk and dataset management."""

import csv
import hashlib
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from uuid import UUID

from src.config import settings
from src.core.models import ChunkMetadata, OutputFormat
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StorageHandler(ABC):
    """Abstract base class for storage handlers."""

    @abstractmethod
    def store_chunk(
        self,
        job_id: UUID,
        chunk_id: int,
        data: list[dict[str, Any]],
        format: OutputFormat
    ) -> ChunkMetadata:
        """Store a data chunk.
        
        Args:
            job_id: Job identifier
            chunk_id: Chunk identifier
            data: Chunk data
            format: Output format
            
        Returns:
            Chunk metadata
        """
        pass

    @abstractmethod
    def retrieve_chunk(
        self,
        metadata: ChunkMetadata,
        format: OutputFormat
    ) -> list[dict[str, Any]]:
        """Retrieve a data chunk.
        
        Args:
            metadata: Chunk metadata
            format: Output format
            
        Returns:
            Chunk data
        """
        pass

    @abstractmethod
    def merge_chunks(
        self,
        job_id: UUID,
        chunks: list[ChunkMetadata],
        output_path: Path,
        format: OutputFormat
    ) -> Path:
        """Merge multiple chunks into a single file.
        
        Args:
            job_id: Job identifier
            chunks: List of chunk metadata
            output_path: Output file path
            format: Output format
            
        Returns:
            Path to merged file
        """
        pass

    @abstractmethod
    def delete_chunk(self, metadata: ChunkMetadata):
        """Delete a stored chunk.
        
        Args:
            metadata: Chunk metadata
        """
        pass

    @abstractmethod
    def cleanup_job(self, job_id: UUID):
        """Clean up all chunks for a job.
        
        Args:
            job_id: Job identifier
        """
        pass


class DiskStorageHandler(StorageHandler):
    """Disk-based storage handler."""

    def __init__(self, base_path: Path | None = None):
        """Initialize disk storage handler.
        
        Args:
            base_path: Base path for storage (uses config default if not provided)
        """
        self.base_path = base_path or settings.storage.temp_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized DiskStorageHandler at {self.base_path}")

    def store_chunk(
        self,
        job_id: UUID,
        chunk_id: int,
        data: list[dict[str, Any]],
        format: OutputFormat
    ) -> ChunkMetadata:
        """Store chunk to disk."""
        # Create job directory
        job_dir = self.base_path / str(job_id)
        job_dir.mkdir(exist_ok=True)

        # Determine file extension
        ext = self._get_extension(format)
        file_path = job_dir / f"chunk_{chunk_id:06d}.{ext}"

        # Write data
        if format == OutputFormat.CSV:
            self._write_csv(file_path, data)
        elif format == OutputFormat.JSON:
            self._write_json(file_path, data)
        elif format == OutputFormat.PARQUET:
            self._write_parquet(file_path, data)

        # Calculate checksum and size
        checksum = self._calculate_checksum(file_path)
        size_bytes = file_path.stat().st_size

        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            job_id=job_id,
            rows_generated=len(data),
            storage_location=str(file_path),
            checksum=checksum,
            size_bytes=size_bytes
        )

        logger.debug(f"Stored chunk {chunk_id} at {file_path} ({size_bytes} bytes)")
        return metadata

    def retrieve_chunk(
        self,
        metadata: ChunkMetadata,
        format: OutputFormat
    ) -> list[dict[str, Any]]:
        """Retrieve chunk from disk."""
        file_path = Path(metadata.storage_location)

        if not file_path.exists():
            raise FileNotFoundError(f"Chunk file not found: {file_path}")

        if format == OutputFormat.CSV:
            return self._read_csv(file_path)
        elif format == OutputFormat.JSON:
            return self._read_json(file_path)
        elif format == OutputFormat.PARQUET:
            return self._read_parquet(file_path)

        raise ValueError(f"Unsupported format: {format}")

    def merge_chunks(
        self,
        job_id: UUID,
        chunks: list[ChunkMetadata],
        output_path: Path,
        format: OutputFormat
    ) -> Path:
        """Merge chunks into single file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Sort chunks by ID
        chunks = sorted(chunks, key=lambda c: c.chunk_id)

        if format == OutputFormat.CSV:
            self._merge_csv(chunks, output_path)
        elif format == OutputFormat.JSON:
            self._merge_json(chunks, output_path)
        elif format == OutputFormat.PARQUET:
            self._merge_parquet(chunks, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Merged {len(chunks)} chunks to {output_path}")
        return output_path

    def delete_chunk(self, metadata: ChunkMetadata):
        """Delete chunk file."""
        file_path = Path(metadata.storage_location)
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Deleted chunk {metadata.chunk_id}")

    def cleanup_job(self, job_id: UUID):
        """Clean up all job files."""
        job_dir = self.base_path / str(job_id)
        if job_dir.exists():
            for file in job_dir.glob("*"):
                file.unlink()
            job_dir.rmdir()
            logger.info(f"Cleaned up job {job_id} storage")

    def _get_extension(self, format: OutputFormat) -> str:
        """Get file extension for format."""
        return {
            OutputFormat.CSV: "csv",
            OutputFormat.JSON: "json",
            OutputFormat.PARQUET: "parquet"
        }[format]

    def _write_csv(self, path: Path, data: list[dict[str, Any]]):
        """Write data to CSV file."""
        if not data:
            return

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    def _read_csv(self, path: Path) -> list[dict[str, Any]]:
        """Read data from CSV file."""
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _write_json(self, path: Path, data: list[dict[str, Any]]):
        """Write data to JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        """Read data from JSON file."""
        with open(path, encoding='utf-8') as f:
            return json.load(f)

    def _write_parquet(self, path: Path, data: list[dict[str, Any]]):
        """Write data to Parquet file."""
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            df.to_parquet(path, index=False)
        except ImportError:
            raise ImportError("pandas and pyarrow are required for Parquet support")

    def _read_parquet(self, path: Path) -> list[dict[str, Any]]:
        """Read data from Parquet file."""
        try:
            import pandas as pd
            df = pd.read_parquet(path)
            return df.to_dict('records')
        except ImportError:
            raise ImportError("pandas and pyarrow are required for Parquet support")

    def _merge_csv(self, chunks: list[ChunkMetadata], output_path: Path):
        """Merge CSV chunks."""
        first_chunk = True
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            for chunk in chunks:
                chunk_path = Path(chunk.storage_location)
                with open(chunk_path, encoding='utf-8') as infile:
                    if first_chunk:
                        # Include header from first chunk
                        outfile.write(infile.read())
                        first_chunk = False
                    else:
                        # Skip header for subsequent chunks
                        next(infile)  # Skip header line
                        outfile.write(infile.read())

    def _merge_json(self, chunks: list[ChunkMetadata], output_path: Path):
        """Merge JSON chunks."""
        all_data = []
        for chunk in chunks:
            chunk_data = self._read_json(Path(chunk.storage_location))
            all_data.extend(chunk_data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, default=str)

    def _merge_parquet(self, chunks: list[ChunkMetadata], output_path: Path):
        """Merge Parquet chunks."""
        try:
            import pandas as pd
            dfs = []
            for chunk in chunks:
                df = pd.read_parquet(Path(chunk.storage_location))
                dfs.append(df)

            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df.to_parquet(output_path, index=False)
        except ImportError:
            raise ImportError("pandas and pyarrow are required for Parquet support")

    def _calculate_checksum(self, path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


class MemoryStorageHandler(StorageHandler):
    """In-memory storage handler for small datasets."""

    def __init__(self, max_chunks: int = None):
        """Initialize memory storage handler.
        
        Args:
            max_chunks: Maximum chunks to keep in memory (uses config default if not provided)
        """
        self.max_chunks = max_chunks or settings.storage.max_memory_chunks
        self.storage: dict[tuple, list[dict[str, Any]]] = {}
        logger.info(f"Initialized MemoryStorageHandler (max {self.max_chunks} chunks)")

    def store_chunk(
        self,
        job_id: UUID,
        chunk_id: int,
        data: list[dict[str, Any]],
        format: OutputFormat
    ) -> ChunkMetadata:
        """Store chunk in memory."""
        key = (str(job_id), chunk_id)

        if len(self.storage) >= self.max_chunks:
            logger.warning("Memory storage limit reached, consider using disk storage")

        self.storage[key] = data

        # Calculate approximate size
        size_bytes = len(json.dumps(data, default=str))

        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            job_id=job_id,
            rows_generated=len(data),
            storage_location=f"memory://{job_id}/{chunk_id}",
            size_bytes=size_bytes
        )

        logger.debug(f"Stored chunk {chunk_id} in memory ({size_bytes} bytes)")
        return metadata

    def retrieve_chunk(
        self,
        metadata: ChunkMetadata,
        format: OutputFormat
    ) -> list[dict[str, Any]]:
        """Retrieve chunk from memory."""
        key = (str(metadata.job_id), metadata.chunk_id)

        if key not in self.storage:
            raise KeyError(f"Chunk not found in memory: {key}")

        return self.storage[key]

    def merge_chunks(
        self,
        job_id: UUID,
        chunks: list[ChunkMetadata],
        output_path: Path,
        format: OutputFormat
    ) -> Path:
        """Merge chunks and write to disk."""
        # Sort chunks by ID
        chunks = sorted(chunks, key=lambda c: c.chunk_id)

        # Collect all data
        all_data = []
        for chunk in chunks:
            data = self.retrieve_chunk(chunk, format)
            all_data.extend(data)

        # Write to disk
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == OutputFormat.CSV:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if all_data:
                    writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
                    writer.writeheader()
                    writer.writerows(all_data)
        elif format == OutputFormat.JSON:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, default=str)
        elif format == OutputFormat.PARQUET:
            try:
                import pandas as pd
                df = pd.DataFrame(all_data)
                df.to_parquet(output_path, index=False)
            except ImportError:
                raise ImportError("pandas and pyarrow are required for Parquet support")

        logger.info(f"Merged {len(chunks)} chunks to {output_path}")
        return output_path

    def delete_chunk(self, metadata: ChunkMetadata):
        """Delete chunk from memory."""
        key = (str(metadata.job_id), metadata.chunk_id)
        if key in self.storage:
            del self.storage[key]
            logger.debug(f"Deleted chunk {metadata.chunk_id} from memory")

    def cleanup_job(self, job_id: UUID):
        """Clean up all chunks for job."""
        keys_to_delete = [k for k in self.storage.keys() if k[0] == str(job_id)]
        for key in keys_to_delete:
            del self.storage[key]
        logger.info(f"Cleaned up job {job_id} from memory ({len(keys_to_delete)} chunks)")


def get_storage_handler(storage_type: str | None = None) -> StorageHandler:
    """Get storage handler based on configuration.
    
    Args:
        storage_type: Storage type override (uses config if not provided)
        
    Returns:
        Configured storage handler
    """
    storage_type = storage_type or settings.storage.type

    if storage_type == "disk":
        return DiskStorageHandler()
    elif storage_type == "memory":
        return MemoryStorageHandler()
    elif storage_type == "cloud":
        # TODO: Implement cloud storage handler
        logger.warning("Cloud storage not yet implemented, falling back to disk")
        return DiskStorageHandler()
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
