"""Deterministic Unified Git Diff Parser.

Parses unified diff text and extracts modified files, line numbers,
status, and changed line ranges.
"""

from dataclasses import dataclass, field
import re
from typing import List, Literal, Optional, Tuple


@dataclass
class ParsedFileDiff:
    file_path: str
    status: Literal["modified", "added", "deleted", "renamed"]
    old_path: Optional[str] = None
    lines_added: int = 0
    lines_deleted: int = 0
    changed_lines: List[int] = field(default_factory=list)  # lines in the new file that changed
    added_lines: List[int] = field(default_factory=list)
    deleted_lines: List[int] = field(default_factory=list)


def clean_file_path(raw_path: str) -> str:
    """Normalize git diff file path removing a/ or b/ prefixes."""
    path = raw_path.strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]
    return path.replace("\\", "/")


def parse_unified_diff(diff_text: str) -> Tuple[List[ParsedFileDiff], List[str]]:
    """Parse unified git diff string into structured file diffs and limitations.

    Returns:
        (file_diffs, limitations)
    """
    if not diff_text or not diff_text.strip():
        return [], ["Empty diff provided."]

    lines = diff_text.splitlines()
    file_diffs: List[ParsedFileDiff] = []
    limitations: List[str] = []

    current_file: Optional[ParsedFileDiff] = None
    old_file_path: Optional[str] = None
    new_file_path: Optional[str] = None
    is_git_header = False

    # Hunk regex: @@ -old_start,old_count +new_start,new_count @@
    hunk_regex = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")

    new_line_num = 0
    old_line_num = 0

    def finalize_current_file():
        nonlocal current_file
        if current_file:
            # Deterministic sorting of line numbers
            current_file.changed_lines = sorted(list(set(current_file.changed_lines)))
            current_file.added_lines = sorted(list(set(current_file.added_lines)))
            current_file.deleted_lines = sorted(list(set(current_file.deleted_lines)))
            file_diffs.append(current_file)
            current_file = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for git diff header: diff --git a/... b/...
        if line.startswith("diff --git "):
            finalize_current_file()
            parts = line.split()
            if len(parts) >= 4:
                old_file_path = clean_file_path(parts[2])
                new_file_path = clean_file_path(parts[3])
            i += 1
            continue

        # Check for rename/copy headers
        if line.startswith("rename from "):
            old_file_path = clean_file_path(line[len("rename from "):])
            i += 1
            continue
        if line.startswith("rename to "):
            new_file_path = clean_file_path(line[len("rename to "):])
            i += 1
            continue

        # Check for --- and +++ lines
        if line.startswith("--- "):
            raw_old = line[4:].strip()
            old_file_path = "/dev/null" if raw_old == "/dev/null" else clean_file_path(raw_old)
            i += 1
            continue

        if line.startswith("+++ "):
            raw_new = line[4:].strip()
            new_file_path = "/dev/null" if raw_new == "/dev/null" else clean_file_path(raw_new)

            finalize_current_file()

            # Determine file path and status
            status: Literal["modified", "added", "deleted", "renamed"] = "modified"
            active_path = new_file_path

            if old_file_path == "/dev/null":
                status = "added"
                active_path = new_file_path
            elif new_file_path == "/dev/null":
                status = "deleted"
                active_path = old_file_path
            elif old_file_path and new_file_path and old_file_path != new_file_path:
                status = "renamed"
                active_path = new_file_path

            if active_path and active_path != "/dev/null":
                current_file = ParsedFileDiff(
                    file_path=active_path,
                    status=status,
                    old_path=old_file_path if status == "renamed" else None,
                )

            i += 1
            continue

        # Check for hunk header
        hunk_match = hunk_regex.match(line)
        if hunk_match:
            if not current_file:
                # Malformed diff where hunk appears without valid --- / +++
                limitations.append(f"Hunk found without prior file header at line {i + 1}.")
                i += 1
                continue

            old_start = int(hunk_match.group(1))
            new_start = int(hunk_match.group(3))

            old_line_num = old_start
            new_line_num = new_start
            i += 1
            continue

        # Inside a hunk
        if current_file and (line.startswith("+") or line.startswith("-") or line.startswith(" ") or line == ""):
            if line.startswith("+"):
                current_file.lines_added += 1
                current_file.added_lines.append(new_line_num)
                current_file.changed_lines.append(new_line_num)
                new_line_num += 1
            elif line.startswith("-"):
                current_file.lines_deleted += 1
                current_file.deleted_lines.append(old_line_num)
                # Map deleted line to the current new_line_num position for symbol mapping
                current_file.changed_lines.append(max(1, new_line_num))
                old_line_num += 1
            elif line.startswith(" ") or line == "":
                old_line_num += 1
                new_line_num += 1

        i += 1

    finalize_current_file()

    # Deterministic sorting by file_path
    file_diffs.sort(key=lambda f: f.file_path)

    if not file_diffs and not limitations:
        limitations.append("No valid file diffs could be parsed from input.")

    return file_diffs, limitations
