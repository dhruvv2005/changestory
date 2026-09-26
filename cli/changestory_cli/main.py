"""ChangeStory CLI tool.

Collects local git diff or diff file, sends it to the ChangeStory API,
displays a concise terminal summary, and opens the local report in the browser.
"""

import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Optional
import urllib.error
import urllib.parse
import urllib.request
import webbrowser


CONFIG_DIR = ".changestory"
CONFIG_FILE = "config.json"
IGNORED_UNTRACKED_PARTS = {".git", ".changestory", "venv", ".venv", "node_modules", "__pycache__"}
SERVICE_START_TIMEOUT_SECONDS = 25


def git_output(repo_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=str(repo_path), capture_output=True, text=True,
        shell=False, timeout=15,
    )


def discover_project_root(start: Path) -> tuple[Path, bool]:
    """Resolve configured root or Git root from a directory inside a project."""
    start = start.resolve()
    if start.is_file():
        start = start.parent
    for candidate in (start, *start.parents):
        config = candidate / CONFIG_DIR / CONFIG_FILE
        if config.is_file():
            try:
                data = json.loads(config.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("Configuration must be a JSON object")
                git_result = git_output(candidate, "rev-parse", "--show-toplevel")
                return candidate.resolve(), git_result.returncode == 0
            except (OSError, ValueError, TypeError, AttributeError):
                raise ValueError(f"Invalid ChangeStory config: {config}")
        try:
            result = git_output(candidate, "rev-parse", "--show-toplevel")
            if result.returncode == 0:
                return Path(result.stdout.strip()).resolve(), True
        except (OSError, subprocess.SubprocessError):
            break
    return start, False


def detect_languages(root: Path) -> list[str]:
    markers = {
        "Python": ("pyproject.toml", "setup.py", "requirements.txt"),
        "JavaScript/TypeScript": ("package.json", "tsconfig.json"),
        "Java": ("pom.xml", "build.gradle", "build.gradle.kts"),
    }
    languages = [language for language, files in markers.items() if any((root / name).exists() for name in files)]
    if "Python" not in languages:
        excluded = {".git", ".changestory", ".venv", "venv", "node_modules", "__pycache__"}
        if any(
            not any(part.lower() in excluded for part in path.relative_to(root).parts)
            for path in root.rglob("*.py")
        ):
            languages.append("Python")
    return languages


def initialize_project(start: Path) -> Path:
    root, _ = discover_project_root(start)
    config_dir = root / CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / CONFIG_FILE
    if config_path.exists():
        try:
            existing = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                raise ValueError("Configuration must be a JSON object")
        except (OSError, ValueError, TypeError, AttributeError) as e:
            raise ValueError(f"Invalid ChangeStory config: {config_path}") from e
    try:
        git_root_result = git_output(root, "rev-parse", "--show-toplevel")
        git_root = str(Path(git_root_result.stdout.strip()).resolve()) if git_root_result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        git_root = None
    config = {
        "version": 1,
        "project_root": str(root),
        "git_root": git_root,
        "languages": detect_languages(root),
        "analysis_mode": "local",
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return root


def _loopback_http_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.hostname != "localhost":
        return url
    port = f":{parsed.port}" if parsed.port else ""
    return urllib.parse.urlunsplit((parsed.scheme, f"127.0.0.1{port}", parsed.path, parsed.query, parsed.fragment))


def _local_service_ready(url: str, expected_service: Optional[str] = None, timeout: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(_loopback_http_url(url), timeout=timeout) as response:
            if response.status != 200:
                return False
            if expected_service is None:
                return True
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("service") == expected_service
    except (OSError, ValueError, urllib.error.URLError):
        return False


def _start_hidden_process(command: list[str], cwd: Path, env: Optional[dict] = None) -> subprocess.Popen:
    options = {
        "cwd": str(cwd),
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "shell": False,
    }
    if env is not None:
        options["env"] = env
    if sys.platform == "win32":
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    else:
        options["start_new_session"] = True
    return subprocess.Popen(command, **options)


def _loopback_url_parts(url: str) -> Optional[tuple[str, int]]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        return None
    try:
        return parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError:
        return None


def ensure_local_backend(api_url: str) -> bool:
    """Use the local API, starting the bundled backend when available."""
    health_url = f"{api_url.rstrip('/')}/health"
    if _local_service_ready(health_url, "changestory-backend"):
        return True

    address = _loopback_url_parts(api_url)
    project_source = Path(__file__).resolve().parents[2]
    backend_dir = project_source / "backend"
    if not address or not (backend_dir / "app" / "main.py").is_file():
        return False

    host, port = address
    launch_host = "127.0.0.1" if host == "localhost" else host
    try:
        _start_hidden_process(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", launch_host, "--port", str(port)],
            backend_dir,
        )
    except OSError:
        return False

    deadline = time.monotonic() + SERVICE_START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if _local_service_ready(health_url, "changestory-backend"):
            return True
        time.sleep(0.25)
    return False


def ensure_local_dashboard(frontend_url: str, api_url: str) -> bool:
    """Start the bundled Next dashboard if it is not already reachable."""
    if _local_service_ready(frontend_url, timeout=8):
        return True

    address = _loopback_url_parts(frontend_url)
    project_source = Path(__file__).resolve().parents[2]
    frontend_dir = project_source / "frontend"
    next_cli = frontend_dir / "node_modules" / "next" / "dist" / "bin" / "next"
    node = shutil.which("node")
    if not address or not next_cli.is_file() or not node:
        return False

    host, port = address
    launch_host = "127.0.0.1" if host == "localhost" else host
    frontend_env = os.environ.copy()
    frontend_env["NEXT_PUBLIC_API_URL"] = _loopback_http_url(api_url.rstrip("/"))
    try:
        _start_hidden_process(
            [node, str(next_cli), "dev", "--hostname", launch_host, "--port", str(port)],
            frontend_dir,
            env=frontend_env,
        )
    except OSError:
        return False

    deadline = time.monotonic() + SERVICE_START_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if _local_service_ready(frontend_url, timeout=4):
            return True
        time.sleep(0.25)
    return False


def get_git_diff(repo_path: Path) -> str:
    """Collect git diff from the local repository safely without shell=True."""
    # Check if git is installed and directory is git repo
    try:
        # Compare tracked changes to HEAD (staged and unstaged); support repositories
        # without an initial commit by falling back to the index and work tree.
        tracked = git_output(repo_path, "diff", "--find-renames", "HEAD", "--")
        if tracked.returncode != 0:
            unstaged = git_output(repo_path, "diff", "--find-renames", "--")
            staged = git_output(repo_path, "diff", "--cached", "--find-renames", "--")
            tracked_text = (staged.stdout if staged.returncode == 0 else "") + (unstaged.stdout if unstaged.returncode == 0 else "")
        else:
            tracked_text = tracked.stdout
        diff_parts = [tracked_text] if tracked_text.strip() else []
        untracked = git_output(repo_path, "ls-files", "--others", "--exclude-standard", "--")
        if untracked.returncode == 0:
            for relative_name in untracked.stdout.splitlines():
                rel = Path(relative_name)
                if any(part.lower() in IGNORED_UNTRACKED_PARTS for part in rel.parts):
                    continue
                if rel.suffix.lower() != ".py":
                    continue
                file_path = (repo_path / rel).resolve()
                if repo_path.resolve() not in file_path.parents or not file_path.is_file():
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    continue
                diff_parts.extend(difflib.unified_diff(
                    [], content.splitlines(keepends=True), fromfile="/dev/null",
                    tofile=f"b/{rel.as_posix()}", lineterm="\n",
                ))
        return "".join(diff_parts)
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
        with urllib.request.urlopen(req, timeout=120) as response:
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

    init_parser = subparsers.add_parser("init", help="Initialize ChangeStory in the current project.")
    init_parser.add_argument("--repo", type=str, default=".", help="Project directory (default: current directory)")

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

    if args.command == "init":
        try:
            root = initialize_project(Path(args.repo))
        except (OSError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        git_result = git_output(root, "rev-parse", "--show-toplevel")
        print(f"ChangeStory initialized in {root}")
        print(f"Git repository: {'detected' if git_result.returncode == 0 else 'not detected'}")
        languages = detect_languages(root)
        print(f"Detected languages: {', '.join(languages) if languages else 'unknown'}")
        return

    if args.command == "analyze":
        diff_content = ""
        try:
            repo_dir, is_git_repo = discover_project_root(Path(args.repo))
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if args.diff_file:
            diff_path = Path(args.diff_file).resolve()
            if not diff_path.exists():
                print(f"Error: Diff file not found: {args.diff_file}", file=sys.stderr)
                sys.exit(1)
            diff_content = diff_path.read_text(encoding="utf-8")
        else:
            if not is_git_repo:
                print("Error: No Git repository found. Run `changestory init` in a Git project or use --diff-file.", file=sys.stderr)
                sys.exit(1)
            diff_content = get_git_diff(repo_dir)

        if not diff_content.strip():
            print("Error: No diff changes detected to analyze.", file=sys.stderr)
            print("Tip: Provide a diff file via --diff-file <path> or make git changes in repository.", file=sys.stderr)
            sys.exit(1)

        source_mode = "sample" if args.sample_mode else ("diff_only" if args.diff_file else "local")

        if not ensure_local_backend(args.api_url):
            print(
                "Analysis Failed: The local ChangeStory backend could not be reached or started. "
                "Install the ChangeStory project dependencies and retry.",
                file=sys.stderr,
            )
            sys.exit(1)

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
        project = report.get("project") or {}
        print(f"Project: {project.get('name') or repo_dir.name}")
        print(f"{ok_sym} {s.get('files_changed', 0)} files changed")
        print(f"{ok_sym} {s.get('symbols_changed', 0)} symbols changed")
        print(f"{ok_sym} {s.get('symbols_affected', 0)} affected symbols (direct callers)")
        risks_count = s.get("potential_risks", 0)
        risk_icon = warn_sym if risks_count > 0 else ok_sym
        print(f"{risk_icon} {risks_count} potential risks")
        print(f"{ok_sym} {s.get('test_recommendations', 0)} test recommendations")

        # Report URLs
        backend_report_url = f"{args.api_url.rstrip('/')}/report/{session_id}"
        frontend_report_url = f"{_loopback_http_url(args.frontend_url.rstrip('/'))}?session_id={session_id}"

        print("\nReport:")
        print(f"  Interactive Dashboard: {frontend_report_url}")
        print(f"  Local Report View:     {backend_report_url}")
        print(f"  Export JSON:           {args.api_url.rstrip('/')}/api/v1/reports/{session_id}/export.json")
        print(f"  Export Markdown:       {args.api_url.rstrip('/')}/api/v1/reports/{session_id}/export.md")

        if not args.no_browser:
            print("\nOpening report in browser...")
            try:
                if ensure_local_dashboard(args.frontend_url, args.api_url):
                    webbrowser.open(frontend_report_url)
                else:
                    print("Dashboard unavailable; opening the local report view instead.")
                    webbrowser.open(backend_report_url)
            except Exception:
                webbrowser.open(backend_report_url)


if __name__ == "__main__":
    cli_main()
