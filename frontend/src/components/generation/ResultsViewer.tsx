'use client';

import { useEffect, useState } from 'react';
import { jobService } from '@/services/jobs';

interface ResultsViewerProps {
  jobId: string;
  onReset: () => void;
}

export default function ResultsViewer({ jobId, onReset }: ResultsViewerProps) {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkResults = async () => {
      try {
        const status = await jobService.getJobStatus(jobId);
        
        if (status.status === 'completed' && status.results) {
          setResults(status.results);
          setLoading(false);
        } else if (status.status !== 'completed') {
          setTimeout(checkResults, 2000);
        }
      } catch (err) {
        console.error('Failed to fetch results:', err);
      }
    };

    checkResults();
  }, [jobId]);

  const handleDownload = async (format: 'csv' | 'json') => {
    try {
      const blob = await jobService.downloadResults(jobId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `synthaix_${jobId}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Waiting for results...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Generation Complete! 🎉</h3>
        <button
          onClick={onReset}
          className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50"
        >
          Generate More Data
        </button>
      </div>

      <div className="flex gap-4">
        <button
          onClick={() => handleDownload('csv')}
          className="flex-1 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Download CSV
        </button>
        <button
          onClick={() => handleDownload('json')}
          className="flex-1 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
        >
          Download JSON
        </button>
      </div>

      {results?.data && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium mb-2">Preview (first 5 rows)</h4>
          <pre className="text-xs overflow-auto max-h-96">
            {JSON.stringify(results.data.slice(0, 5), null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
