"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  ChangeStoryReport,
  DemoScenario,
  Evidence,
  FileChange,
  Risk,
  Symbol,
  TestRecommendation,
} from "@/types/changestory";
import {
  analyzeDiff,
  getReport,
  getScenarios,
  runVerification,
} from "@/lib/api";
import { Header } from "@/components/Header";
import { SummaryCards } from "@/components/SummaryCards";
import { DiffInput } from "@/components/DiffInput";
import { ChangedFilesPanel } from "@/components/ChangedFilesPanel";
import { ImpactGraph } from "@/components/ImpactGraph";
import { EvidenceDrawer } from "@/components/EvidenceDrawer";
import { RiskPanel } from "@/components/RiskPanel";
import { TestRecommendationPanel } from "@/components/TestRecommendationPanel";
import { VerificationPanel } from "@/components/VerificationPanel";
import { LimitationsPanel } from "@/components/LimitationsPanel";
import { ExportControls } from "@/components/ExportControls";
import { AlertCircle, RefreshCw } from "lucide-react";

function ChangeStoryDashboard() {
  const searchParams = useSearchParams();
  const urlSessionId = searchParams.get("session_id");

  const [diffText, setDiffText] = useState<string>("");
  const [report, setReport] = useState<ChangeStoryReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(null);

  // Inspector selection states
  const [selectedSymbol, setSelectedSymbol] = useState<Symbol | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileChange | null>(null);
  const [selectedRisk, setSelectedRisk] = useState<Risk | null>(null);
  const [selectedTestRec, setSelectedTestRec] = useState<TestRecommendation | null>(null);

  // Load scenarios on mount
  useEffect(() => {
    async function init() {
      try {
        const scList = await getScenarios();
        setScenarios(scList);

        if (urlSessionId) {
          setLoading(true);
          try {
            const rep = await getReport(urlSessionId);
            setReport(rep);
          } catch (e: any) {
            setError(e.message || "Failed to load session report");
          } finally {
            setLoading(false);
          }
        }
      } catch (err: any) {
        console.warn("Could not fetch scenarios from backend:", err);
      }
    }
    init();
  }, [urlSessionId]);

  const handleSelectScenario = (sc: DemoScenario) => {
    setActiveScenarioId(sc.id);
    setDiffText(sc.diff_text);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!diffText.trim()) return;
    setLoading(true);
    setError(null);
    clearInspector();

    try {
      // Demo diffs use the bundled sample context. Pasted diffs are labeled
      // diff-only so the report does not imply repository-wide impact coverage.
      const sourceMode = activeScenarioId ? "sample" : "diff_only";
      const rep = await analyzeDiff(diffText, sourceMode);
      setReport(rep);
    } catch (err: any) {
      setError(err.message || "Analysis request failed. Ensure ChangeStory backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setDiffText("");
    setReport(null);
    setError(null);
    setActiveScenarioId(null);
    clearInspector();
  };

  const handleRunVerification = async () => {
    if (!report) return;
    setVerifying(true);
    setError(null);

    try {
      const verResult = await runVerification(report.session_id);
      setReport({
        ...report,
        verification: verResult,
      });
    } catch (err: any) {
      setError(err.message || "Controlled verification execution failed.");
    } finally {
      setVerifying(false);
    }
  };

  const clearInspector = () => {
    setSelectedSymbol(null);
    setSelectedFile(null);
    setSelectedRisk(null);
    setSelectedTestRec(null);
  };

  const onSelectFile = (file: FileChange) => {
    setSelectedFile(file);
    setSelectedSymbol(null);
    setSelectedRisk(null);
    setSelectedTestRec(null);
  };

  const onSelectSymbol = (sym: Symbol) => {
    setSelectedSymbol(sym);
    setSelectedFile(null);
    setSelectedRisk(null);
    setSelectedTestRec(null);
  };

  const onSelectRisk = (risk: Risk) => {
    setSelectedRisk(risk);
    setSelectedSymbol(null);
    setSelectedFile(null);
    setSelectedTestRec(null);
  };

  const onSelectTestRec = (rec: TestRecommendation) => {
    setSelectedTestRec(rec);
    setSelectedSymbol(null);
    setSelectedFile(null);
    setSelectedRisk(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      <Header sessionId={report?.session_id} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Error notification banner if any */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-200 text-xs flex items-center justify-between shadow-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-rose-400 hover:text-white text-xs font-semibold underline ml-4"
            >
              Dismiss
            </button>
          </div>
        )}

        {!urlSessionId && !report && (
          <section className="rounded-xl border border-cyan-900/60 bg-cyan-950/25 p-5">
            <h2 className="text-sm font-semibold text-cyan-100">Analyze changes in your local project</h2>
            <p className="mt-1 text-xs text-slate-300">
              Run <code className="text-cyan-300">changestory init</code> once, then <code className="text-cyan-300">changestory analyze</code> after code changes. The CLI uses your Git repository for caller and test context, then opens this dashboard with the report.
            </p>
          </section>
        )}

        {/* Advanced diff input and demo scenarios */}
        <DiffInput
          diffText={diffText}
          onChangeDiff={(text) => {
            setDiffText(text);
            if (activeScenarioId && text !== scenarios.find((scenario) => scenario.id === activeScenarioId)?.diff_text) {
              setActiveScenarioId(null);
            }
          }}
          onAnalyze={handleAnalyze}
          onReset={handleReset}
          loading={loading}
          scenarios={scenarios}
          onSelectScenario={handleSelectScenario}
          activeScenarioId={activeScenarioId}
        />

        {/* Analysis Output Section */}
        {report && (
          <div className="space-y-6">
            {/* Top Bar with Summary & Export Actions */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-white tracking-tight">
                  Analysis Findings & Impact Map
                </h2>
                <p className="text-xs text-slate-400">
                  {report.project?.name ? `${report.project.name} · ${report.project.analysis_mode} analysis · ` : ""}
                  Generated at {report.timestamp ? new Date(report.timestamp).toLocaleTimeString() : "N/A"}
                </p>
              </div>

              <ExportControls sessionId={report.session_id} />
            </div>

            {/* Summary Cards */}
            <SummaryCards summary={report.change_summary} />

            {/* Main Interactive Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Changed Files List */}
              <div className="lg:col-span-1">
                <ChangedFilesPanel
                  files={report.files}
                  onSelectFile={onSelectFile}
                  selectedFilePath={selectedFile?.file_path}
                />
              </div>

              {/* Center Column: Impact & Caller Graph */}
              <div className="lg:col-span-2">
                <ImpactGraph
                  changedSymbols={report.changed_symbols}
                  affectedSymbols={report.affected_symbols}
                  relationships={report.relationships}
                  onSelectSymbol={onSelectSymbol}
                  selectedSymbolId={selectedSymbol?.id}
                />
              </div>
            </div>

            {/* Lower Grid: Risks, Test Recommendations, and Inspector */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Potential Risks */}
              <div>
                <RiskPanel
                  risks={report.risks}
                  onSelectRisk={onSelectRisk}
                  selectedRiskId={selectedRisk?.id}
                />
              </div>

              {/* Recommended Tests */}
              <div>
                <TestRecommendationPanel
                  recommendations={report.test_recommendations}
                  onSelectRecommendation={onSelectTestRec}
                  selectedRecId={selectedTestRec?.id}
                />
              </div>

              {/* Evidence & Inspector Drawer */}
              <div>
                <EvidenceDrawer
                  selectedSymbol={selectedSymbol}
                  selectedFile={selectedFile}
                  selectedRisk={selectedRisk}
                  selectedTestRec={selectedTestRec}
                  allEvidence={report.evidence}
                  explanations={report.explanations}
                  onClearSelection={clearInspector}
                />
              </div>
            </div>

            {/* Controlled Test Verification */}
            <VerificationPanel
              sessionId={report.session_id}
              verification={report.verification}
              onRunVerification={handleRunVerification}
              loading={verifying}
              enabled={report.project?.analysis_mode === "sample"}
            />

            {/* Explicit Limitations Section */}
            <LimitationsPanel limitations={report.limitations} />
          </div>
        )}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-6 px-6 text-center text-xs text-slate-500">
        ChangeStory • Deterministic Code Change Impact Engine • Python AST Analysis
      </footer>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950 flex items-center justify-center text-xs text-slate-400">Loading ChangeStory...</div>}>
      <ChangeStoryDashboard />
    </Suspense>
  );
}
