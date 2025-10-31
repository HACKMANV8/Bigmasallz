import type { LucideIcon } from "lucide-react";

export type ChatMessage = {
  id: number;
  role: "user" | "agent" | "system";
  content: string;
  timestamp: string;
};

export type FieldDefinition = {
  id: number;
  name: string;
  type: string;
  description: string;
  synthetic: boolean;
  example: string;
};

export type DatasetStats = {
  rows: number;
  columns: number;
  estimatedSize: string;
  syntheticScore: number;
  generationTime: string;
};

export type LlmMetric = {
  id: number;
  label: string;
  value: string;
  trend: "up" | "down";
  accent: "cyan" | "violet" | "emerald" | "amber" | "pink";
};

export type AccentColor = "cyan" | "violet" | "emerald" | "amber" | "pink" | "blue";

export type TelemetryBase = {
  id: string;
  label: string;
  caption: string;
  accent: AccentColor;
};

export type TelemetryGaugeSignal = TelemetryBase & {
  type: "gauge";
  percentage: number;
  status: string;
  icon: LucideIcon;
};

export type TelemetrySparkSignal = TelemetryBase & {
  type: "spark";
  points: number[];
};

export type TelemetryBarSegment = {
  label: string;
  value: number;
  color: string;
};

export type TelemetryBarSignal = TelemetryBase & {
  type: "bar";
  segments: TelemetryBarSegment[];
  total: number;
};

export type TelemetryPieSlice = {
  label: string;
  value: number;
  color: string;
};

export type TelemetryPieSignal = TelemetryBase & {
  type: "pie";
  slices: TelemetryPieSlice[];
  total: number;
};

export type TelemetrySignal =
  | TelemetryGaugeSignal
  | TelemetrySparkSignal
  | TelemetryBarSignal
  | TelemetryPieSignal;

export type BuildTelemetrySignalsInput = {
  stats: DatasetStats;
  blueprintDensity: number;
  llmMetrics: LlmMetric[];
};