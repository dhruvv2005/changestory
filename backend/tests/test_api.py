import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import FIXTURES_DIR

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_get_scenarios():
    res = client.get("/api/v1/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 3
    ids = [s["id"] for s in scenarios]
    assert "scenario_a" in ids
    assert "scenario_b" in ids
    assert "scenario_c" in ids


def test_analyze_and_report_flow():
    diff_path = FIXTURES_DIR / "diffs" / "scenario_a.diff"
    diff_text = diff_path.read_text(encoding="utf-8")

    # 1. Analyze
    res = client.post("/api/v1/analyze", json={"diff_text": diff_text, "source_mode": "sample"})
    assert res.status_code == 200
    report = res.json()
    session_id = report["session_id"]
    assert session_id.startswith("cs_")
    assert report["change_summary"]["files_changed"] == 1

    # 2. Get Report
    res_get = client.get(f"/api/v1/reports/{session_id}")
    assert res_get.status_code == 200
    assert res_get.json()["session_id"] == session_id

    # 3. Export JSON
    res_json = client.get(f"/api/v1/reports/{session_id}/export.json")
    assert res_json.status_code == 200
    assert "attachment" in res_json.headers.get("content-disposition", "")

    # 4. Export Markdown
    res_md = client.get(f"/api/v1/reports/{session_id}/export.md")
    assert res_md.status_code == 200
    assert "# ChangeStory Analysis Report" in res_md.text

    # 5. Local HTML Report View
    res_html = client.get(f"/report/{session_id}")
    assert res_html.status_code == 200
    assert "ChangeStory Report" in res_html.text

    # 6. Controlled Verification
    res_ver = client.post(f"/api/v1/verify/{session_id}")
    assert res_ver.status_code == 200
    ver_data = res_ver.json()
    assert ver_data["status"] in ["passed", "failed"]


def test_analyze_empty_diff_returns_400():
    res = client.post("/api/v1/analyze", json={"diff_text": "", "source_mode": "sample"})
    assert res.status_code == 400


def test_report_not_found():
    res = client.get("/api/v1/reports/nonexistent_session_id")
    assert res.status_code == 404
