"use client";

import { Database, Table, Search, Filter, Download, Eye } from "lucide-react";
import type { FieldDefinition, DatasetStats } from "./types";

interface DatasetPreviewProps {
  isGenerated: boolean;
  previewData: Array<Record<string, any>>;
  fields: FieldDefinition[];
  stats: DatasetStats;
}

export default function DatasetPreview({ isGenerated, previewData, fields, stats }: DatasetPreviewProps) {
  return (
    <div className="glass-panel group relative overflow-hidden rounded-3xl border border-cyan-500/30 bg-slate-900/80 p-6 shadow-neon transition duration-500 hover:border-violet-400/40 hover:shadow-[0_0_55px_rgba(124,58,237,0.22)]">
      <div className="pointer-events-none absolute inset-x-4 -top-24 h-44 rounded-full bg-linear-to-b from-violet-500/12 via-transparent to-transparent blur-3xl opacity-0 transition group-hover:opacity-100 animate-drift-slow" />
      
      <div className="relative flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Dataset Preview</h2>
        <Database className="h-5 w-5 text-cyan-300" />
      </div>

      {isGenerated ? (
        <div className="mt-6 space-y-6">
          {/* Dataset Stats Cards */}
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4 text-center">
              <div className="text-2xl font-bold text-emerald-400">{stats.rows.toLocaleString()}</div>
              <div className="text-xs text-slate-400 uppercase tracking-[0.2em]">Rows</div>
            </div>
            <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4 text-center">
              <div className="text-2xl font-bold text-cyan-400">{stats.columns}</div>
              <div className="text-xs text-slate-400 uppercase tracking-[0.2em]">Columns</div>
            </div>
            <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4 text-center">
              <div className="text-2xl font-bold text-violet-400">{stats.estimatedSize}</div>
              <div className="text-xs text-slate-400 uppercase tracking-[0.2em]">Size</div>
            </div>
            <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4 text-center">
              <div className="text-2xl font-bold text-amber-400">{stats.syntheticScore}%</div>
              <div className="text-xs text-slate-400 uppercase tracking-[0.2em]">Synthetic</div>
            </div>
          </div>

          {/* Data Table */}
          <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Table className="h-4 w-4 text-slate-400" />
                <span className="text-sm font-semibold text-slate-200">Data Sample</span>
              </div>
              <div className="flex items-center gap-2">
                <button className="rounded-lg border border-slate-600/40 bg-slate-800/60 p-2 text-slate-400 transition hover:border-cyan-400/40 hover:text-cyan-300">
                  <Search className="h-4 w-4" />
                </button>
                <button className="rounded-lg border border-slate-600/40 bg-slate-800/60 p-2 text-slate-400 transition hover:border-cyan-400/40 hover:text-cyan-300">
                  <Filter className="h-4 w-4" />
                </button>
                <button className="rounded-lg border border-emerald-600/40 bg-emerald-500/20 p-2 text-emerald-300 transition hover:bg-emerald-500/30">
                  <Download className="h-4 w-4" />
                </button>
              </div>
            </div>
            
            <div className="overflow-hidden rounded-xl border border-slate-700/60 bg-black/40">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700/60 bg-slate-800/60">
                      {fields.map((field, index) => (
                        <th
                          key={index}
                          className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.2em] text-slate-300"
                        >
                          {field.name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.map((row, rowIndex) => (
                      <tr
                        key={rowIndex}
                        className="border-b border-slate-700/30 transition hover:bg-slate-800/40"
                      >
                        {fields.map((field, fieldIndex) => (
                          <td
                            key={fieldIndex}
                            className="px-4 py-3 text-sm text-slate-200"
                          >
                            {row[field.name] || "-"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Blueprint Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {fields.map((field, index) => (
              <div
                key={index}
                className="group relative overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4 transition-all duration-500 hover:-translate-y-1 hover:border-cyan-400/50 hover:shadow-[0_0_30px_rgba(59,130,246,0.15)]"
              >
                <div className="mb-3 flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-200">{field.name}</span>
                  <span className="rounded-full border border-cyan-400/40 bg-cyan-500/10 px-2 py-1 text-xs font-semibold text-cyan-300">
                    {field.type}
                  </span>
                </div>
                <p className="mb-3 text-xs text-slate-400">{field.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Example:</span>
                  <span className="font-mono text-xs text-emerald-300">{field.example}</span>
                </div>
                {field.synthetic && (
                  <div className="mt-2 flex items-center gap-1">
                    <div className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
                    <span className="text-xs text-violet-300">AI Generated</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Generation Info */}
          <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="rounded-full border border-emerald-400/40 bg-emerald-500/20 p-2">
                  <Eye className="h-4 w-4 text-emerald-300" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-emerald-200">Dataset Generated</div>
                  <div className="text-xs text-emerald-400">Generation time: {stats.generationTime}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-emerald-200">Quality Score</div>
                <div className="text-xs text-emerald-400">{stats.syntheticScore}% synthetic accuracy</div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-6 flex flex-col items-center justify-center py-12">
          <div className="rounded-full border border-slate-600/40 bg-slate-800/60 p-6">
            <Database className="h-8 w-8 text-slate-400" />
          </div>
          <div className="mt-4 text-center">
            <h3 className="text-lg font-semibold text-slate-300">No Dataset Generated</h3>
            <p className="mt-2 text-sm text-slate-400">
              Configure your schema and generate a dataset to see the preview
            </p>
          </div>
        </div>
      )}
    </div>
  );
}