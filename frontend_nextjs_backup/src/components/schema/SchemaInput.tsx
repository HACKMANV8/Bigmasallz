'use client';

import { useState } from 'react';
import { schemaService } from '@/services/schema';
import type { DataSchema } from '@/types/schema';

interface SchemaInputProps {
  onSchemaTranslated: (schema: DataSchema) => void;
}

export default function SchemaInput({ onSchemaTranslated }: SchemaInputProps) {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await schemaService.translateSchema({ prompt });
      onSchemaTranslated(response.schema);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to translate schema');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Describe your data in natural language
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="w-full h-32 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
          placeholder="Example: Generate 10,000 financial transactions with user ID, amount in USD, timestamp, and transaction type (debit/credit)"
          required
        />
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !prompt.trim()}
        className="w-full py-3 px-6 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Translating Schema...' : 'Translate to Schema'}
      </button>
    </form>
  );
}
