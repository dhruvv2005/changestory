"use client";

import React from "react";
import { TestRecommendation } from "@/types/changestory";
import { CheckSquare, ChevronRight } from "lucide-react";

interface TestRecommendationPanelProps {
  recommendations: TestRecommendation[];
  onSelectRecommendation: (rec: TestRecommendation) => void;
  selectedRecId?: string | null;
}

export const TestRecommendationPanel: React.FC<TestRecommendationPanelProps> = ({
  recommendations,
  onSelectRecommendation,
  selectedRecId,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <CheckSquare className="h-4 w-4 text-emerald-400" />
          <span>Recommended Tests ({recommendations.length})</span>
        </h2>
        <span className="text-[11px] text-slate-400">Static AST suggestions</span>
      </div>

      <div className="mt-3.5 space-y-2.5 overflow-y-auto max-h-[380px] pr-1">
        {recommendations.length === 0 ? (
          <div className="text-xs text-slate-500 italic py-8 text-center">
            No targeted tests statically detected for changed symbols.
          </div>
        ) : (
          recommendations.map((rec) => {
            const isSelected = selectedRecId === rec.id;
            const badgeColor =
              rec.confidence === "high"
                ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                : rec.confidence === "medium"
                ? "bg-cyan-950 text-cyan-300 border-cyan-800"
                : "bg-slate-800 text-slate-300 border-slate-700";

            return (
              <div
                key={rec.id}
                onClick={() => onSelectRecommendation(rec)}
                className={`p-3.5 rounded-lg border cursor-pointer transition ${
                  isSelected
                    ? "bg-slate-800/90 border-emerald-500/80 shadow-md shadow-emerald-950/40"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="text-xs font-semibold text-white">
                    {rec.title}
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border shrink-0 ${badgeColor}`}>
                    {rec.confidence} confidence
                  </span>
                </div>

                <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                  {rec.reason}
                </p>

                {rec.related_symbols.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-1">
                    {rec.related_symbols.map((sym, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-300"
                      >
                        {sym.split(".").pop()}
                      </span>
                    ))}
                  </div>
                )}

                <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-800/60 pt-2">
                  <span>{rec.evidence_ids.length} test reference(s)</span>
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
