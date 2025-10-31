import apiClient from './api';
import type { JobStatusResponse } from '@/types/job';

export const jobService = {
  /**
   * Get job status
   */
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await apiClient.get<JobStatusResponse>(
      `/api/jobs/${jobId}/status`
    );
    return response.data;
  },

  /**
   * Download job results
   */
  async downloadResults(jobId: string, format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const response = await apiClient.get(`/api/jobs/${jobId}/download`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * List all jobs
   */
  async listJobs(params?: {
    limit?: number;
    offset?: number;
    status_filter?: string;
  }): Promise<any> {
    const response = await apiClient.get('/api/jobs/', { params });
    return response.data;
  },
};
