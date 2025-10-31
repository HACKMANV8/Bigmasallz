"use client";

import { Database, Plus, Trash2, Sparkles } from "lucide-react";
import type { FieldDefinition } from "./types";
import { TYPE_OPTIONS } from "./constants";

interface SchemaArchitectProps {
  datasetName: string;
  setDatasetName: (value: string) => void;
  datasetNarrative: string;
  setDatasetNarrative: (value: string) => void;
  rowCount: number;
  setRowCount: (value: number) => void;
  fields: FieldDefinition[];
  onAddField: () => void;
  onFieldChange: <K extends keyof FieldDefinition>(
    fieldId: number,
    key: K,
    value: FieldDefinition[K]
  ) => void;
  onRemoveField: (fieldId: number) => void;
  onGenerateDataset: () => void;
  isGenerating: boolean;
}

export default function SchemaArchitect({
  datasetName,
  setDatasetName,
  datasetNarrative,
  setDatasetNarrative,
  rowCount,
  setRowCount,
  fields,
  onAddField,
  onFieldChange,
  onRemoveField,
  onGenerateDataset,
  isGenerating,
}: SchemaArchitectProps) {
  return (
    <div className="glass-panel group relative overflow-hidden rounded-3xl border border-cyan-500/30 bg-slate-900/85 shadow-2xl transition duration-500 hover:border-violet-400/40 hover:shadow-[0_0_60px_rgba(124,58,237,0.25)]">
      {/* Enhanced glow effects */}
      <div className="pointer-events-none absolute inset-x-4 -top-32 h-64 rounded-full bg-linear-to-b from-violet-500/15 via-cyan-500/10 to-transparent blur-3xl opacity-0 transition-opacity duration-700 group-hover:opacity-100 animate-drift-slow" />
      
      <div className="relative p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Database className="h-6 w-6 text-cyan-300" />
              <div className="absolute -inset-1 bg-cyan-400/20 rounded-lg blur-sm" />
            </div>
            <h2 className="text-lg font-semibold bg-linear-to-r from-cyan-200 to-violet-200 bg-clip-text text-transparent">
              Schema Architect
            </h2>
          </div>
          <div className="px-3 py-1 rounded-full border border-cyan-400/40 bg-cyan-500/10 text-xs font-medium text-cyan-300">
            DESIGN MODE
          </div>
        </div>
      
      <div className="mt-4 grid gap-4">
        <label className="flex flex-col gap-2 text-sm">
          <span className="text-xs uppercase tracking-[0.25em] text-slate-400">Dataset Name</span>
          <input
            className="rounded-2xl border border-cyan-500/40 bg-black/40 px-4 py-3 text-sm text-slate-100 focus:border-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
            value={datasetName}
            onChange={(event) => setDatasetName(event.target.value)}
          />
        </label>
        
        <label className="flex flex-col gap-2 text-sm">
          <span className="text-xs uppercase tracking-[0.25em] text-slate-400">Narrative</span>
          <textarea
            className="min-h-18 rounded-2xl border border-cyan-500/40 bg-black/40 px-4 py-3 text-sm text-slate-100 focus:border-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
            value={datasetNarrative}
            onChange={(event) => setDatasetNarrative(event.target.value)}
          />
        </label>
        
        <label className="flex flex-col gap-2 text-sm">
          <span className="text-xs uppercase tracking-[0.25em] text-slate-400">Rows Required</span>
          <input
            type="number"
            min={100}
            step={100}
            className="rounded-2xl border border-cyan-500/40 bg-black/40 px-4 py-3 text-sm text-slate-100 focus:border-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
            value={rowCount}
            onChange={(event) => setRowCount(Number(event.target.value))}
          />
        </label>
      </div>

      <div className="mt-6 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-[0.35em]">Blueprint</h3>
        <button
          onClick={onAddField}
          className="inline-flex items-center gap-2 rounded-full border border-cyan-400/40 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-100 transition hover:bg-cyan-400/30"
        >
          <Plus className="h-3.5 w-3.5" /> add column
        </button>
      </div>

      <div className="mt-4 space-y-4">
        {fields.map((field, index) => (
          <div
            key={field.id}
            className="rounded-2xl border border-slate-700/60 bg-slate-900/90 p-4 shadow-inner transition-all duration-500 hover:-translate-y-1 hover:border-cyan-400/50 hover:shadow-[0_0_40px_rgba(59,130,246,0.2)]"
          >
            <div className="flex items-start gap-4">
              <span className="mt-1 inline-flex h-7 w-7 items-center justify-center rounded-full border border-cyan-400/40 bg-cyan-500/10 text-xs font-semibold text-cyan-100">
                {index + 1}
              </span>
              <div className="flex-1 space-y-3 text-sm">
                <div className="grid gap-3 md:grid-cols-[1.3fr_0.9fr]">
                  <input
                    placeholder="column_name"
                    value={field.name}
                    onChange={(event) =>
                      onFieldChange(field.id, "name", event.target.value)
                    }
                    className="rounded-xl border border-cyan-500/30 bg-black/40 px-4 py-2 text-sm text-slate-100 focus:border-cyan-300 focus:outline-none"
                  />
                  <select
                    value={field.type}
                    onChange={(event) =>
                      onFieldChange(field.id, "type", event.target.value)
                    }
                    className="rounded-xl border border-cyan-500/30 bg-black/40 px-4 py-2 text-sm text-slate-100 focus:border-cyan-300 focus:outline-none"
                  >
                    {TYPE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
                <textarea
                  placeholder="Describe the signal, distribution, and constraints"
                  value={field.description}
                  onChange={(event) =>
                    onFieldChange(field.id, "description", event.target.value)
                  }
                  className="w-full rounded-xl border border-slate-700/60 bg-black/30 px-4 py-2 text-sm text-slate-100 focus:border-cyan-300 focus:outline-none"
                />
                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                  <label className="inline-flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={field.synthetic}
                      onChange={(event) =>
                        onFieldChange(field.id, "synthetic", event.target.checked)
                      }
                      className="h-4 w-4 rounded border border-cyan-500/40 bg-black/40"
                    />
                    <span>Model generated feature</span>
                  </label>
                  <input
                    placeholder="example value"
                    value={field.example}
                    onChange={(event) =>
                      onFieldChange(field.id, "example", event.target.value)
                    }
                    className="rounded-xl border border-slate-700/60 bg-black/30 px-3 py-1 text-xs text-slate-200 focus:border-cyan-300 focus:outline-none"
                  />
                </div>
              </div>
              <button
                onClick={() => onRemoveField(field.id)}
                className="rounded-full border border-red-500/30 bg-red-500/10 p-2 text-red-200 transition hover:bg-red-500/30"
                aria-label="Remove column"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <button
          onClick={onGenerateDataset}
          disabled={isGenerating}
          className="inline-flex items-center gap-2 rounded-full border border-emerald-400/40 bg-emerald-400/20 px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.25em] text-emerald-100 transition hover:bg-emerald-400/40 disabled:cursor-not-allowed disabled:border-emerald-300/20 disabled:bg-emerald-400/10 disabled:text-emerald-300/60"
        >
          <Sparkles className="h-5 w-5" />
          generate dataset
        </button>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-emerald-300" />
          Auto-governed synthetic mode
        </div>
      </div>
      </div>
    </div>
  );
}