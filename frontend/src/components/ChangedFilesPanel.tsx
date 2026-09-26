"use client";

import React from "react";
import { FileChange } from "@/types/changestory";
import { FileText, Plus, Minus, Search } from "lucide-react";

interface ChangedFilesPanelProps {
  files: FileChange[];
  onSelectFile: (file: FileChange) => void;
  selectedFilePath?: string | null;
}

export const ChangedFilesPanel: React.FC<ChangedFilesPanelProps> = ({
  files,
  onSelectFile,
  selectedFilePath,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <FileText className="h-4 w-4 text-cyan-400" />
          <span>Changed Files ({files.length})</span>
        </h2>
        <span className="text-[11px] text-slate-400">Click to view evidence</span>
      </div>

      <div className="mt-3.5 space-y-2 overflow-y-auto max-h-[380px] pr-1">
        {files.length === 0 ? (
          <div className="text-xs text-slate-500 italic py-6 text-center">
            No files changed in this analysis.
          </div>
        ) : (
          files.map((f) => {
            const isSelected = selectedFilePath === f.file_path;
            const statusColor =
              f.status === "added"
                ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                : f.status === "deleted"
                ? "bg-rose-950 text-rose-300 border-rose-800"
                : "bg-blue-950 text-blue-300 border-blue-800";

            return (
              <div
                key={f.file_path}
                onClick={() => onSelectFile(f)}
                className={`p-3 rounded-lg border cursor-pointer transition flex flex-col justify-between ${
                  isSelected
                    ? "bg-slate-800/90 border-cyan-500/80 shadow-md shadow-cyan-950/40"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/50"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="font-mono text-xs text-slate-200 truncate font-medium">
                    {f.file_path}
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border ${statusColor}`}>
                    {f.status}
                  </span>
                </div>

                <div className="flex items-center justify-between mt-2 text-[11px] text-slate-400">
                  <div className="flex items-center space-x-2">
                    <span className="flex items-center text-emerald-400">
                      <Plus className="h-3 w-3 mr-0.5" /> {f.lines_added}
                    </span>
                    <span className="flex items-center text-rose-400">
                      <Minus className="h-3 w-3 mr-0.5" /> {f.lines_deleted}
                    </span>
                  </div>

                  <div className="text-slate-400 text-[10px]">
                    {f.related_symbols.length} symbol(s) mapped
                  </div>
                </div>

                {f.related_symbols.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {f.related_symbols.map((sym, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300"
                      >
                        {sym.split(".").pop()}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
