"""Controlled Predefined Test Runner with Strict Security Controls.

Enforces:
- Execution strictly against the bundled controlled sample-project only.
- Fixed predefined command list: sys.executable -m pytest.
- Absolute rejection of shell=True, user-supplied commands, or external repos.
- Safe parsing of test results into passed/failed/error.
"""

import os
from pathlib import Path
import subprocess
import sys
import time
from typing import List, Optional
from app.config import SAMPLE_PROJECT_DIR
from app.models.schemas import VerificationResult


class SecurityError(Exception):
    """Raised when an unauthorized or potentially unsafe execution is attempted."""
    pass


class ControlledTestRunner:
    def __init__(self, allowed_project_dir: Optional[Path] = None):
        self.project_dir = allowed_project_dir or SAMPLE_PROJECT_DIR

    def run_tests(
        self,
        custom_command: Optional[List[str]] = None,
        target_repo: Optional[Path] = None,
    ) -> VerificationResult:
        """Run controlled tests. Rejects any attempt to override command or target."""
        # 1. Security enforcement: No custom commands allowed
        if custom_command is not None:
            raise SecurityError("Custom test commands are strictly forbidden for security reasons.")

        # 2. Security enforcement: No arbitrary target repositories allowed
        if target_repo is not None and target_repo.resolve() != self.project_dir.resolve():
            raise SecurityError("Execution against unapproved external repositories is blocked.")

        if not self.project_dir.exists():
            return VerificationResult(
                status="error",
                passed=[],
                failed=[],
                duration_seconds=0.0,
                summary=f"Sample project directory does not exist: {self.project_dir}",
            )

        # 3. Fixed predefined command list (NO shell=True)
        # Using python executable in current venv
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-v",
            "--tb=short",
            "tests",
        ]

        # Prepare clean environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_dir.resolve())
        # Disable writing bytecode during test verification
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        start_time = time.perf_counter()
        try:
            # shell=False is strictly enforced
            result = subprocess.run(
                cmd,
                cwd=str(self.project_dir.resolve()),
                env=env,
                capture_output=True,
                text=True,
                shell=False,
                timeout=30,  # 30-second timeout guard
            )
            duration = round(time.perf_counter() - start_time, 3)

            output = result.stdout + "\n" + result.stderr
            passed_tests: List[str] = []
            failed_tests: List[str] = []

            for line in output.splitlines():
                line_str = line.strip()
                if " PASSED" in line_str:
                    test_id = line_str.split()[0]
                    passed_tests.append(test_id)
                elif " FAILED" in line_str:
                    test_id = line_str.split()[0]
                    failed_tests.append(test_id)

            if result.returncode == 0:
                status = "passed"
                summary = f"{len(passed_tests)} tests passed in {duration}s."
            elif failed_tests:
                status = "failed"
                summary = f"{len(failed_tests)} failed, {len(passed_tests)} passed in {duration}s."
            else:
                status = "error"
                summary = f"Pytest exited with code {result.returncode}. Output:\n{output[:300]}"

            return VerificationResult(
                status=status,
                passed=passed_tests,
                failed=failed_tests,
                duration_seconds=duration,
                summary=summary,
            )

        except subprocess.TimeoutExpired:
            return VerificationResult(
                status="error",
                passed=[],
                failed=[],
                duration_seconds=30.0,
                summary="Controlled test execution timed out after 30 seconds.",
            )
        except Exception as e:
            return VerificationResult(
                status="error",
                passed=[],
                failed=[],
                duration_seconds=0.0,
                summary=f"Controlled test execution failed: {str(e)}",
            )
