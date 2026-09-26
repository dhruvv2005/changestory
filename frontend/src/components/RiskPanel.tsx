"use client";

import React from "react";
import { Risk } from "@/types/changestory";
import { AlertTriangle, ShieldCheck, ChevronRight } from "lucide-react";

interface RiskPanelProps {
  risks: Risk[];
  onSelectRisk: (risk: Risk) => void;
  selectedRiskId?: string | null;
}

export const RiskPanel: React.FC<RiskPanelProps> = ({
  risks,
  onSelectRisk,
  selectedRiskId,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          <span>Potential Risks ({risks.length})</span>
        </h2>
        <span className="text-[11px] text-slate-400">Deterministic findings</span>
      </div>

      <div className="mt-3.5 space-y-2.5 overflow-y-auto max-h-[380px] pr-1">
        {risks.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center py-8 text-slate-500 text-xs">
            <ShieldCheck className="h-8 w-8 text-emerald-500/40 mb-1.5" />
            <span className="text-emerald-400 font-medium">No potential risks detected</span>
            <span className="text-[11px] text-slate-500 mt-0.5">
              Change meets conservative stability and coverage rules.
            </span>
          </div>
        ) : (
          risks.map((risk) => {
            const isSelected = selectedRiskId === risk.id;
            const badgeColor =
              risk.severity === "high"
                ? "bg-rose-950 text-rose-300 border-rose-800"
                : risk.severity === "medium"
                ? "bg-amber-950 text-amber-300 border-amber-800"
                : "bg-blue-950 text-blue-300 border-blue-800";

            return (
              <div
                key={risk.id}
                onClick={() => onSelectRisk(risk)}
                className={`p-3.5 rounded-lg border cursor-pointer transition ${
                  isSelected
                    ? "bg-slate-800/90 border-amber-500/80 shadow-md shadow-amber-950/40"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="text-xs font-semibold text-white">
                    {risk.title}
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border shrink-0 ${badgeColor}`}>
                    {risk.severity}
                  </span>
                </div>

                <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                  {risk.description}
                </p>

                {risk.related_symbols.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-1">
                    {risk.related_symbols.map((sym, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400"
                      >
                        {sym.split(".").pop()}
                      </span>
                    ))}
                  </div>
                )}

                <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-800/60 pt-2">
                  <span>{risk.evidence_ids.length} supporting evidence item(s)</span>
                  <span className="flex items-center text-cyan-400 font-medium hover:underline">
                    Inspect <ChevronRight className="h-3 w-3 ml-0.5" />
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
