import { ChangeStoryReport, DemoScenario, VerificationResult } from "@/types/changestory";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function analyzeDiff(
  diffText: string,
  sourceMode: "sample" | "local" | "diff_only" = "diff_only"
): Promise<ChangeStoryReport> {
  const res = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      diff_text: diffText,
      source_mode: sourceMode,
    }),
  });

  if (!res.ok) {
    let errorDetail = `Backend returned status ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) errorDetail = err.detail;
    } catch {}
    throw new Error(errorDetail);
  }

  return res.json();
}

export async function getReport(sessionId: string): Promise<ChangeStoryReport> {
  const res = await fetch(`${API_BASE}/api/v1/reports/${sessionId}`);
  if (!res.ok) {
    throw new Error(`Report not found (${res.status})`);
  }
  return res.json();
}

export async function runVerification(sessionId: string): Promise<VerificationResult> {
  const res = await fetch(`${API_BASE}/api/v1/verify/${sessionId}`, {
    method: "POST",
  });
  if (!res.ok) {
    let errorDetail = `Verification failed with status ${res.status}`;
    try {
      const err = await res.json();
      if (err.detail) errorDetail = err.detail;
    } catch {}
    throw new Error(errorDetail);
  }
  return res.json();
}

export async function getScenarios(): Promise<DemoScenario[]> {
  const res = await fetch(`${API_BASE}/api/v1/scenarios`);
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export function getExportJsonUrl(sessionId: string): string {
  return `${API_BASE}/api/v1/reports/${sessionId}/export.json`;
}

export function getExportMdUrl(sessionId: string): string {
  return `${API_BASE}/api/v1/reports/${sessionId}/export.md`;
}
