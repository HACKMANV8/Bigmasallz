"""Interactive CLI client for the Synthetic Dataset Generator.

This script lets a user provide a natural-language description of a dataset,
extracts the schema with Gemini, creates a generation job, produces data chunks,
and merges the final dataset using the existing core services.

Usage (after setting GEMINI_API_KEY and optional Langfuse env vars):

    uv run examples/interactive_client.py --rows 1000 --chunk-size 500 --format csv

If the prompt is not supplied via ``--prompt``, the script will ask interactively.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.api.gemini_client import get_gemini_client
from src.config import settings
from src.core.job_manager import get_job_manager
from src.core.models import (
    DataSchema,
    JobSpecification,
    JobStatus,
    OutputFormat,
    SchemaExtractionRequest,
    StorageType,
)
from src.storage.handlers import get_storage_handler
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive client for the synthetic dataset generator",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Natural-language dataset description",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=1000,
        help="Total number of rows to generate",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=settings.generation.default_chunk_size,
        help="Number of rows per chunk",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=[fmt.value for fmt in OutputFormat],
        default=settings.generation.default_output_format,
        help="Output dataset format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional override for merged dataset path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract schema only (skip generation)",
    )
    return parser.parse_args()


def _print_schema(schema: DataSchema) -> None:
    print("\nExtracted Schema:")
    print("=================")
    for field in schema.fields:
        constraint_bits = []
        if field.constraints.unique:
            constraint_bits.append("unique")
        if not field.constraints.nullable:
            constraint_bits.append("required")
        if field.constraints.min_value is not None or field.constraints.max_value is not None:
            constraint_bits.append(
                f"range={field.constraints.min_value or '-'}..{field.constraints.max_value or '-'}"
            )
        if field.constraints.enum_values:
            constraint_bits.append(f"enum={len(field.constraints.enum_values)} values")
        constraint_str = f" ({', '.join(constraint_bits)})" if constraint_bits else ""
        print(f"- {field.name} : {field.type.value}{constraint_str}")
        if field.description:
            print(f"    description: {field.description}")
        if field.sample_values:
            sample_preview = ", ".join(map(str, field.sample_values[:3]))
            print(f"    samples: {sample_preview}")
    print()


def _confirm(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if not answer or answer in {"n", "no"}:
            return False
        print("Please respond with 'y' or 'n'.")


def main() -> int:
    args = _parse_args()

    user_prompt = args.prompt or input("Describe the dataset you want to generate:\n> ")
    if not user_prompt.strip():
        print("Prompt is required to proceed.")
        return 1

    client = get_gemini_client()
    logger.info("Requesting schema from Gemini...")
    schema_response = client.extract_schema(
        SchemaExtractionRequest(
            user_input=user_prompt,
        )
    )

    schema = schema_response.schema
    _print_schema(schema)

    print("Confidence:", schema_response.confidence)
    if schema_response.suggestions:
        print("Suggestions:")
        for suggestion in schema_response.suggestions:
            print("  -", suggestion)
    if schema_response.warnings:
        print("Warnings:")
        for warning in schema_response.warnings:
            print("  -", warning)

    if args.dry_run:
        print("\nDry run complete – schema extracted but no data generated.")
        return 0

    if not _confirm("Proceed with job creation and data generation?"):
        print("Aborted by user.")
        return 0

    output_format = OutputFormat(args.format)
    storage_type = StorageType(settings.storage.type)

    job_spec = JobSpecification(
        schema=schema,
        total_rows=args.rows,
        chunk_size=args.chunk_size,
        output_format=output_format,
        storage_type=storage_type,
    )

    job_manager = get_job_manager()
    job_state = job_manager.create_job(job_spec)
    job_manager.validate_schema(job_state.specification.job_id)

    storage_handler = get_storage_handler(storage_type.value)

    job_manager.update_job_status(job_state.specification.job_id, JobStatus.GENERATING)

    unique_fields = [field.name for field in schema.fields if field.constraints.unique]
    existing_values: dict[str, list[Any]] = {field: [] for field in unique_fields}

    print("\nStarting data generation...")
    for chunk_idx in range(job_state.progress.total_chunks):
        job = job_manager.get_job(job_state.specification.job_id)
        if not job:
            raise RuntimeError("Job disappeared during processing")

        remaining_rows = job.specification.total_rows - job.progress.rows_generated
        chunk_rows = min(job.specification.chunk_size, remaining_rows)
        if chunk_rows <= 0:
            break

        logger.info("Generating chunk %s (%s rows)...", chunk_idx, chunk_rows)
        data = client.generate_data_chunk(
            schema=schema,
            num_rows=chunk_rows,
            existing_values=existing_values or None,
            seed=job.specification.seed,
        )

        for field in unique_fields:
            existing_values[field].extend(
                [row[field] for row in data if field in row and row[field] is not None]
            )

        metadata = storage_handler.store_chunk(
            job_id=job.specification.job_id,
            chunk_id=chunk_idx,
            data=data,
            format=output_format,
        )

        job_manager.add_chunk(job.specification.job_id, metadata)
        print(
            f"  ✓ Chunk {chunk_idx + 1}/{job.progress.total_chunks} | "
            f"rows generated: {metadata.rows_generated}"
        )

    job_manager.update_job_status(job_state.specification.job_id, JobStatus.COMPLETED)

    print("\nMerging chunks...")
    output_path = args.output or (settings.storage.output_path / f"{job_state.specification.job_id}.{output_format.value}")
    job = job_manager.get_job(job_state.specification.job_id)
    if not job:
        raise RuntimeError("Job not found after generation")

    merged_path = storage_handler.merge_chunks(
        job_id=job_state.specification.job_id,
        chunks=job.chunks,
        output_path=output_path,
        format=output_format,
    )

    file_size = merged_path.stat().st_size
    print("\nGeneration complete!")
    print("====================")
    print("Job ID:", job_state.specification.job_id)
    print("Output:", merged_path)
    print("Size:", f"{file_size / (1024 * 1024):.2f} MB")
    print("Format:", output_format.value)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        sys.exit(1)
