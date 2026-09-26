"use client";

import React from "react";
import { Evidence, Explanation, FileChange, Risk, Symbol, TestRecommendation } from "@/types/changestory";
import { ShieldCheck, Info, FileCode, CheckCircle2, AlertTriangle } from "lucide-react";

interface EvidenceDrawerProps {
  selectedSymbol?: Symbol | null;
  selectedFile?: FileChange | null;
  selectedRisk?: Risk | null;
  selectedTestRec?: TestRecommendation | null;
  allEvidence: Evidence[];
  explanations: Explanation[];
  onClearSelection: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  selectedSymbol,
  selectedFile,
  selectedRisk,
  selectedTestRec,
  allEvidence,
  explanations,
  onClearSelection,
}) => {
  if (!selectedSymbol && !selectedFile && !selectedRisk && !selectedTestRec) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-center items-center text-center min-h-[300px]">
        <ShieldCheck className="h-10 w-10 text-slate-700 mb-2" />
        <h3 className="text-sm font-semibold text-slate-300">Evidence & Inspector</h3>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Select any changed file, graph symbol node, risk item, or test recommendation to inspect supporting evidence and verified line ranges.
        </p>
      </div>
    );
  }

  // Find relevant evidence items
  let relevantEvidence: Evidence[] = [];
  let explanationText: string | null = null;

  if (selectedSymbol) {
    relevantEvidence = allEvidence.filter(
      (e) => e.symbol === selectedSymbol.qualified_name || (e.file_path === selectedSymbol.file_path && e.line_start >= selectedSymbol.start_line && e.line_end <= selectedSymbol.end_line)
    );
    const exp = explanations.find((x) => x.symbol === selectedSymbol.qualified_name);
    if (exp) explanationText = exp.text;
  } else if (selectedFile) {
    relevantEvidence = allEvidence.filter((e) => e.file_path === selectedFile.file_path);
  } else if (selectedRisk) {
    relevantEvidence = allEvidence.filter((e) => selectedRisk.evidence_ids.includes(e.id));
  } else if (selectedTestRec) {
    relevantEvidence = allEvidence.filter((e) => selectedTestRec.evidence_ids.includes(e.id));
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Info className="h-4 w-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white">Evidence & Details Inspector</h2>
        </div>
        <button
          onClick={onClearSelection}
          className="text-xs text-slate-400 hover:text-slate-200 transition"
        >
          Clear
        </button>
      </div>

      <div className="mt-3.5 space-y-4">
        {/* Selected Entity Title & Meta */}
        {selectedSymbol && (
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-cyan-300">
                {selectedSymbol.name}
              </span>
              <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                {selectedSymbol.type}
              </span>
            </div>
            <div className="text-[11px] font-mono text-slate-400 mt-1">
              {selectedSymbol.file_path}:{selectedSymbol.start_line}-{selectedSymbol.end_line}
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Qualified Name: <code className="text-slate-400">{selectedSymbol.qualified_name}</code>
            </div>
          </div>
        )}

        {selectedFile && (
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-slate-200 truncate">
                {selectedFile.file_path}
              </span>
              <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                {selectedFile.status}
              </span>
            </div>
            <div className="text-xs text-slate-400 mt-1">
              +{selectedFile.lines_added} / -{selectedFile.lines_deleted} lines changed
            </div>
          </div>
        )}

        {selectedRisk && (
          <div className="p-3 bg-amber-950/20 rounded-lg border border-amber-900/40">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-300">
                {selectedRisk.title}
              </span>
              <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                {selectedRisk.severity}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1.5">
              {selectedRisk.description}
            </p>
          </div>
        )}

        {selectedTestRec && (
          <div className="p-3 bg-emerald-950/20 rounded-lg border border-emerald-900/40">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-300">
                {selectedTestRec.title}
              </span>
              <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                {selectedTestRec.confidence} confidence
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1.5">
              {selectedTestRec.reason}
            </p>
          </div>
        )}

        {/* Deterministic Explanation snippet if available */}
        {explanationText && (
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
            <div className="text-xs font-semibold text-slate-400 mb-1">Deterministic Explanation:</div>
            <pre className="text-[11px] font-mono text-slate-300 whitespace-pre-wrap leading-relaxed">
              {explanationText}
            </pre>
          </div>
        )}

        {/* Supporting Evidence Items */}
        <div>
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Supporting Evidence ({relevantEvidence.length})
          </h3>
          {relevantEvidence.length === 0 ? (
            <div className="text-xs text-slate-500 italic p-3 bg-slate-950 rounded border border-slate-800">
              Evidence unavailable for this element.
            </div>
          ) : (
            <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
              {relevantEvidence.map((ev) => (
                <div
                  key={ev.id}
                  className="p-2.5 rounded bg-slate-950 border border-slate-800/80 text-xs"
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-mono text-cyan-400">{ev.file_path}</span>
                    <span className="font-mono text-slate-400">
                      Lines {ev.line_start}{ev.line_start !== ev.line_end ? `-${ev.line_end}` : ""}
                    </span>
                  </div>
                  <div className="text-slate-300 mt-1 text-[11px]">{ev.description}</div>
                  <div className="mt-1 flex items-center justify-between text-[10px] text-slate-500">
                    <span>Kind: {ev.kind}</span>
                    <span className="font-mono">{ev.id}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
