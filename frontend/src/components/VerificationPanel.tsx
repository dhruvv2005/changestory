"use client";

import React, { useState } from "react";
import { VerificationResult } from "@/types/changestory";
import { ShieldCheck, Play, CheckCircle2, XCircle, AlertCircle, Clock } from "lucide-react";

interface VerificationPanelProps {
  sessionId: string;
  verification?: VerificationResult | null;
  onRunVerification: () => Promise<void>;
  loading: boolean;
  enabled?: boolean;
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({
  sessionId,
  verification,
  onRunVerification,
  loading,
  enabled = true,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            <span>Controlled Test Verification</span>
          </h2>
          <p className="text-xs text-slate-400">
            Executes only predefined tests against the controlled sample project (No shell=True)
          </p>
        </div>

        <button
          type="button"
          onClick={onRunVerification}
          disabled={loading || !enabled}
          className="flex items-center space-x-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 rounded-md shadow-md shadow-emerald-950/40 transition disabled:opacity-50 self-start sm:self-auto"
        >
          {loading ? (
            <>
              <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Running Pytest...</span>
            </>
          ) : !enabled ? (
            <span>Sample verification only</span>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Run Controlled Verification</span>
            </>
          )}
        </button>
      </div>

      <div className="mt-4">
        {!verification ? (
          <div className="p-6 text-center rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-500">
            <Clock className="h-6 w-6 text-slate-600 mx-auto mb-2" />
            <span className="font-medium text-slate-400">No controlled verification has been run yet.</span>
            <p className="text-[11px] text-slate-600 mt-1 max-w-sm mx-auto">
              Click &quot;Run Controlled Verification&quot; to execute pytest in a sandboxed, predefined subprocess against the sample repository.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Status Header */}
            <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center space-x-3">
                {verification.status === "passed" ? (
                  <CheckCircle2 className="h-6 w-6 text-emerald-400 shrink-0" />
                ) : verification.status === "failed" ? (
                  <XCircle className="h-6 w-6 text-rose-400 shrink-0" />
                ) : (
                  <AlertCircle className="h-6 w-6 text-amber-400 shrink-0" />
                )}
                <div>
                  <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center space-x-2">
                    <span>Actual Execution: {verification.status}</span>
                    <span className="text-[10px] text-slate-400 lowercase font-normal">
                      ({verification.duration_seconds}s)
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 mt-0.5">{verification.summary}</div>
                </div>
              </div>

              <div className="flex items-center space-x-3 text-xs">
                <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono font-semibold">
                  {verification.passed.length} Passed
                </span>
                <span className="px-2.5 py-1 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono font-semibold">
                  {verification.failed.length} Failed
                </span>
              </div>
            </div>

            {/* Test lists */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Passed */}
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <div className="text-xs font-semibold text-emerald-400 mb-2 flex items-center">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Verified Passed Tests ({verification.passed.length})
                </div>
                <div className="space-y-1 max-h-[160px] overflow-y-auto pr-1">
                  {verification.passed.length === 0 ? (
                    <div className="text-[11px] text-slate-600 italic">None</div>
                  ) : (
                    verification.passed.map((t, idx) => (
                      <div key={idx} className="font-mono text-[11px] text-slate-300 bg-slate-900/60 p-1.5 rounded border border-slate-800/80 truncate">
                        {t}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Failed */}
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                <div className="text-xs font-semibold text-rose-400 mb-2 flex items-center">
                  <XCircle className="h-3.5 w-3.5 mr-1" /> Failed Tests ({verification.failed.length})
                </div>
                <div className="space-y-1 max-h-[160px] overflow-y-auto pr-1">
                  {verification.failed.length === 0 ? (
                    <div className="text-[11px] text-slate-600 italic">No tests failed.</div>
                  ) : (
                    verification.failed.map((t, idx) => (
                      <div key={idx} className="font-mono text-[11px] text-rose-300 bg-rose-950/20 p-1.5 rounded border border-rose-900/40 truncate">
                        {t}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
