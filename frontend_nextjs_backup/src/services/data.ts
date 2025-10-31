import apiClient from './api';
import type {
  DataGenerationRequest,
  DataGenerationResponse,
} from '@/types/data';

export const dataService = {
  /**
   * Start data generation job
   */
  async generateData(
    request: DataGenerationRequest
  ): Promise<DataGenerationResponse> {
    const response = await apiClient.post<DataGenerationResponse>(
      '/api/data/generate',
      request
    );
    return response.data;
  },

  /**
   * Cancel a running job
   */
  async cancelJob(jobId: string): Promise<void> {
    await apiClient.post(`/api/data/${jobId}/cancel`);
  },
};
