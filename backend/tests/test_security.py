import pytest
from pathlib import Path
from app.config import SAMPLE_PROJECT_DIR
from app.services.test_runner import ControlledTestRunner, SecurityError


def test_controlled_test_runner_success():
    runner = ControlledTestRunner(SAMPLE_PROJECT_DIR)
    result = runner.run_tests()
    assert result.status in ["passed", "failed"]
    assert result.duration_seconds >= 0.0
    assert len(result.passed) >= 1


def test_security_blocks_custom_command():
    runner = ControlledTestRunner(SAMPLE_PROJECT_DIR)
    with pytest.raises(SecurityError) as exc:
        runner.run_tests(custom_command=["rm", "-rf", "/"])
    assert "strictly forbidden" in str(exc.value)


def test_security_blocks_unauthorized_repository():
    runner = ControlledTestRunner(SAMPLE_PROJECT_DIR)
    unauthorized_path = Path("/tmp/malicious_repo")
    with pytest.raises(SecurityError) as exc:
        runner.run_tests(target_repo=unauthorized_path)
    assert "blocked" in str(exc.value)
