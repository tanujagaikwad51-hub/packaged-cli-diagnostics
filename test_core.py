import json
import os
from pathlib import Path

from envdoctor.core import ConfigurationError, inspect_environment, load_config, render_json


def config(**overrides):
    result = {
        "minimum_python": "3.0",
        "minimum_free_disk_mb": 0,
        "required_env": [],
        "tools": [],
    }
    result.update(overrides)
    return result


def test_success_report_is_healthy_and_json_is_deterministic(tmp_path):
    report = inspect_environment(config(), disk_path=str(tmp_path))
    assert report["status"] == "healthy"
    assert report["summary"]["failed"] == 0
    assert render_json(report) == render_json(report)
    assert json.loads(render_json(report))["schema_version"] == 1


def test_missing_dependency_is_reported_as_failure(tmp_path):
    report = inspect_environment(config(tools=[{
        "name": "imaginary", "command": "envdoctor-command-that-does-not-exist-92731", "version_args": ["--version"]
    }]), disk_path=str(tmp_path))
    failed = [item for item in report["checks"] if item["name"] == "tool:imaginary"]
    assert failed and failed[0]["status"] == "fail"
    assert report["status"] == "unhealthy"


def test_missing_required_environment_variable_fails(monkeypatch, tmp_path):
    monkeypatch.delenv("ENVDOCTOR_TEST_REQUIRED", raising=False)
    report = inspect_environment(config(required_env=["ENVDOCTOR_TEST_REQUIRED"]), disk_path=str(tmp_path))
    assert next(c for c in report["checks"] if c["name"] == "env:ENVDOCTOR_TEST_REQUIRED")["status"] == "fail"


def test_malformed_configuration_path(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{ "tools": [ }', encoding="utf-8")
    try:
        load_config(str(path))
    except ConfigurationError as exc:
        assert "Malformed JSON" in str(exc)
    else:
        raise AssertionError("Expected ConfigurationError")


def test_missing_configuration_path(tmp_path):
    try:
        load_config(str(tmp_path / "missing.json"))
    except ConfigurationError as exc:
        assert "Cannot read config" in str(exc)
    else:
        raise AssertionError("Expected ConfigurationError")
