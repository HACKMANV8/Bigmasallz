export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  total_chunks: number;
  completed_chunks: number;
  progress_percentage: number;
  rows_generated: number;
  rows_deduplicated: number;
  created_at: string;
  estimated_completion?: string;
  results?: any;
  error_message?: string;
}
