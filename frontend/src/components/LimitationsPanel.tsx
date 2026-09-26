"use client";

import React from "react";
import { Info } from "lucide-react";

interface LimitationsPanelProps {
  limitations: string[];
}

export const LimitationsPanel: React.FC<LimitationsPanelProps> = ({ limitations }) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <Info className="h-4 w-4 text-slate-400" />
          <span>Explicit Analysis Scope & Limitations</span>
        </h2>
        <span className="text-[11px] text-slate-500 font-mono">Boundaries</span>
      </div>

      <div className="mt-3.5 space-y-2">
        {limitations.map((lim, idx) => (
          <div
            key={idx}
            className="flex items-start space-x-2.5 text-xs text-slate-300 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-slate-500 mt-1.5 shrink-0" />
            <span className="leading-relaxed">{lim}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
