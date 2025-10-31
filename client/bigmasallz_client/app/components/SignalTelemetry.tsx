"use client";

import { Activity, Zap, TrendingUp, BarChart3, PieChart, Target } from "lucide-react";
import type { TelemetrySignal } from "./types";

interface TelemetryGaugeProps {
  value: number;
  label: string;
  color: string;
  unit?: string;
}

function TelemetryGauge({ value, label, color, unit = "" }: TelemetryGaugeProps) {
  const normalizedValue = Math.min(100, Math.max(0, value));
  const strokeDasharray = `${normalizedValue * 2.51} 251`;

  return (
    <div className="relative h-24 w-24">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 84 84">
        <circle
          cx="42"
          cy="42"
          r="40"
          stroke="currentColor"
          strokeWidth="2"
          fill="transparent"
          className="text-slate-700/50"
        />
        <circle
          cx="42"
          cy="42"
          r="40"
          stroke={color}
          strokeWidth="2"
          fill="transparent"
          strokeDasharray={strokeDasharray}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
          style={{
            filter: `drop-shadow(0 0 6px ${color}40)`,
          }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-slate-100">
          {Math.round(value)}{unit}
        </span>
        <span className="text-xs text-slate-400">{label}</span>
      </div>
    </div>
  );
}

interface SparklineProps {
  data: number[];
  color: string;
}

function Sparkline({ data, color }: SparklineProps) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 100 - ((value - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className="h-12 w-full">
      <svg viewBox="0 0 100 100" className="h-full w-full">
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="2"
          points={points}
          className="transition-all duration-500"
          style={{
            filter: `drop-shadow(0 0 4px ${color}60)`,
          }}
        />
      </svg>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  title: string;
  value: string;
  change: string;
  trend: "up" | "down" | "neutral";
  sparklineData?: number[];
  color: string;
}

function MetricCard({ icon, title, value, change, trend, sparklineData, color }: MetricCardProps) {
  const trendColors = {
    up: "text-emerald-400",
    down: "text-red-400",
    neutral: "text-slate-400",
  };

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4 shadow-inner transition-all duration-500 hover:-translate-y-1 hover:border-cyan-400/50 hover:shadow-[0_0_30px_rgba(59,130,246,0.15)]">
      <div className="flex items-start justify-between">
        <div className="text-slate-400">{icon}</div>
        <div className={`text-xs font-semibold ${trendColors[trend]}`}>
          {change}
        </div>
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold text-slate-100">{value}</div>
        <div className="text-sm text-slate-400">{title}</div>
      </div>
      {sparklineData && (
        <div className="mt-3">
          <Sparkline data={sparklineData} color={color} />
        </div>
      )}
    </div>
  );
}

interface DonutChartProps {
  data: Array<{ label: string; value: number; color: string }>;
}

function DonutChart({ data }: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let cumulativePercent = 0;

  return (
    <div className="relative h-32 w-32">
      <svg viewBox="0 0 42 42" className="h-full w-full">
        {data.map((item, index) => {
          const percent = (item.value / total) * 100;
          const strokeDasharray = `${percent} ${100 - percent}`;
          const strokeDashoffset = -cumulativePercent;
          cumulativePercent += percent;

          return (
            <circle
              key={index}
              cx="21"
              cy="21"
              r="15.915"
              fill="transparent"
              stroke={item.color}
              strokeWidth="2"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-1000 ease-out"
              style={{
                filter: `drop-shadow(0 0 4px ${item.color}40)`,
              }}
            />
          );
        })}
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-sm font-bold text-slate-100">{total}</span>
      </div>
    </div>
  );
}

interface BarChartProps {
  data: Array<{ label: string; value: number }>;
  color: string;
}

function BarChart({ data, color }: BarChartProps) {
  const max = Math.max(...data.map(d => d.value));

  return (
    <div className="flex h-24 items-end justify-between gap-1">
      {data.map((item, index) => {
        const height = (item.value / max) * 100;
        return (
          <div key={index} className="flex flex-col items-center gap-1">
            <div
              className="w-6 rounded-t-sm transition-all duration-1000 ease-out"
              style={{
                height: `${height}%`,
                backgroundColor: color,
                filter: `drop-shadow(0 0 4px ${color}40)`,
              }}
            />
            <span className="text-xs text-slate-400">{item.label}</span>
          </div>
        );
      })}
    </div>
  );
}

interface SignalTelemetryProps {
  telemetryData: TelemetrySignal[];
}

export default function SignalTelemetry({ telemetryData }: SignalTelemetryProps) {
  // Generate additional telemetry data for charts
  const cpuUsage = 72;
  const memoryUsage = 84;
  const networkThroughput = 156;
  const requestsPerSecond = 342;

  const sparklineData = Array.from({ length: 20 }, () => Math.random() * 100);
  const networkSparkline = Array.from({ length: 20 }, () => 50 + Math.random() * 50);
  const requestSparkline = Array.from({ length: 20 }, () => 200 + Math.random() * 200);

  const modelDistribution = [
    { label: "GPT-4", value: 45, color: "#06b6d4" },
    { label: "Claude", value: 30, color: "#8b5cf6" },
    { label: "Gemini", value: 25, color: "#10b981" },
  ];

  const responseTimeData = [
    { label: "1h", value: 120 },
    { label: "2h", value: 98 },
    { label: "3h", value: 156 },
    { label: "4h", value: 134 },
    { label: "5h", value: 187 },
    { label: "6h", value: 165 },
  ];

  return (
    <div className="glass-panel group relative overflow-hidden rounded-3xl border border-cyan-500/30 bg-slate-900/80 p-4 lg:p-6 shadow-neon transition duration-500 hover:border-violet-400/40 hover:shadow-[0_0_55px_rgba(124,58,237,0.22)] w-full">
      <div className="pointer-events-none absolute inset-x-4 -top-24 h-44 rounded-full bg-linear-to-b from-violet-500/12 via-transparent to-transparent blur-3xl opacity-0 transition group-hover:opacity-100 animate-drift-slow" />
      
      <div className="relative flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-100">Signal Telemetry</h2>
        <Activity className="h-5 w-5 text-cyan-300" />
      </div>
      
      <div className="space-y-4 lg:space-y-6">
        {/* Performance Gauges - Responsive Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4">
          <div className="flex flex-col items-center gap-2">
            <TelemetryGauge
              value={cpuUsage}
              label="CPU"
              color="#06b6d4"
              unit="%"
            />
          </div>
          <div className="flex flex-col items-center gap-2">
            <TelemetryGauge
              value={memoryUsage}
              label="Memory"
              color="#8b5cf6"
              unit="%"
            />
          </div>
          <div className="flex flex-col items-center gap-2">
            <TelemetryGauge
              value={networkThroughput}
              label="Network"
              color="#10b981"
              unit="MB/s"
            />
          </div>
          <div className="flex flex-col items-center gap-2">
            <TelemetryGauge
              value={requestsPerSecond}
              label="Requests"
              color="#f59e0b"
              unit="/s"
            />
          </div>
        </div>

        {/* Metric Cards - Simplified Grid */}
        <div className="grid gap-3 lg:gap-4 grid-cols-1 lg:grid-cols-3">
          <MetricCard
            icon={<Zap className="h-4 w-4 lg:h-5 lg:w-5" />}
            title="Avg Response Time"
            value="142ms"
            change="+12%"
            trend="up"
            sparklineData={sparklineData}
            color="#06b6d4"
          />
          <MetricCard
            icon={<TrendingUp className="h-4 w-4 lg:h-5 lg:w-5" />}
            title="Throughput"
            value="1.2k/min"
            change="-3%"
            trend="down"
            sparklineData={networkSparkline}
            color="#8b5cf6"
          />
          <MetricCard
            icon={<Target className="h-4 w-4 lg:h-5 lg:w-5" />}
            title="Success Rate"
            value="99.7%"
            change="+0.1%"
            trend="up"
            sparklineData={requestSparkline}
            color="#10b981"
          />
        </div>

        {/* Charts Row - Stacked on smaller screens */}
        <div className="grid gap-4 lg:gap-6 grid-cols-1 xl:grid-cols-3">
          {/* Model Distribution */}
          <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4">
            <div className="mb-4 flex items-center gap-2">
              <PieChart className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-semibold text-slate-200">Model Distribution</span>
            </div>
            <div className="flex items-center justify-between">
              <DonutChart data={modelDistribution} />
              <div className="space-y-2">
                {modelDistribution.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-xs text-slate-300">{item.label}</span>
                    <span className="text-xs text-slate-400">{item.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Response Time Trend */}
          <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4">
            <div className="mb-4 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-semibold text-slate-200">Response Time</span>
            </div>
            <BarChart data={responseTimeData} color="#06b6d4" />
          </div>

          {/* Live Telemetry Stream */}
          <div className="rounded-2xl border border-slate-700/60 bg-slate-900/80 p-4">
            <div className="mb-4 flex items-center gap-2">
              <Activity className="h-4 w-4 text-slate-400" />
              <span className="text-sm font-semibold text-slate-200">Live Stream</span>
            </div>
            <div className="space-y-2">
              {telemetryData.slice(0, 5).map((signal, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-lg border border-slate-700/40 bg-black/20 px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        signal.type === "gauge" && signal.status === "active"
                          ? "bg-emerald-400 animate-pulse"
                          : signal.type === "gauge" && signal.status === "warning"
                          ? "bg-yellow-400"
                          : "bg-red-400"
                      }`}
                    />
                    <span className="text-xs text-slate-300">{signal.label}</span>
                  </div>
                  <span className="text-xs font-mono text-slate-400">
                    {signal.type === "gauge" ? `${signal.percentage}%` : signal.caption}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}