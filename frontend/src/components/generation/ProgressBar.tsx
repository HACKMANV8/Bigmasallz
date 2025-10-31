'use client';

import { useEffect, useState } from 'react';
import { jobService } from '@/services/jobs';
import type { JobStatusResponse } from '@/types/job';

interface ProgressBarProps {
  jobId: string;
}

export default function ProgressBar({ jobId }: ProgressBarProps) {
  const [status, setStatus] = useState<JobStatusResponse | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await jobService.getJobStatus(jobId);
        setStatus(data);

        // Continue polling if not complete
        if (data.status !== 'completed' && data.status !== 'failed') {
          setTimeout(fetchStatus, 2000);
        }
      } catch (err) {
        console.error('Failed to fetch status:', err);
      }
    };

    fetchStatus();
  }, [jobId]);

  if (!status) {
    return <div>Loading...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <span className="text-lg font-semibold">Generation Progress</span>
        <span className="text-sm text-gray-600">
          {status.completed_chunks} / {status.total_chunks} chunks
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className="bg-primary-600 h-4 rounded-full transition-all duration-500"
          style={{ width: `${status.progress_percentage}%` }}
        />
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-primary-600">
            {status.progress_percentage.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Progress</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {status.rows_generated}
          </div>
          <div className="text-sm text-gray-600">Rows Generated</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">
            {status.rows_deduplicated}
          </div>
          <div className="text-sm text-gray-600">Deduplicated</div>
        </div>
      </div>
    </div>
  );
}
