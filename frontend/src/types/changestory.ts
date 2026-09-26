export type SymbolType = "function" | "method" | "class" | "async_function" | "async_method";
export type FileChangeStatus = "modified" | "added" | "deleted" | "renamed";
export type RiskSeverity = "low" | "medium" | "high";
export type ConfidenceLevel = "high" | "medium" | "low";
export type VerificationStatus = "passed" | "failed" | "error" | "not_run";

export interface Symbol {
  id: string;
  name: string;
  qualified_name: string;
  type: SymbolType;
  file_path: string;
  start_line: number;
  end_line: number;
  parent_class?: string | null;
}

export interface RelationshipEvidence {
  file_path: string;
  line: number;
  snippet: string;
}

export interface Relationship {
  source: string;
  target: string;
  relationship: string;
  evidence?: RelationshipEvidence | null;
}

export interface Evidence {
  id: string;
  kind: "changed_line" | "symbol_def" | "call_site" | "test_ref" | "file_change";
  file_path: string;
  line_start: number;
  line_end: number;
  symbol?: string | null;
  description: string;
}

export interface Risk {
  id: string;
  severity: RiskSeverity;
  title: string;
  description: string;
  related_symbols: string[];
  evidence_ids: string[];
  is_potential: boolean;
}

export interface TestRecommendation {
  id: string;
  title: string;
  reason: string;
  related_symbols: string[];
  evidence_ids: string[];
  confidence: ConfidenceLevel;
  test_file?: string | null;
  test_symbol?: string | null;
}

export interface FileChange {
  file_path: string;
  status: FileChangeStatus;
  lines_added: number;
  lines_deleted: number;
  changed_lines: number[];
  added_lines: number[];
  deleted_lines: number[];
  related_symbols: string[];
  evidence_ids: string[];
}

export interface VerificationResult {
  status: VerificationStatus;
  passed: string[];
  failed: string[];
  duration_seconds: number;
  summary: string;
}

export interface Explanation {
  symbol: string;
  file: string;
  lines: string;
  caller_count: number;
  affected_symbols: string[];
  text: string;
}

export interface ChangeSummary {
  files_changed: number;
  lines_added: number;
  lines_deleted: number;
  symbols_changed: number;
  symbols_affected: number;
  potential_risks: number;
  test_recommendations: number;
}

export interface ChangeStoryReport {
  schema_version: string;
  session_id: string;
  timestamp?: string | null;
  project?: {
    name: string;
    root?: string | null;
    git_root?: string | null;
    analysis_mode: "local" | "sample" | "diff_only";
  } | null;
  change_summary: ChangeSummary;
  files: FileChange[];
  changed_symbols: Symbol[];
  affected_symbols: Symbol[];
  relationships: Relationship[];
  evidence: Evidence[];
  risks: Risk[];
  test_recommendations: TestRecommendation[];
  verification?: VerificationResult | null;
  limitations: string[];
  explanations: Explanation[];
}

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  diff_file: string;
  diff_text: string;
}
