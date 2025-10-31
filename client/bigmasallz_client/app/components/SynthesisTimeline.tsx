"use client";

import clsx from "clsx";
import { ShieldCheck, Rocket, RefreshCcw, Terminal } from "lucide-react";
import type { LlmMetric } from "./types";
import { PROGRESS_STEPS } from "./constants";

interface MetricSignalProps {
  metric: LlmMetric;
}

function MetricSignal({ metric }: MetricSignalProps) {
  const palette = {
    cyan: {
      border: "border-cyan-400/40",
      glow: "from-cyan-500/20 via-transparent to-transparent",
      text: "text-cyan-100",
    },
    violet: {
      border: "border-violet-400/40",
      glow: "from-violet-500/18 via-transparent to-transparent",
      text: "text-violet-100",
    },
    emerald: {
      border: "border-emerald-400/40",
      glow: "from-emerald-500/20 via-transparent to-transparent",
      text: "text-emerald-100",
    },
    amber: {
      border: "border-amber-400/40",
      glow: "from-amber-500/20 via-transparent to-transparent",
      text: "text-amber-100",
    },
    pink: {
      border: "border-pink-400/40",
      glow: "from-pink-500/20 via-transparent to-transparent",
      text: "text-pink-100",
    },
  } as const;

  const iconMap = {
    cyan: "Activity",
    violet: "Radar",
    emerald: "Gauge",
    amber: "Cpu",
    pink: "Waves",
  } as const;

  const trendLabel = metric.trend === "up" ? "ascend" : "stabilize";
  const trendSymbol = metric.trend === "up" ? "▲" : "▼";
  const trendColor = metric.trend === "up" ? "text-emerald-300" : "text-amber-300";
  const { border, glow, text } = palette[metric.accent];

  return (
    <div
      className={clsx(
        "relative overflow-hidden rounded-2xl border bg-black/50 p-4 shadow-[0_0_35px_rgba(34,211,238,0.18)] transition duration-500 hover:-translate-y-1 hover:shadow-[0_0_55px_rgba(56,189,248,0.24)]",
        border
      )}
    >
      <div
        className={clsx(
          "pointer-events-none absolute inset-x-0 -top-16 h-24 bg-linear-to-b blur-3xl",
          glow
        )}
      />
      <div className="relative flex items-center gap-3">
        <span
          className={clsx(
            "grid h-9 w-9 place-items-center rounded-xl border bg-black/40 text-base shadow-[0_0_25px_rgba(103,232,249,0.25)]",
            text,
            border
          )}
        >
          <span className="h-4 w-4">{/* Icon placeholder */}</span>
        </span>
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-400">{metric.label}</p>
          <p className={clsx("mt-1 text-xl font-semibold", text)}>{metric.value}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
        <span>LLM fusion cycle</span>
        <span className={clsx("inline-flex items-center gap-1 font-semibold", trendColor)}>
          {trendSymbol} {trendLabel}
        </span>
      </div>
    </div>
  );
}

interface SynthesisTimelineProps {
  isGenerating: boolean;
  activeStepIndex: number;
  llmMetrics: LlmMetric[];
}

export default function SynthesisTimeline({
  isGenerating,
  activeStepIndex,
  llmMetrics,
}: SynthesisTimelineProps) {
  return (
    <div className="glass-panel group relative overflow-hidden rounded-3xl border border-slate-700/70 bg-slate-900/80 p-4 shadow-neon transition duration-500 hover:border-cyan-400/40 hover:shadow-[0_0_42px_rgba(21,244,255,0.18)]">
      <div className="pointer-events-none absolute inset-x-8 -top-24 h-48 rounded-full bg-linear-to-b from-cyan-500/12 via-transparent to-transparent blur-3xl opacity-0 transition group-hover:opacity-100 animate-drift-slow" />
      <div className="pointer-events-none absolute inset-y-0 right-12 w-px bg-linear-to-b from-transparent via-cyan-500/40 to-transparent opacity-40" />
      <div className="pointer-events-none absolute inset-y-6 left-8 hidden w-px bg-linear-to-b from-transparent via-cyan-500/25 to-transparent opacity-70 lg:block" />
      
      <div className="relative flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Synthesis Timeline</h2>
        <Terminal className="h-5 w-5 text-cyan-300" />
      </div>
      
      {isGenerating && (
        <div className="relative mt-5 grid gap-3 rounded-2xl border border-cyan-500/30 bg-black/40 p-4 shadow-[0_0_25px_rgba(20,184,166,0.18)] md:grid-cols-2">
          <div className="pointer-events-none absolute inset-0 animate-pulse-slow rounded-2xl border border-cyan-500/20" />
          {llmMetrics.map((metric) => (
            <MetricSignal key={metric.id} metric={metric} />
          ))}
        </div>
      )}
      
      <div className="relative mt-3 space-y-3">
        {PROGRESS_STEPS.map((step, index) => {
          const status =
            index < activeStepIndex
              ? "done"
              : index === activeStepIndex
              ? "active"
              : "pending";
          return (
            <div
              key={step.title}
              className={clsx(
                "rounded-2xl border p-3 transition-all duration-500 hover:-translate-y-1 hover:shadow-[0_0_26px_rgba(59,130,246,0.16)]",
                {
                "border-emerald-400/30 bg-emerald-400/10 shadow-neon": status === "done",
                "border-cyan-400/40 bg-cyan-500/20 shadow-neon": status === "active",
                "border-slate-700/50 bg-slate-900/70": status === "pending",
                }
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div
                    className={clsx(
                      "flex h-7 w-7 items-center justify-center rounded-full border text-[11px]",
                      status === "done"
                        ? "border-emerald-300/60 bg-emerald-400/20 text-emerald-100"
                        : status === "active"
                        ? "border-cyan-300/60 bg-cyan-500/20 text-cyan-100"
                        : "border-slate-600 bg-slate-800 text-slate-400"
                    )}
                  >
                    {status === "done" ? (
                      <ShieldCheck className="h-4 w-4" />
                    ) : status === "active" ? (
                      <Rocket className="h-4 w-4" />
                    ) : (
                      <RefreshCcw className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-100">{step.title}</p>
                    <p className="text-xs text-slate-400">{step.description}</p>
                  </div>
                </div>
                <div
                  className={clsx("text-xs uppercase tracking-[0.25em]", {
                    "text-emerald-200": status === "done",
                    "text-cyan-200": status === "active",
                    "text-slate-500": status === "pending",
                  })}
                >
                  {status === "done" ? "sealed" : status === "active" ? "executing" : "queued"}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}