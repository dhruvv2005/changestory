"""Main FastAPI Application Entrypoint for ChangeStory."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.routes import router as api_router
from app.storage.report_store import ReportStore

app = FastAPI(
    title="ChangeStory API",
    version="1.0.0",
    description="Deterministic Change Impact and Evidence Analysis Engine",
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router)

report_store = ReportStore()


@app.get("/health")
def health_check():
    """Health check endpoint returning service status."""
    return {
        "status": "ok",
        "service": "changestory-backend",
        "version": "1.0.0",
    }


@app.get("/report/{session_id}", response_class=HTMLResponse)
def view_local_report(session_id: str):
    """Serve local report page view.

    Provides a clean standalone HTML viewer and links to the full dashboard.
    """
    report = report_store.get_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report session '{session_id}' not found.")

    s = report.change_summary
    md_content = report_store.get_markdown(session_id) or ""
    # Safe HTML-escaped summary representation
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ChangeStory Report — {session_id}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 2rem; }}
    .container {{ max-width: 960px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 2rem; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
    h1 {{ color: #38bdf8; margin-top: 0; }}
    .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; background: #334155; color: #94a3b8; }}
    .badge-ok {{ background: #065f46; color: #34d399; }}
    .badge-risk {{ background: #854d0e; color: #fde047; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
    .card {{ background: #0f172a; padding: 1rem; border-radius: 8px; border: 1px solid #334155; }}
    .card-num {{ font-size: 1.8rem; font-weight: bold; color: #38bdf8; }}
    .card-label {{ font-size: 0.85rem; color: #94a3b8; }}
    .btn {{ display: inline-block; padding: 8px 16px; border-radius: 6px; background: #2563eb; color: white; text-decoration: none; font-weight: 500; margin-right: 8px; }}
    .btn:hover {{ background: #1d4ed8; }}
    .btn-secondary {{ background: #334155; color: #cbd5e1; }}
    pre {{ background: #0b1120; padding: 1rem; border-radius: 8px; overflow-x: auto; color: #e2e8f0; font-size: 0.9rem; border: 1px solid #1e293b; }}
  </style>
</head>
<body>
  <div class="container">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h1>ChangeStory Report</h1>
      <span class="badge">Session: {session_id}</span>
    </div>
    <p>Deterministic change impact, caller graph, and verification analysis.</p>

    <div style="margin: 1rem 0;">
      <a class="btn" href="http://localhost:3000?session_id={session_id}">Open Interactive React Dashboard</a>
      <a class="btn btn-secondary" href="/api/v1/reports/{session_id}/export.json" download>Export JSON</a>
      <a class="btn btn-secondary" href="/api/v1/reports/{session_id}/export.md" download>Export Markdown</a>
    </div>

    <div class="grid">
      <div class="card">
        <div class="card-num">{s.files_changed}</div>
        <div class="card-label">Files Changed</div>
      </div>
      <div class="card">
        <div class="card-num">{s.symbols_changed}</div>
        <div class="card-label">Symbols Changed</div>
      </div>
      <div class="card">
        <div class="card-num">{s.symbols_affected}</div>
        <div class="card-label">Direct Callers</div>
      </div>
      <div class="card">
        <div class="card-num">{s.potential_risks}</div>
        <div class="card-label">Potential Risks</div>
      </div>
      <div class="card">
        <div class="card-num">{s.test_recommendations}</div>
        <div class="card-label">Test Candidates</div>
      </div>
    </div>

    <h2>Markdown Report</h2>
    <pre>{md_content}</pre>
  </div>
</body>
</html>"""
    return html


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
