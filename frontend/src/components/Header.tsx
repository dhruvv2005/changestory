"use client";

import React from "react";
import { GitCommit, Layers, Terminal, ShieldAlert } from "lucide-react";

interface HeaderProps {
  sessionId?: string | null;
}

export const Header: React.FC<HeaderProps> = ({ sessionId }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-40 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <GitCommit className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white">ChangeStory</h1>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                MVP v1.0 • Python AST
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Deterministic change impact, caller graph, and evidence engine
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          {sessionId && (
            <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 border border-slate-700/60 rounded-md">
              <span className="text-slate-500">Session:</span>
              <span className="font-mono text-cyan-300 font-semibold">{sessionId}</span>
            </div>
          )}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-md text-slate-300">
            <Terminal className="h-3.5 w-3.5 text-slate-400" />
            <span>CLI: <code className="text-cyan-400">changestory analyze</code></span>
          </div>
        </div>
      </div>
    </header>
  );
};
