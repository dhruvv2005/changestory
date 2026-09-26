"""ChangeStory CLI tool.

Collects local git diff or diff file, sends it to the ChangeStory API,
displays a concise terminal summary, and opens the local report in the browser.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Optional
import urllib.error
import urllib.parse
import urllib.request
import webbrowser


def get_git_diff(repo_path: Path) -> str:
    """Collect git diff from the local repository safely without shell=True."""
    # Check if git is installed and directory is git repo
    try:
        # Check staged + unstaged changes: git diff HEAD
        proc = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout

        # Fallback to unstaged: git diff
        proc_unstaged = subprocess.run(
            ["git", "diff"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )
        if proc_unstaged.returncode == 0 and proc_unstaged.stdout.strip():
            return proc_unstaged.stdout

        # Check last commit diff: git show
        proc_show = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )
        if proc_show.returncode == 0 and proc_show.stdout.strip():
            return proc_show.stdout

        return ""
    except Exception as e:
        print(f"Warning: Could not extract git diff: {e}", file=sys.stderr)
        return ""


def analyze_diff(
    diff_text: str,
    api_url: str = "http://127.0.0.1:8000",
    repo_path: Optional[str] = None,
    source_mode: str = "sample",
) -> dict:
    """Send diff to ChangeStory FastAPI endpoint."""
    url = f"{api_url.rstrip('/')}/api/v1/analyze"
    payload = {
        "diff_text": diff_text,
        "repository_path": repo_path,
        "source_mode": source_mode,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                body = response.read().decode("utf-8")
                return json.loads(body)
            else:
                raise RuntimeError(f"API returned status {response.status}")
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Could not connect to ChangeStory backend at {api_url}.\n"
            "Please ensure the backend is running (`python -m uvicorn app.main:app` in backend/)."
        ) from e


def cli_main():
    parser = argparse.ArgumentParser(
        prog="changestory",
        description="ChangeStory: Deterministic code change impact, caller graph, and evidence analyzer.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze git changes and generate report.")
    analyze_parser.add_argument("--repo", type=str, default=".", help="Path to local repository (default: current directory)")
    analyze_parser.add_argument("--diff-file", type=str, default=None, help="Path to a unified diff file instead of git")
    analyze_parser.add_argument("--api-url", type=str, default="http://127.0.0.1:8000", help="ChangeStory API URL (default: http://127.0.0.1:8000)")
    analyze_parser.add_argument("--frontend-url", type=str, default="http://localhost:3000", help="ChangeStory Frontend URL (default: http://localhost:3000)")
    analyze_parser.add_argument("--no-browser", action="store_true", help="Do not automatically open report in web browser")
    analyze_parser.add_argument("--sample-mode", action="store_true", help="Analyze against bundled sample project")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "analyze":
        diff_content = ""
        repo_dir = Path(args.repo).resolve()

        if args.diff_file:
            diff_path = Path(args.diff_file).resolve()
            if not diff_path.exists():
                print(f"Error: Diff file not found: {args.diff_file}", file=sys.stderr)
                sys.exit(1)
            diff_content = diff_path.read_text(encoding="utf-8")
        else:
            diff_content = get_git_diff(repo_dir)

        if not diff_content.strip():
            print("Error: No diff changes detected to analyze.", file=sys.stderr)
            print("Tip: Provide a diff file via --diff-file <path> or make git changes in repository.", file=sys.stderr)
            sys.exit(1)

        source_mode = "sample" if args.sample_mode else ("local" if not args.diff_file else "sample")

        print("Analyzing changes with ChangeStory engine...")
        try:
            report = analyze_diff(
                diff_text=diff_content,
                api_url=args.api_url,
                repo_path=str(repo_dir) if source_mode == "local" else None,
                source_mode=source_mode,
            )
        except Exception as e:
            print(f"\nAnalysis Failed: {e}", file=sys.stderr)
            sys.exit(1)

        s = report.get("change_summary", {})
        session_id = report.get("session_id", "latest")

        # Safe console output for Windows cp1252 & UTF-8
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            ok_sym = "[OK]"
            warn_sym = "[!]"
        except Exception:
            ok_sym = "[OK]"
            warn_sym = "[!]"

        print("\nChangeStory Analysis")
        print("--------------------")
        print(f"{ok_sym} {s.get('files_changed', 0)} files changed")
        print(f"{ok_sym} {s.get('symbols_changed', 0)} symbols changed")
        print(f"{ok_sym} {s.get('symbols_affected', 0)} affected symbols (direct callers)")
        risks_count = s.get("potential_risks", 0)
        risk_icon = warn_sym if risks_count > 0 else ok_sym
        print(f"{risk_icon} {risks_count} potential risks")
        print(f"{ok_sym} {s.get('test_recommendations', 0)} test recommendations")

        # Report URLs
        backend_report_url = f"{args.api_url.rstrip('/')}/report/{session_id}"
        frontend_report_url = f"{args.frontend_url.rstrip('/')}?session_id={session_id}"

        print("\nReport:")
        print(f"  Interactive Dashboard: {frontend_report_url}")
        print(f"  Local Report View:     {backend_report_url}")
        print(f"  Export JSON:           {args.api_url.rstrip('/')}/api/v1/reports/{session_id}/export.json")
        print(f"  Export Markdown:       {args.api_url.rstrip('/')}/api/v1/reports/{session_id}/export.md")

        if not args.no_browser:
            print("\nOpening report in browser...")
            try:
                # Prefer frontend URL, fallback to backend view
                webbrowser.open(frontend_report_url)
            except Exception:
                pass


if __name__ == "__main__":
    cli_main()
