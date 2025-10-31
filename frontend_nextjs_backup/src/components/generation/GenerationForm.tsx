'use client';

import { useState } from 'react';
import { dataService } from '@/services/data';
import type { DataSchema } from '@/types/schema';

interface GenerationFormProps {
  schema: DataSchema;
  onGenerationStarted: (jobId: string) => void;
  onBack: () => void;
}

export default function GenerationForm({ schema, onGenerationStarted, onBack }: GenerationFormProps) {
  const [totalRows, setTotalRows] = useState(1000);
  const [chunkSize, setChunkSize] = useState(500);
  const [maxWorkers, setMaxWorkers] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await dataService.generateData({
        schema,
        total_rows: totalRows,
        chunk_size: chunkSize,
        max_workers: maxWorkers,
      });

      onGenerationStarted(response.job_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start generation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Configure Data Generation</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Total Rows
          </label>
          <input
            type="number"
            value={totalRows}
            onChange={(e) => setTotalRows(parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg"
            min="1"
            max="1000000"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Chunk Size
          </label>
          <input
            type="number"
            value={chunkSize}
            onChange={(e) => setChunkSize(parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg"
            min="100"
            max="2000"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max Workers
          </label>
          <input
            type="number"
            value={maxWorkers}
            onChange={(e) => setMaxWorkers(parseInt(e.target.value))}
            className="w-full px-3 py-2 border rounded-lg"
            min="1"
            max="50"
          />
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="flex justify-between gap-4">
        <button
          onClick={onBack}
          className="px-6 py-3 border rounded-lg hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? 'Starting Generation...' : 'Start Generation'}
        </button>
      </div>
    </div>
  );
}
