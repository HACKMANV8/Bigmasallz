import apiClient from './api';
import type { SchemaTranslationRequest, SchemaTranslationResponse } from '@/types/schema';

export const schemaService = {
  /**
   * Translate natural language prompt to structured schema
   */
  async translateSchema(
    request: SchemaTranslationRequest
  ): Promise<SchemaTranslationResponse> {
    const response = await apiClient.post<SchemaTranslationResponse>(
      '/api/schema/translate',
      request
    );
    return response.data;
  },

  /**
   * Validate a schema
   */
  async validateSchema(schema: any): Promise<{ valid: boolean; errors?: string[] }> {
    const response = await apiClient.post('/api/schema/validate', schema);
    return response.data;
  },
};
