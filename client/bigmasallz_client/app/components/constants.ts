import type { FieldDefinition, LlmMetric } from "./types";

export const PROGRESS_STEPS = [
  {
    title: "Interpreting request",
    description: "SynthxAI analyzes dataset intent and domain context.",
  },
  {
    title: "Drafting schema",
    description: "Generating relational blueprint with field level semantics.",
  },
  {
    title: "Synthesizing rows",
    description: "Calibrating statistical models and rendering synthetic records.",
  },
  {
    title: "Quality assurance",
    description: "Running privacy checks and structural validations before delivery.",
  },
];

export const LLM_METRIC_TEMPLATES: LlmMetric[] = [
  {
    id: 1,
    label: "Tokens / sec",
    value: "42.4k",
    trend: "up",
    accent: "cyan",
  },
  {
    id: 2,
    label: "Latency",
    value: "128 ms",
    trend: "down",
    accent: "violet",
  },
  {
    id: 3,
    label: "Context load",
    value: "78 %",
    trend: "up",
    accent: "emerald",
  },
  {
    id: 4,
    label: "Coherence",
    value: "96 %",
    trend: "up",
    accent: "amber",
  },
];

export const TYPE_OPTIONS = [
  "string",
  "integer",
  "float",
  "boolean",
  "datetime",
  "uuid",
  "email",
  "currency",
];

export const DEFAULT_FIELDS: FieldDefinition[] = [
  {
    id: 1,
    name: "customer_id",
    type: "uuid",
    description: "Unique entity identifier",
    synthetic: true,
    example: "bce5-9f11-90aa",
  },
  {
    id: 2,
    name: "region",
    type: "string",
    description: "Market region label",
    synthetic: true,
    example: "EMEA",
  },
  {
    id: 3,
    name: "plan_tier",
    type: "string",
    description: "Subscription level",
    synthetic: true,
    example: "Enterprise",
  },
  {
    id: 4,
    name: "sessions_last_30d",
    type: "integer",
    description: "Usage intensity in rolling month",
    synthetic: true,
    example: "28",
  },
  {
    id: 5,
    name: "revenue_90d",
    type: "currency",
    description: "Latest 90 day revenue snapshot",
    synthetic: true,
    example: "$9,420.13",
  },
];