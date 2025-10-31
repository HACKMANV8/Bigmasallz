import type { DataSchema } from './schema';

export interface DataGenerationRequest {
  schema: DataSchema;
  total_rows: number;
  chunk_size?: number;
  max_workers?: number;
  deduplication_threshold?: number;
  seed?: number;
}

export interface DataGenerationResponse {
  job_id: string;
  status: string;
  total_rows: number;
  total_chunks: number;
  created_at: string;
  message: string;
}
