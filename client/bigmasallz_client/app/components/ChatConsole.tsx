"use client";

import { FormEvent } from "react";
import clsx from "clsx";
import { Bot, User, WandSparkles } from "lucide-react";
import type { ChatMessage } from "./types";

interface ChatConsoleProps {
  messages: ChatMessage[];
  chatDraft: string;
  setChatDraft: (value: string) => void;
  onSendMessage: (event: FormEvent<HTMLFormElement>) => void;
}

export default function ChatConsole({
  messages,
  chatDraft,
  setChatDraft,
  onSendMessage,
}: ChatConsoleProps) {
  return (
    <div className="glass-panel group relative overflow-hidden rounded-3xl border border-cyan-500/30 bg-slate-900/90 shadow-2xl transition duration-500 hover:border-violet-400/40 hover:shadow-[0_0_100px_rgba(124,58,237,0.4)]">
      {/* Enhanced background effects for wider container */}
      <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-700 group-hover:opacity-100">
        <div className="absolute inset-x-8 -top-24 h-48 rounded-full bg-linear-to-b from-cyan-500/25 via-blue-500/20 to-transparent blur-3xl animate-drift-slow" />
        <div className="absolute -right-20 top-1/2 h-96 w-40 -translate-y-1/2 rotate-12 bg-linear-to-t from-transparent via-violet-500/30 to-transparent blur-3xl animate-drift-slow" />
        <div className="absolute -left-20 bottom-1/3 h-96 w-40 translate-y-1/2 -rotate-12 bg-linear-to-t from-transparent via-emerald-500/25 to-transparent blur-3xl animate-drift-slow" />
      </div>
      
      {/* Elegant side borders with gradient enhancement */}
      <div className="absolute inset-y-8 left-0 w-px bg-linear-to-b from-transparent via-cyan-500/50 to-transparent opacity-70" />
      <div className="absolute inset-y-8 right-0 w-px bg-linear-to-b from-transparent via-violet-500/50 to-transparent opacity-70" />
      
      <div className="relative z-10 p-8">
        {/* Enhanced Header with more space */}
        <div className="mb-8 flex items-center justify-between rounded-2xl border border-cyan-500/40 bg-slate-950/80 px-6 py-5 shadow-[0_0_50px_rgba(14,165,233,0.3)]">
          <div className="flex items-center gap-4">
            <div className="relative">
              <WandSparkles className="h-6 w-6 text-cyan-300" />
              <div className="absolute -inset-1 bg-cyan-400/20 rounded-lg blur-sm" />
            </div>
            <div>
              <span className="text-lg font-bold bg-linear-to-r from-cyan-200 to-blue-200 bg-clip-text text-transparent uppercase tracking-[0.3em]">
                AI Console
              </span>
              <p className="text-xs text-slate-400 font-medium mt-1">Neural Processing Interface</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="h-3 w-3 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_12px_#10b981]" />
            <span className="text-sm text-emerald-300 font-semibold">NEURAL LINK ACTIVE</span>
          </div>
        </div>
        
        {/* Enhanced Messages Area with better use of width */}
        <div className="h-[500px] lg:h-[600px] xl:h-[650px] 2xl:h-[700px] max-h-[75vh] flex flex-col bg-slate-950/30 rounded-2xl border border-slate-700/50 p-4 lg:p-6">
          <div className="flex-1 space-y-4 lg:space-y-6 overflow-y-auto pr-2 lg:pr-4 scrollbar-thin scrollbar-track-slate-800/50 scrollbar-thumb-cyan-500/50">
            {messages.map((message) => (
              <div
                key={message.id}
                className={clsx(
                  "flex w-full",
                  message.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={clsx(
                    "flex max-w-[85%] lg:max-w-[80%] xl:max-w-[75%] min-w-[200px] items-start gap-3 lg:gap-4",
                    message.role === "user"
                      ? "flex-row-reverse text-right"
                      : "flex-row text-left"
                  )}
                >
                  <div
                    className={clsx(
                      "shrink-0 rounded-full border p-3 shadow-[0_0_30px_rgba(59,130,246,0.3)]",
                      message.role === "user"
                        ? "border-cyan-500/60 bg-linear-to-b from-cyan-500/30 via-cyan-600/15 to-transparent text-cyan-200"
                        : "border-purple-500/60 bg-linear-to-b from-purple-500/30 via-purple-600/15 to-transparent text-purple-200"
                    )}
                  >
                    {message.role === "user" ? (
                      <User className="h-5 w-5" />
                    ) : (
                      <Bot className="h-5 w-5" />
                    )}
                  </div>
                  <div
                    className={clsx(
                      "rounded-2xl border px-6 py-4 text-sm leading-7 shadow-lg transition-all duration-500 hover:-translate-y-1 hover:shadow-[0_0_60px_rgba(0,212,255,0.25)] backdrop-blur-sm",
                      message.role === "user"
                        ? "border-cyan-500/40 bg-linear-to-r from-cyan-500/25 via-cyan-500/15 to-transparent text-cyan-100"
                        : "border-purple-500/40 bg-linear-to-r from-purple-500/25 via-purple-500/15 to-transparent text-purple-100"
                    )}
                  >
                    <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.4em] text-slate-300 mb-3">
                      <span className="font-semibold">
                        {message.role === "user" ? "OPERATOR" : "SYNTHX CORE"}
                      </span>
                      <span className="opacity-70">{message.timestamp}</span>
                    </div>
                    <p className="text-base leading-relaxed">{message.content}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Enhanced Input Area */}
          <form onSubmit={onSendMessage} className="mt-4 lg:mt-6 flex gap-3 lg:gap-4">
            <textarea
              value={chatDraft}
              onChange={(event) => setChatDraft(event.target.value)}
              placeholder="Describe the dataset intent, features, constraints, and synthesis requirements..."
              className="min-h-12 lg:min-h-16 flex-1 resize-none rounded-2xl border border-cyan-500/30 bg-slate-900/70 px-4 lg:px-5 py-3 lg:py-4 text-sm text-slate-100 placeholder:text-slate-500 transition focus:border-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-300/40 backdrop-blur-sm"
              rows={2}
            />
            <button
              type="submit"
              className="group flex items-center gap-2 lg:gap-3 rounded-2xl border border-cyan-500/50 bg-linear-to-r from-cyan-500/50 via-sky-500/50 to-teal-500/40 px-4 lg:px-6 py-3 lg:py-4 text-xs lg:text-sm font-bold uppercase tracking-[0.3em] text-cyan-50 transition hover:-translate-y-1 hover:border-cyan-200/70 hover:shadow-[0_0_60px_rgba(0,242,255,0.35)] min-w-[100px] lg:min-w-[120px]"
            >
              <WandSparkles className="h-4 lg:h-5 w-4 lg:w-5 transition group-hover:scale-110 group-hover:rotate-12" />
              <span className="hidden sm:inline">Engage</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}