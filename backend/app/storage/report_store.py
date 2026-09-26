"""Local Filesystem Report and Session Storage.

Saves and retrieves ChangeStory reports in JSON and Markdown formats.
No database required.
"""

import json
from pathlib import Path
from typing import Optional
from app.config import REPORTS_DIR
from app.models.schemas import ChangeStoryReport


class ReportStore:
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or REPORTS_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _json_path(self, session_id: str) -> Path:
        # Sanitize session_id to prevent path traversal
        clean_id = Path(session_id).name
        return self.storage_dir / f"{clean_id}.json"

    def _md_path(self, session_id: str) -> Path:
        clean_id = Path(session_id).name
        return self.storage_dir / f"{clean_id}.md"

    def save_report(self, report: ChangeStoryReport) -> Path:
        """Save report as JSON and Markdown."""
        json_file = self._json_path(report.session_id)
        md_file = self._md_path(report.session_id)

        # 1. Write JSON
        json_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        # 2. Write Markdown
        md_content = self.render_markdown(report)
        md_file.write_text(md_content, encoding="utf-8")

        return json_file

    def get_report(self, session_id: str) -> Optional[ChangeStoryReport]:
        """Load report by session ID."""
        json_file = self._json_path(session_id)
        if not json_file.exists():
            return None
        data = json.loads(json_file.read_text(encoding="utf-8"))
        return ChangeStoryReport.model_validate(data)

    def get_markdown(self, session_id: str) -> Optional[str]:
        """Load report markdown text."""
        md_file = self._md_path(session_id)
        if md_file.exists():
            return md_file.read_text(encoding="utf-8")
        report = self.get_report(session_id)
        if report:
            md_content = self.render_markdown(report)
            md_file.write_text(md_content, encoding="utf-8")
            return md_content
        return None

    def render_markdown(self, report: ChangeStoryReport) -> str:
        """Render complete structured Markdown document for a report."""
        s = report.change_summary
        lines = [
            f"# ChangeStory Analysis Report — Session `{report.session_id}`",
            "",
            f"- **Generated At**: {report.timestamp or 'N/A'}",
            f"- **Schema Version**: {report.schema_version}",
            "",
            "## 1. Change Summary",
            "",
            "| Metric | Count |",
            "| --- | --- |",
            f"| Files Changed | {s.files_changed} |",
            f"| Lines Added | +{s.lines_added} |",
            f"| Lines Deleted | -{s.lines_deleted} |",
            f"| Symbols Changed | {s.symbols_changed} |",
            f"| Symbols Affected | {s.symbols_affected} |",
            f"| Potential Risks | {s.potential_risks} |",
            f"| Test Recommendations | {s.test_recommendations} |",
            "",
            "## 2. Changed Files",
            "",
        ]

        if not report.files:
            lines.append("_No file changes detected._\n")
        else:
            for f in report.files:
                syms = ", ".join(f.related_symbols) if f.related_symbols else "None"
                lines.append(f"### `{f.file_path}` ({f.status.upper()})")
                lines.append(f"- **Lines Added**: +{f.lines_added} | **Lines Deleted**: -{f.lines_deleted}")
                lines.append(f"- **Changed Lines**: `{f.changed_lines}`")
                lines.append(f"- **Related Symbols**: {syms}")
                lines.append("")

        lines.extend([
            "## 3. Detected Facts (Changed Symbols)",
            "",
        ])
        if not report.changed_symbols:
            lines.append("_No changed Python symbols mapped._\n")
        else:
            for sym in report.changed_symbols:
                lines.append(f"- **`{sym.qualified_name}`** (`{sym.type}` in `{sym.file_path}:{sym.start_line}-{sym.end_line}`)")
            lines.append("")

        lines.extend([
            "## 4. Statically Affected Symbols & Direct Callers",
            "",
        ])
        if not report.affected_symbols:
            lines.append("_No direct callers statically detected in this repository._\n")
        else:
            for aff in report.affected_symbols:
                lines.append(f"- **`{aff.qualified_name}`** (`{aff.type}` in `{aff.file_path}:{aff.start_line}`)")
            lines.append("")

        lines.extend([
            "## 5. Relationships",
            "",
        ])
        if not report.relationships:
            lines.append("_No direct caller relationships detected._\n")
        else:
            for rel in report.relationships:
                snip = f" (`{rel.evidence.snippet}`)" if rel.evidence else ""
                lines.append(f"- `{rel.source}` **{rel.relationship}** `{rel.target}`{snip}")
            lines.append("")

        lines.extend([
            "## 6. Potential Risks (Deterministic)",
            "",
        ])
        if not report.risks:
            lines.append("_No potential risks identified based on deterministic rules._\n")
        else:
            for risk in report.risks:
                lines.append(f"### [{risk.severity.upper()}] {risk.title}")
                lines.append(f"{risk.description}")
                if risk.related_symbols:
                    lines.append(f"- **Related Symbols**: {', '.join(risk.related_symbols)}")
                lines.append("")

        lines.extend([
            "## 7. Recommended Targeted Tests",
            "",
        ])
        if not report.test_recommendations:
            lines.append("_No targeted test candidates identified._\n")
        else:
            for rec in report.test_recommendations:
                lines.append(f"### [{rec.confidence.upper()}] {rec.title}")
                lines.append(f"- **Reason**: {rec.reason}")
                lines.append(f"- **Symbols**: {', '.join(rec.related_symbols)}")
                lines.append("")

        lines.extend([
            "## 8. Controlled Verification Results",
            "",
        ])
        if not report.verification:
            lines.append("_No controlled verification has been run yet._\n")
        else:
            v = report.verification
            lines.append(f"- **Status**: `{v.status.upper()}`")
            lines.append(f"- **Duration**: {v.duration_seconds}s")
            lines.append(f"- **Summary**: {v.summary}")
            if v.passed:
                lines.append(f"- **Passed ({len(v.passed)})**:\n  - " + "\n  - ".join(v.passed))
            if v.failed:
                lines.append(f"- **Failed ({len(v.failed)})**:\n  - " + "\n  - ".join(v.failed))
            lines.append("")

        lines.extend([
            "## 9. Verification Checklist",
            "",
            "- [ ] Review diff line ranges and confirmed symbol mapping",
            "- [ ] Verify all caller call-sites identified in evidence",
            "- [ ] Inspect and mitigate potential shared-impact risks",
            "- [ ] Execute recommended targeted tests",
            "- [ ] Check controlled verification execution output",
            "",
            "## 10. Explicit Limitations",
            "",
        ])
        for lim in report.limitations:
            lines.append(f"- {lim}")
        lines.append("")

        return "\n".join(lines)
