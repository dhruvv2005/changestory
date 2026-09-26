"use client";

import React, { useState } from "react";
import { DemoScenario } from "@/types/changestory";
import { Play, RotateCcw, Sparkles, FileCode, Check } from "lucide-react";

interface DiffInputProps {
  diffText: string;
  onChangeDiff: (text: string) => void;
  onAnalyze: () => void;
  onReset: () => void;
  loading: boolean;
  scenarios: DemoScenario[];
  onSelectScenario: (scenario: DemoScenario) => void;
  activeScenarioId?: string | null;
}

export const DiffInput: React.FC<DiffInputProps> = ({
  diffText,
  onChangeDiff,
  onAnalyze,
  onReset,
  loading,
  scenarios,
  onSelectScenario,
  activeScenarioId,
}) => {
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleAnalyzeClick = () => {
    if (!diffText.trim()) {
      setErrorMsg("Please provide unified git diff content or select a demo scenario.");
      return;
    }
    setErrorMsg(null);
    onAnalyze();
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-800/80 gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
            <FileCode className="h-4 w-4 text-cyan-400" />
            <span>Unified Diff Input</span>
          </h2>
          <p className="text-xs text-slate-400">
            Paste a Git diff or select one of the controlled scenarios below
          </p>
        </div>

        {/* Demo Scenario Selectors */}
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-slate-400 mr-1 flex items-center">
            <Sparkles className="h-3.5 w-3.5 text-amber-400 mr-1" /> Scenarios:
          </span>
          {scenarios.map((sc) => {
            const isSelected = activeScenarioId === sc.id;
            return (
              <button
                key={sc.id}
                type="button"
                onClick={() => {
                  setErrorMsg(null);
                  onSelectScenario(sc);
                }}
                className={`text-xs px-2.5 py-1 rounded-md transition font-medium border ${
                  isSelected
                    ? "bg-cyan-950 text-cyan-300 border-cyan-500/60 shadow-sm shadow-cyan-950"
                    : "bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-800 hover:text-white"
                }`}
                title={sc.description}
              >
                {sc.name.split("—")[0].trim()}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-3.5">
        <textarea
          value={diffText}
          onChange={(e) => {
            setErrorMsg(null);
            onChangeDiff(e.target.value);
          }}
          placeholder="Paste unified git diff here (e.g. diff --git a/... b/... or --- a/... +++ b/...)"
          rows={6}
          className="w-full font-mono text-xs bg-slate-950/80 text-slate-200 border border-slate-800 rounded-lg p-3 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 resize-y placeholder:text-slate-600"
        />
      </div>

      {errorMsg && (
        <div className="mt-2 text-xs text-rose-400 bg-rose-950/30 border border-rose-900/40 p-2 rounded">
          {errorMsg}
        </div>
      )}

      <div className="mt-3.5 flex items-center justify-between">
        <span className="text-xs text-slate-400">
          Target: <strong className="text-slate-300">Controlled Sample Project (changestory_sample)</strong>
        </span>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={onReset}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800/60 hover:bg-slate-800 rounded-md border border-slate-700/60 transition disabled:opacity-50"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset</span>
          </button>

          <button
            type="button"
            onClick={handleAnalyzeClick}
            disabled={loading}
            className="flex items-center space-x-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-md shadow-md shadow-cyan-900/30 transition disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Run Analysis</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
