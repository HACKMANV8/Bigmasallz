"""Shared service layer for schema extraction and job generation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable
from uuid import UUID

from src.api import QuotaExceededError, get_gemini_client
from src.config import settings
from src.core.job_manager import get_job_manager
from src.core.models import (
    ChunkGenerationResponse,
    DataSchema,
    DatasetDownloadInfo,
    FieldConstraint,
    FieldDefinition,
    FieldType,
    JobControlRequest,
    JobProgress,
    JobSpecification,
    JobState,
    JobStatus,
    OutputFormat,
    SchemaExtractionRequest,
    SchemaExtractionResponse,
    StorageType,
)
from src.services.fallback_generator import FallbackGenerator, build_fallback_generator
from src.storage.handlers import StorageHandler, get_storage_handler
from src.storage.vector_store import get_vector_store
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _parse_field(field_data: dict[str, Any]) -> FieldDefinition:
    """Parse incoming dict into FieldDefinition."""
    try:
        field_type = FieldType(field_data["type"])
    except KeyError as exc:  # pragma: no cover - guarded upstream
        raise ValueError("Field definition missing required 'type'") from exc
    except ValueError as exc:
        raise ValueError(f"Unsupported field type: {field_data['type']}") from exc

    constraints = FieldConstraint(**field_data.get("constraints", {}))

    return FieldDefinition(
        name=field_data["name"],
        type=field_type,
        description=field_data.get("description"),
        constraints=constraints,
        sample_values=field_data.get("sample_values", []),
        depends_on=field_data.get("depends_on"),
        generation_hint=field_data.get("generation_hint"),
    )


def build_schema_from_dict(schema_data: dict[str, Any]) -> DataSchema:
    """Convert raw schema payload from API into DataSchema object."""
    if "fields" not in schema_data:
        raise ValueError("Schema payload missing 'fields'")

    fields = [_parse_field(field) for field in schema_data["fields"]]

    return DataSchema(
        fields=fields,
        description=schema_data.get("description"),
        relationships=schema_data.get("relationships"),
        metadata=schema_data.get("metadata", {}),
    )


class GenerationService:
    """Facade for schema extraction, job orchestration, and chunk management."""

    def __init__(self):
        self.job_manager = get_job_manager()
        self.gemini_client = get_gemini_client()
        self._storage_handlers: dict[str, StorageHandler] = {}
        self._vector_store = self._init_vector_store()
        self._fallback_generator: FallbackGenerator = build_fallback_generator()

    def _init_vector_store(self):
        if not settings.vector_store.enabled:
            return None
        try:
            return get_vector_store()
        except Exception as exc:  # pragma: no cover - protective logging
            logger.error("Failed to initialise vector store: %s", exc)
            return None

    def _get_storage_handler(self, storage_type: StorageType) -> StorageHandler:
        key = storage_type.value
        if key not in self._storage_handlers:
            self._storage_handlers[key] = get_storage_handler(key)
        return self._storage_handlers[key]

    def extract_schema_from_prompt(
        self,
        *,
        user_input: str,
        context: dict[str, Any] | None = None,
        example_data: str | None = None,
    ) -> SchemaExtractionResponse:
        """Run the Gemini schema extraction flow."""
        request = SchemaExtractionRequest(
            user_input=user_input,
            context=context,
            example_data=example_data,
        )
        logger.info("Running schema extraction via Gemini")
        try:
            return self.gemini_client.extract_schema(request)
        except QuotaExceededError as exc:
            logger.warning("Gemini quota exceeded during schema extraction; switching to fallback", exc_info=False)
            fallback_response = self._fallback_generator.extract_schema(request)
            quota_message = self._format_quota_warning(exc)
            fallback_response.warnings.insert(0, quota_message)
            fallback_response.suggestions.append("Re-run schema extraction once Gemini quota resets for richer results.")
            fallback_response.schema.metadata.setdefault("fallback", {})
            fallback_response.schema.metadata["fallback"].update(
                {
                    "reason": "quota_exceeded",
                    "quota_metric": exc.quota_metric,
                    "retry_after_seconds": exc.retry_after,
                }
            )
            return fallback_response

    def create_generation_job(
        self,
        *,
        schema: DataSchema | dict[str, Any],
        total_rows: int,
        chunk_size: int | None = None,
        output_format: str | OutputFormat | None = None,
        uniqueness_fields: Iterable[str] | None = None,
        seed: int | None = None,
        name: str | None = None,
        description: str | None = None,
        created_by: str | None = None,
        metadata: dict[str, Any] | None = None,
        storage_type: str | StorageType | None = None,
    ) -> JobState:
        """Create a new generation job from schema and parameters."""
        if total_rows <= 0:
            raise ValueError("total_rows must be greater than zero")

        schema_obj = schema if isinstance(schema, DataSchema) else build_schema_from_dict(schema)
        issues = schema_obj.validate_constraints()
        if issues:
            raise ValueError(f"Schema validation failed: {issues}")

        specification = _create_job_spec(
            schema=schema_obj,
            total_rows=total_rows,
            chunk_size=chunk_size,
            output_format=output_format,
            uniqueness_fields=uniqueness_fields,
            seed=seed,
            name=name,
            description=description,
            created_by=created_by,
            metadata=metadata,
            storage_type=storage_type,
        )

        job_state = self.job_manager.create_job(specification)
        self.job_manager.validate_schema(job_state.specification.job_id)
        job_state.schema_validated = True
        return job_state

    def get_job(self, job_id: UUID) -> JobState | None:
        """Retrieve a job by its ID."""
        return self.job_manager.get_job(job_id)

    def get_job_progress(self, job_id: UUID) -> JobProgress:
        """Fetch job progress, raising if job is missing."""
        job = self.job_manager.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        return job.progress

    def list_jobs(self, *, status: JobStatus | None = None, limit: int = 100) -> list[JobState]:
        """List jobs with optional status filtering."""
        return self.job_manager.list_jobs(status=status, limit=limit)

    def control_job(self, request: JobControlRequest) -> bool:
        """Relay job control command to job manager."""
        return self.job_manager.control_job(request)

    def generate_chunk(self, *, job_id: UUID, chunk_id: int) -> ChunkGenerationResponse:
        """Generate and persist a chunk for the given job."""
        job = self.job_manager.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.progress.status == JobStatus.COMPLETED:
            raise ValueError(f"Job {job_id} is already completed")

        if any(chunk.chunk_id == chunk_id for chunk in job.chunks):
            raise ValueError(f"Chunk {chunk_id} has already been generated for job {job_id}")

        remaining_rows = job.specification.total_rows - job.progress.rows_generated
        if remaining_rows <= 0:
            self.job_manager.update_job_status(job_id, JobStatus.COMPLETED)
            raise ValueError(f"Job {job_id} has already generated all rows")

        rows_this_chunk = min(job.specification.chunk_size, remaining_rows)

        if job.progress.status == JobStatus.PENDING:
            self.job_manager.update_job_status(job_id, JobStatus.GENERATING)

        self.job_manager.set_current_chunk(job_id, chunk_id)

        uniqueness_fields = list(job.specification.uniqueness_fields or [])
        vector_store = self._vector_store
        if vector_store and not uniqueness_fields:
            uniqueness_fields = [
                field.name for field in job.specification.schema.fields if field.constraints.unique
            ]

        existing_values = (
            self._collect_existing_values(job, uniqueness_fields) if uniqueness_fields else None
        )

        deduped_rows: list[dict[str, Any]] = []
        duplicates_total = 0
        attempts = 0
        max_attempts = settings.vector_store.max_retry_attempts if vector_store else 1

        use_fallback_only = False
        fallback_issue: str | None = None

        try:
            while len(deduped_rows) < rows_this_chunk and attempts < max_attempts:
                attempts += 1
                rows_needed = rows_this_chunk - len(deduped_rows)

                if use_fallback_only:
                    batch = self._fallback_generator.generate_data_chunk(
                        schema=job.specification.schema,
                        num_rows=rows_needed,
                        existing_values=existing_values if existing_values else None,
                        seed=job.specification.seed,
                    )
                else:
                    try:
                        batch = self.gemini_client.generate_data_chunk(
                            schema=job.specification.schema,
                            num_rows=rows_needed,
                            existing_values=existing_values if existing_values else None,
                            seed=job.specification.seed,
                        )
                    except QuotaExceededError as exc:
                        logger.warning(
                            "Gemini quota exceeded while generating chunk %s for job %s; switching to fallback",
                            chunk_id,
                            job_id,
                        )
                        use_fallback_only = True
                        fallback_issue = self._format_quota_warning(exc)
                        batch = self._fallback_generator.generate_data_chunk(
                            schema=job.specification.schema,
                            num_rows=rows_needed,
                            existing_values=existing_values if existing_values else None,
                            seed=job.specification.seed,
                        )

                if vector_store and batch:
                    batch, duplicates = vector_store.filter_new_rows(
                        job_id=str(job_id),
                        rows=batch,
                        unique_fields=uniqueness_fields,
                    )
                    duplicates_total += len(duplicates)

                if not batch:
                    logger.debug(
                        "Job %s chunk %s produced no usable rows on attempt %s",
                        job_id,
                        chunk_id,
                        attempts,
                    )
                    if not vector_store:
                        break
                else:
                    deduped_rows.extend(batch)
                    if existing_values:
                        for row in batch:
                            for field, values in existing_values.items():
                                value = row.get(field)
                                if value is not None:
                                    values.append(value)

            if not deduped_rows:
                raise RuntimeError(
                    "No new rows generated for this chunk after applying uniqueness checks"
                )

            storage_handler = self._get_storage_handler(job.specification.storage_type)
            metadata = storage_handler.store_chunk(
                job_id=job_id,
                chunk_id=chunk_id,
                data=deduped_rows,
                format=job.specification.output_format,
            )

            self.job_manager.add_chunk(job_id, metadata)
            self.job_manager.set_current_chunk(job_id, None)

            if (
                job.progress.chunks_completed >= job.progress.total_chunks
                or job.progress.rows_generated >= job.specification.total_rows
            ):
                self.job_manager.update_job_status(job_id, JobStatus.COMPLETED)

            issues: list[str] = []
            if duplicates_total:
                issues.append(f"Removed {duplicates_total} duplicate rows via vector store")
            if fallback_issue:
                issues.append(fallback_issue)

            return ChunkGenerationResponse(
                chunk_id=chunk_id,
                data=deduped_rows,
                rows_generated=len(deduped_rows),
                metadata=metadata,
                issues=issues,
            )

        except Exception as exc:
            logger.error("Chunk generation failed for job %s: %s", job_id, exc, exc_info=True)
            self.job_manager.update_job_status(job_id, JobStatus.FAILED, str(exc))
            raise

    def run_job(self, job_id: UUID) -> DatasetDownloadInfo:
        """Generate all chunks for a job and merge the final dataset."""
        job = self.job_manager.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.progress.status == JobStatus.CANCELLED:
            raise ValueError(f"Job {job_id} has been cancelled")

        if job.progress.status in {
            JobStatus.PENDING,
            JobStatus.SCHEMA_VALIDATION,
            JobStatus.PAUSED,
            JobStatus.FAILED,
        }:
            self.job_manager.update_job_status(job_id, JobStatus.GENERATING)

        try:
            for chunk_index in range(1, job.progress.total_chunks + 1):
                current_state = self.job_manager.get_job(job_id)
                if not current_state:
                    raise RuntimeError(f"Job {job_id} state unavailable during execution")

                if current_state.progress.status == JobStatus.CANCELLED:
                    raise RuntimeError(f"Job {job_id} was cancelled during execution")

                if any(chunk.chunk_id == chunk_index for chunk in current_state.chunks):
                    continue

                self.generate_chunk(job_id=job_id, chunk_id=chunk_index)

            final_state = self.job_manager.get_job(job_id)
            if final_state and final_state.progress.status != JobStatus.COMPLETED:
                self.job_manager.update_job_status(job_id, JobStatus.COMPLETED)

            download_info = self.merge_job_dataset(job_id)
            download_info.download_url = f"/jobs/{job_id}/download"
            return download_info

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Job %s failed during execution: %s", job_id, exc, exc_info=True)
            self.job_manager.update_job_status(job_id, JobStatus.FAILED, str(exc))
            raise

    def merge_job_dataset(self, job_id: UUID) -> DatasetDownloadInfo:
        """Merge completed chunks and return download details."""
        job = self.job_manager.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.progress.status != JobStatus.COMPLETED:
            if job.progress.rows_generated < job.specification.total_rows:
                raise ValueError(
                    f"Job {job_id} is not completed yet (status: {job.progress.status.value})"
                )
            self.job_manager.update_job_status(job_id, JobStatus.COMPLETED)

        output_dir: Path = settings.storage.output_path
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{job_id}.{job.specification.output_format.value}"

        storage_handler = self._get_storage_handler(job.specification.storage_type)
        merged_path = storage_handler.merge_chunks(
            job_id=job_id,
            chunks=job.chunks,
            output_path=output_path,
            format=job.specification.output_format,
        )

        file_size = merged_path.stat().st_size
        with open(merged_path, "rb") as file_obj:
            checksum = hashlib.sha256(file_obj.read()).hexdigest()

        return DatasetDownloadInfo(
            job_id=job_id,
            download_url=f"/jobs/{job_id}/download",
            file_path=str(merged_path),
            file_size_bytes=file_size,
            format=job.specification.output_format,
            total_rows=job.progress.rows_generated,
            checksum=checksum,
        )

    def validate_schema(self, schema: DataSchema | dict[str, Any]) -> list[str]:
        """Validate a schema, returning any issues."""
        schema_obj = schema if isinstance(schema, DataSchema) else build_schema_from_dict(schema)
        return schema_obj.validate_constraints()

    @staticmethod
    def _format_quota_warning(exc: QuotaExceededError) -> str:
        parts = ["Gemini quota exceeded"]
        if exc.quota_metric:
            parts.append(f"({exc.quota_metric})")
        if exc.retry_after:
            parts.append(f"retry after ~{int(exc.retry_after)}s")
        return " ".join(parts)

    def _collect_existing_values(
        self, job: JobState, uniqueness_fields: Iterable[str]
    ) -> dict[str, list[Any]]:
        existing: dict[str, list[Any]] = {field: [] for field in uniqueness_fields}
        if not uniqueness_fields:
            return existing

        storage_handler = self._get_storage_handler(job.specification.storage_type)
        for chunk in job.chunks:
            try:
                rows = storage_handler.retrieve_chunk(
                    metadata=chunk,
                    format=job.specification.output_format,
                )
            except FileNotFoundError:
                logger.warning(
                    "Stored chunk missing for job %s chunk %s when collecting uniqueness values",
                    job.specification.job_id,
                    chunk.chunk_id,
                )
                continue
            except Exception as exc:  # pragma: no cover - defensive path
                logger.error("Failed to retrieve chunk %s for job %s: %s", chunk.chunk_id, job.specification.job_id, exc)
                continue

            for row in rows:
                for field in uniqueness_fields:
                    value = row.get(field)
                    if value is not None:
                        existing[field].append(value)

        return existing


def _create_job_spec(
    *,
    schema: DataSchema,
    total_rows: int,
    chunk_size: int | None,
    output_format: str | OutputFormat | None,
    uniqueness_fields: Iterable[str] | None,
    seed: int | None,
    name: str | None,
    description: str | None,
    created_by: str | None,
    metadata: dict[str, Any] | None,
    storage_type: str | StorageType | None,
) -> JobSpecification:
    """Construct a JobSpecification from raw inputs."""
    default_format = OutputFormat(settings.generation.default_output_format)
    fmt = OutputFormat(output_format) if output_format else default_format

    configured_chunk = chunk_size or settings.generation.default_chunk_size
    configured_chunk = max(configured_chunk, settings.generation.min_chunk_size)
    configured_chunk = min(configured_chunk, settings.generation.max_chunk_size)

    storage_type_obj = StorageType(storage_type) if storage_type else StorageType(settings.storage.type)

    metadata_obj = dict(metadata or {})
    if name:
        metadata_obj.setdefault("name", name)
    if description:
        metadata_obj.setdefault("description", description)

    return JobSpecification(
        schema=schema,
        total_rows=total_rows,
        chunk_size=configured_chunk,
        output_format=fmt,
        storage_type=storage_type_obj,
        uniqueness_fields=list(uniqueness_fields or []),
        seed=seed,
        created_by=created_by,
        metadata=metadata_obj,
    )


_generation_service: GenerationService | None = None


def get_generation_service() -> GenerationService:
    """Return the singleton generation service instance."""
    global _generation_service
    if _generation_service is None:
        _generation_service = GenerationService()
    return _generation_service


def extract_schema_from_prompt(
    *,
    user_input: str,
    context: dict[str, Any] | None = None,
    example_data: str | None = None,
) -> SchemaExtractionResponse:
    """Module-level helper delegating to the shared service."""
    service = get_generation_service()
    return service.extract_schema_from_prompt(
        user_input=user_input,
        context=context,
        example_data=example_data,
    )


def create_generation_job(
    *,
    schema: DataSchema | dict[str, Any],
    total_rows: int,
    chunk_size: int | None = None,
    output_format: str | OutputFormat | None = None,
    uniqueness_fields: Iterable[str] | None = None,
    seed: int | None = None,
    name: str | None = None,
    description: str | None = None,
    created_by: str | None = None,
    metadata: dict[str, Any] | None = None,
    storage_type: str | StorageType | None = None,
) -> JobState:
    """Convenience wrapper for job creation."""
    service = get_generation_service()
    return service.create_generation_job(
        schema=schema,
        total_rows=total_rows,
        chunk_size=chunk_size,
        output_format=output_format,
        uniqueness_fields=uniqueness_fields,
        seed=seed,
        name=name,
        description=description,
        created_by=created_by,
        metadata=metadata,
        storage_type=storage_type,
    )


def generate_job_chunk(*, job_id: UUID, chunk_id: int) -> ChunkGenerationResponse:
    """Generate a chunk for a job via the shared service."""
    service = get_generation_service()
    return service.generate_chunk(job_id=job_id, chunk_id=chunk_id)


def merge_job_dataset(job_id: UUID) -> DatasetDownloadInfo:
    """Merge all job chunks and return download metadata."""
    service = get_generation_service()
    return service.merge_job_dataset(job_id)


def get_job(job_id: UUID) -> JobState | None:
    """Retrieve a job state using the shared service."""
    service = get_generation_service()
    return service.get_job(job_id)


def get_job_progress(job_id: UUID) -> JobProgress:
    """Retrieve job progress."""
    service = get_generation_service()
    return service.get_job_progress(job_id)


def list_jobs(*, status: JobStatus | None = None, limit: int = 100) -> list[JobState]:
    """List jobs via the shared service."""
    service = get_generation_service()
    return service.list_jobs(status=status, limit=limit)


def control_job(request: JobControlRequest) -> bool:
    """Proxy job control requests."""
    service = get_generation_service()
    return service.control_job(request)


def validate_schema(schema: DataSchema | dict[str, Any]) -> list[str]:
    """Validate schema using shared service utilities."""
    service = get_generation_service()
    return service.validate_schema(schema)
