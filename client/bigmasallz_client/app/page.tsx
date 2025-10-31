"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Bot, Cpu, Database } from "lucide-react";

import ChatConsole from "./components/ChatConsole";
import SynthesisTimeline from "./components/SynthesisTimeline";
import SchemaArchitect from "./components/SchemaArchitect";
import SignalTelemetry from "./components/SignalTelemetry";
import DatasetPreview from "./components/DatasetPreview";

import type { 
  ChatMessage, 
  FieldDefinition, 
  DatasetStats, 
  LlmMetric, 
  TelemetrySignal 
} from "./components/types";

import { 
  PROGRESS_STEPS, 
  LLM_METRIC_TEMPLATES, 
  DEFAULT_FIELDS 
} from "./components/constants";

// Utility functions for data generation
function generatePreviewData(fields: FieldDefinition[], count: number = 5): Array<Record<string, any>> {
  return Array.from({ length: count }, (_, rowIndex) => {
    const row: Record<string, any> = {};
    fields.forEach((field) => {
      switch (field.type) {
        case "string":
          row[field.name] = field.example || `Sample ${rowIndex + 1}`;
          break;
        case "integer":
          row[field.name] = Math.floor(Math.random() * 1000);
          break;
        case "float":
          row[field.name] = (Math.random() * 100).toFixed(2);
          break;
        case "boolean":
          row[field.name] = Math.random() > 0.5;
          break;
        case "uuid":
          row[field.name] = `${Math.random().toString(36).substr(2, 4)}-${Math.random().toString(36).substr(2, 4)}`;
          break;
        case "email":
          row[field.name] = `user${rowIndex + 1}@example.com`;
          break;
        case "currency":
          row[field.name] = `$${(Math.random() * 10000).toFixed(2)}`;
          break;
        case "datetime":
          row[field.name] = new Date(Date.now() - Math.random() * 86400000 * 30).toISOString().split('T')[0];
          break;
        default:
          row[field.name] = field.example || "Sample";
      }
    });
    return row;
  });
}

function generateTelemetryData(): TelemetrySignal[] {
  return [
    {
      id: "cpu",
      label: "CPU Usage",
      caption: "System load average",
      accent: "cyan",
      type: "gauge",
      percentage: 72,
      status: "active",
      icon: Cpu,
    },
    {
      id: "memory",
      label: "Memory",
      caption: "RAM utilization",
      accent: "violet",
      type: "gauge",
      percentage: 84,
      status: "warning",
      icon: Database,
    },
    {
      id: "network",
      label: "Network",
      caption: "Throughput metrics",
      accent: "emerald",
      type: "spark",
      points: Array.from({ length: 20 }, () => Math.random() * 100),
    },
    {
      id: "requests",
      label: "Requests",
      caption: "API call volume",
      accent: "amber",
      type: "spark",
      points: Array.from({ length: 20 }, () => 50 + Math.random() * 50),
    },
  ];
}

export default function SynthxAI() {
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "system",
      content: "SynthxAI dataset synthesis engine initialized. Ready to generate high-fidelity synthetic data.",
      timestamp: new Date().toLocaleTimeString(),
    },
    {
      id: 2,
      role: "agent",
      content: "Configure your dataset schema in the architect panel, then I'll generate synthetic data that matches your requirements.",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");

  // Schema state
  const [datasetName, setDatasetName] = useState("customer_analytics");
  const [datasetNarrative, setDatasetNarrative] = useState("Enterprise customer behavior and engagement metrics for B2B SaaS platforms");
  const [rowCount, setRowCount] = useState(10000);
  const [fields, setFields] = useState<FieldDefinition[]>(DEFAULT_FIELDS);
  const [nextFieldId, setNextFieldId] = useState(6);

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [isGenerated, setIsGenerated] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  // Data state
  const [previewData, setPreviewData] = useState<Array<Record<string, any>>>([]);
  const [stats, setStats] = useState<DatasetStats>({
    rows: 0,
    columns: 0,
    estimatedSize: "0 MB",
    syntheticScore: 0,
    generationTime: "0s",
  });

  // Telemetry state
  const telemetryData = useMemo(() => generateTelemetryData(), []);
  const [llmMetrics, setLlmMetrics] = useState<LlmMetric[]>(LLM_METRIC_TEMPLATES);

  // Auto-update LLM metrics
  useEffect(() => {
    const interval = setInterval(() => {
      setLlmMetrics(prev => 
        prev.map(metric => ({
          ...metric,
          value: generateMetricValue(metric.label),
          trend: Math.random() > 0.5 ? "up" : "down",
        }))
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  function generateMetricValue(label: string): string {
    switch (label) {
      case "Tokens / sec":
        return `${(Math.random() * 50 + 30).toFixed(1)}k`;
      case "Latency":
        return `${Math.floor(Math.random() * 100 + 80)} ms`;
      case "Context load":
        return `${Math.floor(Math.random() * 30 + 60)} %`;
      case "Coherence":
        return `${Math.floor(Math.random() * 10 + 90)} %`;
      default:
        return "0";
    }
  }

  const handleSendMessage = useCallback((event: FormEvent) => {
    event.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage: ChatMessage = {
      id: messages.length + 1,
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");

    // Simulate agent response
    setTimeout(() => {
      const agentMessage: ChatMessage = {
        id: messages.length + 2,
        role: "agent",
        content: "I understand your request. I'm analyzing the optimal schema configuration for your dataset requirements.",
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, agentMessage]);
    }, 1000);
  }, [inputValue, messages.length]);

  const handleAddField = useCallback(() => {
    const newField: FieldDefinition = {
      id: nextFieldId,
      name: "",
      type: "string",
      description: "",
      synthetic: false,
      example: "",
    };
    setFields(prev => [...prev, newField]);
    setNextFieldId(prev => prev + 1);
  }, [nextFieldId]);

  const handleFieldChange = useCallback(<K extends keyof FieldDefinition>(
    fieldId: number,
    key: K,
    value: FieldDefinition[K]
  ) => {
    setFields(prev =>
      prev.map(field =>
        field.id === fieldId ? { ...field, [key]: value } : field
      )
    );
  }, []);

  const handleRemoveField = useCallback((fieldId: number) => {
    setFields(prev => prev.filter(field => field.id !== fieldId));
  }, []);

  const handleGenerateDataset = useCallback(async () => {
    setIsGenerating(true);
    setIsGenerated(false);
    setCurrentStep(0);

    // Simulate generation process
    for (let step = 0; step < PROGRESS_STEPS.length; step++) {
      setCurrentStep(step);
      await new Promise(resolve => setTimeout(resolve, 1500));
    }

    // Generate preview data and stats
    const generatedData = generatePreviewData(fields);
    setPreviewData(generatedData);
    
    const generatedStats: DatasetStats = {
      rows: rowCount,
      columns: fields.length,
      estimatedSize: `${(rowCount * fields.length * 0.05).toFixed(1)} MB`,
      syntheticScore: Math.floor(Math.random() * 20 + 80),
      generationTime: `${(Math.random() * 10 + 5).toFixed(1)}s`,
    };
    setStats(generatedStats);

    setIsGenerating(false);
    setIsGenerated(true);

    // Add success message
    const successMessage: ChatMessage = {
      id: messages.length + 1,
      role: "agent",
      content: `Dataset '${datasetName}' generated successfully! ${generatedStats.rows.toLocaleString()} rows with ${generatedStats.syntheticScore}% synthetic accuracy.`,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages(prev => [...prev, successMessage]);
  }, [fields, rowCount, datasetName, messages.length]);

  return (
    <main className="min-h-screen bg-linear-to-br from-slate-950 via-slate-900 to-black text-slate-100">
      {/* Enhanced Background Effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {/* Primary gradient overlays */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,var(--tw-gradient-stops))] from-cyan-500/12 via-blue-500/8 to-transparent" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,var(--tw-gradient-stops))] from-violet-500/12 via-purple-500/8 to-transparent" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,var(--tw-gradient-stops))] from-emerald-500/6 via-transparent to-transparent" />
        
        {/* Enhanced animated grid */}
        <div className="absolute inset-0 bg-grid-white/[0.04] bg-size-[80px_80px] animate-pulse" style={{ animationDuration: '6s' }} />
        
        {/* Floating orbs - more subtle */}
        <div className="absolute top-1/5 left-1/6 w-[500px] h-[500px] bg-cyan-500/8 rounded-full blur-3xl animate-bounce opacity-60" style={{ animationDuration: '8s' }} />
        <div className="absolute bottom-1/5 right-1/6 w-[400px] h-[400px] bg-violet-500/8 rounded-full blur-3xl animate-bounce opacity-60" style={{ animationDuration: '10s', animationDelay: '3s' }} />
        
        {/* Scanning lines */}
        <div className="absolute inset-0 bg-linear-to-b from-transparent via-cyan-500/8 to-transparent h-1 animate-pulse" style={{ top: '25%' }} />
        <div className="absolute inset-0 bg-linear-to-b from-transparent via-violet-500/8 to-transparent h-1 animate-pulse" style={{ top: '65%', animationDelay: '2s' }} />
      </div>

      {/* Enhanced Header */}
      <header className="relative border-b border-slate-800/60 bg-slate-900/40 backdrop-blur-xl">
        <div className="absolute inset-0 bg-linear-to-r from-cyan-500/5 via-transparent to-violet-500/5" />
        <div className="mx-auto max-w-7xl px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative group">
                <div className="rounded-2xl border border-cyan-400/40 bg-linear-to-br from-cyan-500/20 to-blue-600/20 p-3 shadow-lg">
                  <Bot className="h-7 w-7 text-cyan-300" />
                </div>
                <div className="absolute -inset-2 rounded-2xl bg-linear-to-r from-cyan-400/20 to-blue-500/20 blur-lg opacity-50 group-hover:opacity-75 transition-opacity duration-300" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-linear-to-r from-cyan-200 via-blue-200 to-violet-200 bg-clip-text text-transparent">
                  SynthxAI
                </h1>
                <p className="text-sm text-slate-400 font-medium">Advanced Synthetic Dataset Generator</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Status Indicators */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 rounded-full border border-emerald-400/50 bg-linear-to-r from-emerald-500/20 to-green-500/20 px-4 py-2 shadow-lg">
                  <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-400 shadow-[0_0_6px_#10b981]" />
                  <span className="text-sm font-semibold text-emerald-300">ONLINE</span>
                </div>
                
                <div className="flex items-center gap-2 rounded-full border border-blue-400/50 bg-linear-to-r from-blue-500/20 to-cyan-500/20 px-4 py-2 shadow-lg">
                  <div className="h-2 w-2 rounded-full bg-blue-400 animate-ping" />
                  <span className="text-sm font-semibold text-blue-300">AI ACTIVE</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Ultimate Professional Main Content Layout */}
      <div className="relative mx-auto max-w-[1600px] 3xl:max-w-[1800px] 4xl:max-w-[2000px] px-6 lg:px-8 py-12">
        {/* Revolutionary Asymmetric Grid - Optimized for All Screens */}
        <div className="grid gap-8 lg:gap-12 grid-cols-1 lg:grid-cols-[1.2fr_580px] xl:grid-cols-[1.3fr_650px] 2xl:grid-cols-[1.4fr_720px] 3xl:grid-cols-[1.5fr_800px] 4xl:grid-cols-[1.6fr_850px]">
          
          {/* Left Column - Streamlined Content */}
          <div className="space-y-12">
            {/* Schema Architect - Enhanced with better proportions */}
            <div className="group relative">
              <div className="absolute -inset-4 bg-linear-to-br from-cyan-500/15 via-blue-500/10 to-violet-500/15 rounded-4xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700" />
              <div className="relative">
                <SchemaArchitect
                  datasetName={datasetName}
                  setDatasetName={setDatasetName}
                  datasetNarrative={datasetNarrative}
                  setDatasetNarrative={setDatasetNarrative}
                  rowCount={rowCount}
                  setRowCount={setRowCount}
                  fields={fields}
                  onAddField={handleAddField}
                  onFieldChange={handleFieldChange}
                  onRemoveField={handleRemoveField}
                  onGenerateDataset={handleGenerateDataset}
                  isGenerating={isGenerating}
                />
              </div>
            </div>

            {/* Optimized Grid for Timeline and Telemetry */}
            <div className="grid gap-6 md:gap-8 grid-cols-1 md:grid-cols-2 min-h-0">
              {/* Synthesis Timeline */}
              <div className="group relative w-full">
                <div className="absolute -inset-4 bg-linear-to-br from-emerald-500/15 via-green-500/10 to-cyan-500/15 rounded-4xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700" />
                <div className="relative w-full">
                  <SynthesisTimeline
                    isGenerating={isGenerating}
                    activeStepIndex={currentStep}
                    llmMetrics={llmMetrics}
                  />
                </div>
              </div>

              {/* Signal Telemetry - Perfectly Positioned */}
              <div className="group relative w-full">
                <div className="absolute -inset-4 bg-linear-to-br from-amber-500/15 via-orange-500/10 to-red-500/15 rounded-4xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700" />
                <div className="relative w-full">
                  <SignalTelemetry telemetryData={telemetryData} />
                </div>
              </div>
            </div>

            {/* Dataset Preview - Full width for better data visibility */}
            <div className="group relative">
              <div className="absolute -inset-4 bg-linear-to-br from-violet-500/15 via-purple-500/10 to-pink-500/15 rounded-4xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700" />
              <div className="relative">
                <DatasetPreview
                  isGenerated={isGenerated}
                  previewData={previewData}
                  fields={fields}
                  stats={stats}
                />
              </div>
            </div>
          </div>

          {/* Right Column - Enhanced Chat Console */}
          <div className="sticky top-8 h-fit">
            <div className="space-y-8">
              <div className="group relative">
                <div className="absolute -inset-6 bg-linear-to-br from-blue-500/20 via-indigo-500/15 to-cyan-500/20 rounded-4xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700" />
                <div className="relative">
                  <ChatConsole
                    messages={messages}
                    chatDraft={inputValue}
                    setChatDraft={setInputValue}
                    onSendMessage={handleSendMessage}
                  />
                </div>
              </div>

              {/* System Status - Better positioned */}
              <div className="group relative">
                <div className="absolute -inset-4 bg-linear-to-br from-emerald-500/15 via-teal-500/10 to-blue-500/15 rounded-4xl blur-2xl opacity-0 group-hover:opacity-100 transition-all duration-700" />
                <div className="relative rounded-3xl border border-emerald-500/30 bg-slate-900/85 p-6 shadow-2xl backdrop-blur-sm">
                  <h3 className="text-lg font-semibold bg-linear-to-r from-emerald-200 to-cyan-200 bg-clip-text text-transparent mb-4">
                    System Status
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Active Sessions</span>
                      <span className="text-emerald-300 font-semibold">3,247</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Data Generated</span>
                      <span className="text-cyan-300 font-semibold">847.2 MB</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Uptime</span>
                      <span className="text-violet-300 font-semibold">99.8%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">AI Accuracy</span>
                      <span className="text-amber-300 font-semibold">97.3%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
