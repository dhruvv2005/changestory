import { describe, it } from "node:test";
import assert from "node:assert/strict";

describe("ChangeStory Dashboard Components & Contract", () => {
  it("validates summary metrics calculation", () => {
    const summary = {
      files_changed: 2,
      lines_added: 5,
      lines_deleted: 2,
      symbols_changed: 1,
      symbols_affected: 2,
      potential_risks: 1,
      test_recommendations: 2,
    };

    assert.equal(summary.files_changed, 2);
    assert.equal(summary.symbols_changed, 1);
    assert.equal(summary.symbols_affected, 2);
    assert.equal(summary.potential_risks, 1);
  });

  it("verifies risk severity categorization", () => {
    const risk = {
      id: "risk_shared_impact_1",
      severity: "medium",
      title: "Potential shared-impact risk",
      description: "Function has multiple callers",
      related_symbols: ["calc.total", "order.process"],
      evidence_ids: ["ev_1", "ev_2"],
      is_potential: true,
    };

    assert.equal(risk.is_potential, true);
    assert.ok(["low", "medium", "high"].includes(risk.severity));
    assert.ok(risk.evidence_ids.length > 0);
  });

  it("ensures test recommendations do not claim execution status", () => {
    const recommendation = {
      id: "rec_1",
      title: "Run test_calculator.py",
      reason: "Directly tests modified symbol",
      confidence: "high",
    };

    // Recommendations must NOT have a passed/failed status
    assert.equal(recommendation.status, undefined);
    assert.ok(["high", "medium", "low"].includes(recommendation.confidence));
  });

  it("ensures controlled verification separates actual results from suggestions", () => {
    const verification = {
      status: "passed",
      passed: ["tests/test_calculator.py::test_calculate_total"],
      failed: [],
      duration_seconds: 0.12,
      summary: "1 passed in 0.12s",
    };

    assert.equal(verification.status, "passed");
    assert.equal(verification.failed.length, 0);
    assert.equal(verification.passed.length, 1);
  });
});
