"use client";

import React from "react";
import { ChangeSummary } from "@/types/changestory";
import { FileCode, FunctionSquare, Network, AlertTriangle, CheckSquare } from "lucide-react";

interface SummaryCardsProps {
  summary: ChangeSummary;
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({ summary }) => {
  const cards = [
    {
      label: "Files Changed",
      value: summary.files_changed,
      sub: `+${summary.lines_added} / -${summary.lines_deleted} lines`,
      icon: FileCode,
      color: "text-blue-400",
      border: "border-blue-900/40",
      bg: "bg-blue-950/20",
    },
    {
      label: "Symbols Changed",
      value: summary.symbols_changed,
      sub: "Functions & methods",
      icon: FunctionSquare,
      color: "text-cyan-400",
      border: "border-cyan-900/40",
      bg: "bg-cyan-950/20",
    },
    {
      label: "Direct Callers Affected",
      value: summary.symbols_affected,
      sub: "Statically resolved",
      icon: Network,
      color: "text-purple-400",
      border: "border-purple-900/40",
      bg: "bg-purple-950/20",
    },
    {
      label: "Potential Risks",
      value: summary.potential_risks,
      sub: summary.potential_risks > 0 ? "Review findings" : "No risks detected",
      icon: AlertTriangle,
      color: summary.potential_risks > 0 ? "text-amber-400" : "text-emerald-400",
      border: summary.potential_risks > 0 ? "border-amber-900/40" : "border-emerald-900/40",
      bg: summary.potential_risks > 0 ? "bg-amber-950/20" : "bg-emerald-950/20",
    },
    {
      label: "Test Recommendations",
      value: summary.test_recommendations,
      sub: "Targeted test candidates",
      icon: CheckSquare,
      color: "text-emerald-400",
      border: "border-emerald-900/40",
      bg: "bg-emerald-950/20",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div
            key={i}
            className={`p-4 rounded-xl border ${c.border} ${c.bg} backdrop-blur-sm flex flex-col justify-between`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">{c.label}</span>
              <Icon className={`h-4 w-4 ${c.color}`} />
            </div>
            <div className="mt-3">
              <div className="text-2xl font-bold text-white tracking-tight">{c.value}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">{c.sub}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
