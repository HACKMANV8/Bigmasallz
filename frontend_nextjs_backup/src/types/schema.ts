export interface ColumnSchema {
  name: string;
  type: 'string' | 'integer' | 'float' | 'boolean' | 'datetime' | 'date' | 'email' | 'phone' | 'url' | 'uuid' | 'json';
  description: string;
  constraints?: Record<string, any>;
  examples?: string[];
}

export interface DataSchema {
  columns: ColumnSchema[];
  metadata?: Record<string, any>;
}

export interface SchemaTranslationRequest {
  prompt: string;
  context?: string;
}

export interface SchemaTranslationResponse {
  schema: DataSchema;
  inferred_count?: number;
  confidence: number;
}
