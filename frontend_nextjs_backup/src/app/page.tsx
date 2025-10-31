'use client';

import { useState } from 'react';
import SchemaInput from '@/components/schema/SchemaInput';
import SchemaEditor from '@/components/schema/SchemaEditor';
import GenerationForm from '@/components/generation/GenerationForm';
import ProgressBar from '@/components/generation/ProgressBar';
import ResultsViewer from '@/components/generation/ResultsViewer';

export default function Home() {
  const [step, setStep] = useState<'input' | 'edit' | 'generate' | 'progress'>('input');
  const [schema, setSchema] = useState<any>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const handleSchemaTranslated = (translatedSchema: any) => {
    setSchema(translatedSchema);
    setStep('edit');
  };

  const handleSchemaConfirmed = (confirmedSchema: any) => {
    setSchema(confirmedSchema);
    setStep('generate');
  };

  const handleGenerationStarted = (newJobId: string) => {
    setJobId(newJobId);
    setStep('progress');
  };

  const handleReset = () => {
    setStep('input');
    setSchema(null);
    setJobId(null);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-8">
        <h2 className="text-4xl font-bold text-gray-900">
          Generate Synthetic Data at Scale
        </h2>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Transform natural language descriptions into high-quality, deduplicated synthetic data
          using AI-powered parallel processing
        </p>
      </div>

      {/* Step Indicator */}
      <div className="flex items-center justify-center space-x-4">
        {[
          { id: 'input', label: '1. Describe Data', icon: '📝' },
          { id: 'edit', label: '2. Confirm Schema', icon: '✅' },
          { id: 'generate', label: '3. Configure & Generate', icon: '⚙️' },
          { id: 'progress', label: '4. Track Progress', icon: '📊' },
        ].map((s, idx) => (
          <div key={s.id} className="flex items-center">
            <div
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${
                step === s.id
                  ? 'bg-primary-500 text-white'
                  : ['input', 'edit', 'generate', 'progress'].indexOf(step) >
                    ['input', 'edit', 'generate', 'progress'].indexOf(s.id)
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              <span className="text-2xl">{s.icon}</span>
              <span className="font-medium text-sm">{s.label}</span>
            </div>
            {idx < 3 && (
              <div className="w-8 h-0.5 bg-gray-300 mx-2"></div>
            )}
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div className="bg-white rounded-xl shadow-lg p-8">
        {step === 'input' && (
          <SchemaInput onSchemaTranslated={handleSchemaTranslated} />
        )}

        {step === 'edit' && schema && (
          <SchemaEditor
            schema={schema}
            onConfirm={handleSchemaConfirmed}
            onBack={() => setStep('input')}
          />
        )}

        {step === 'generate' && schema && (
          <GenerationForm
            schema={schema}
            onGenerationStarted={handleGenerationStarted}
            onBack={() => setStep('edit')}
          />
        )}

        {step === 'progress' && jobId && (
          <div className="space-y-6">
            <ProgressBar jobId={jobId} />
            <ResultsViewer jobId={jobId} onReset={handleReset} />
          </div>
        )}
      </div>

      {/* Features Section */}
      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-3xl mb-3">⚡</div>
          <h3 className="font-bold text-lg mb-2">Lightning Fast</h3>
          <p className="text-gray-600 text-sm">
            Parallel processing with up to 50 workers generates data 10-15x faster than standard
            LLM interfaces
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-3xl mb-3">🎯</div>
          <h3 className="font-bold text-lg mb-2">High Quality</h3>
          <p className="text-gray-600 text-sm">
            Vector-based deduplication ensures unique, realistic data with no repetitive patterns
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-3xl mb-3">🔄</div>
          <h3 className="font-bold text-lg mb-2">Human-in-the-Loop</h3>
          <p className="text-gray-600 text-sm">
            Review and edit AI-inferred schemas before generation for 100% accuracy
          </p>
        </div>
      </div>
    </div>
  );
}
