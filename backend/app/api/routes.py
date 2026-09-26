"""FastAPI API Routes for ChangeStory.

Endpoints:
- POST /api/v1/analyze
- GET  /api/v1/reports/{session_id}
- GET  /api/v1/reports/{session_id}/export.json
- GET  /api/v1/reports/{session_id}/export.md
- POST /api/v1/verify/{session_id}
- GET  /api/v1/scenarios
"""

from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse

from app.analysis.engine import ChangeStoryEngine
from app.config import BASE_DIR, FIXTURES_DIR, SAMPLE_PROJECT_DIR
from app.models.schemas import (
    AnalyzeRequest,
    ChangeStoryReport,
    VerificationResult,
    VerifyRequest,
)
from app.services.test_runner import ControlledTestRunner, SecurityError
from app.storage.report_store import ReportStore

router = APIRouter(prefix="/api/v1", tags=["changestory"])
report_store = ReportStore()
test_runner = ControlledTestRunner(SAMPLE_PROJECT_DIR)


@router.post("/analyze", response_model=ChangeStoryReport)
def analyze_diff(req: AnalyzeRequest) -> ChangeStoryReport:
    """Analyze unified diff and return ChangeStory report."""
    if not req.diff_text or not req.diff_text.strip():
        raise HTTPException(status_code=400, detail="Diff text cannot be empty.")

    # Select target repository: sample or local
    if req.source_mode == "sample":
        target_dir = SAMPLE_PROJECT_DIR
    elif req.source_mode == "local" and req.repository_path:
        local_path = Path(req.repository_path).resolve()
        if not local_path.exists() or not local_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Local repository path does not exist: {req.repository_path}")
        target_dir = local_path
    elif req.source_mode == "local":
        # No explicit path: scan from project root so suffix/basename matching
        # works for any custom diff that references Python files by partial path.
        target_dir = BASE_DIR
    else:
        target_dir = SAMPLE_PROJECT_DIR

    engine = ChangeStoryEngine(target_dir)
    report = engine.analyze(req.diff_text)

    # Persist report
    report_store.save_report(report)
    return report


@router.get("/reports/{session_id}", response_model=ChangeStoryReport)
def get_report(session_id: str) -> ChangeStoryReport:
    """Fetch stored report by session ID."""
    report = report_store.get_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report session '{session_id}' not found.")
    return report


@router.get("/reports/{session_id}/export.json")
def export_json(session_id: str):
    """Export report as downloadable JSON."""
    report = report_store.get_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report session '{session_id}' not found.")
    return Response(
        content=report.model_dump_json(indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="changestory_{session_id}.json"'},
    )


@router.get("/reports/{session_id}/export.md")
def export_markdown(session_id: str):
    """Export report as downloadable Markdown."""
    md_content = report_store.get_markdown(session_id)
    if not md_content:
        raise HTTPException(status_code=404, detail=f"Report session '{session_id}' not found.")
    return PlainTextResponse(
        content=md_content,
        headers={"Content-Disposition": f'attachment; filename="changestory_{session_id}.md"'},
    )


@router.post("/verify/{session_id}", response_model=VerificationResult)
def verify_session(session_id: str) -> VerificationResult:
    """Run controlled verification tests against sample project and update report."""
    report = report_store.get_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report session '{session_id}' not found.")

    try:
        verification = test_runner.run_tests()
    except SecurityError as se:
        raise HTTPException(status_code=403, detail=str(se))

    # Update and re-save report
    report.verification = verification
    report_store.save_report(report)
    return verification


@router.get("/scenarios")
def get_scenarios() -> List[Dict[str, Any]]:
    """Return bundled deterministic demo scenarios."""
    diff_dir = FIXTURES_DIR / "diffs"
    scenarios = [
        {
            "id": "scenario_a",
            "name": "Scenario A — Changed Calculation Function",
            "description": "Modifies calculate_total() in calculator.py. Detects caller in order_service.py and recommends targeted tests.",
            "diff_file": "scenario_a.diff",
        },
        {
            "id": "scenario_b",
            "name": "Scenario B — New API Handler",
            "description": "Adds discount_endpoint() in api_routes.py. Flags API contract change risk and recommends route test.",
            "diff_file": "scenario_b.diff",
        },
        {
            "id": "scenario_c",
            "name": "Scenario C — Changed Shared Utility",
            "description": "Modifies format_currency() in utils.py. Detects multiple callers across modules and raises shared-impact risk.",
            "diff_file": "scenario_c.diff",
        },
    ]

    result = []
    for sc in scenarios:
        path = diff_dir / sc["diff_file"]
        diff_text = path.read_text(encoding="utf-8") if path.exists() else ""
        result.append({
            **sc,
            "diff_text": diff_text,
        })
    return result
