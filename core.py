"""Core checks and stable report formatting for EnvDoctor."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "minimum_python": "3.10",
    "minimum_free_disk_mb": 200,
    "required_env": [],
    "tools": [
        {"name": "git", "command": "git", "version_args": ["--version"]},
        {"name": "pip", "command": "pip", "version_args": ["--version"]},
    ],
}


class ConfigurationError(ValueError):
    """Raised when a configuration file is missing or malformed."""


def load_config(path: str | None) -> dict[str, Any]:
    if path is None:
        return DEFAULT_CONFIG.copy()
    config_path = Path(path).expanduser()
    try:
        raw = config_path.read_text(encoding="utf-8")
        config = json.loads(raw)
    except OSError as exc:
        raise ConfigurationError(f"Cannot read config '{config_path}': {exc.strerror or exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Malformed JSON in config '{config_path}' at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(config, dict):
        raise ConfigurationError("Configuration root must be a JSON object.")

    merged = DEFAULT_CONFIG.copy()
    merged.update(config)
    if not isinstance(merged.get("minimum_python"), str):
        raise ConfigurationError("'minimum_python' must be a version string, for example '3.10'.")
    if not isinstance(merged.get("minimum_free_disk_mb"), int) or merged["minimum_free_disk_mb"] < 0:
        raise ConfigurationError("'minimum_free_disk_mb' must be a non-negative integer.")
    if not isinstance(merged.get("required_env"), list) or not all(isinstance(x, str) and x for x in merged["required_env"]):
        raise ConfigurationError("'required_env' must be a list of non-empty environment-variable names.")
    if not isinstance(merged.get("tools"), list):
        raise ConfigurationError("'tools' must be a list.")
    for index, tool in enumerate(merged["tools"]):
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str) or not isinstance(tool.get("command"), str):
            raise ConfigurationError(f"Each tools entry must have string 'name' and 'command' fields (entry {index}).")
        args = tool.get("version_args", ["--version"])
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise ConfigurationError(f"tools entry {index}: 'version_args' must be a list of strings.")
        tool["version_args"] = args
    return merged


def _version_tuple(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.split(".") if part.isdigit())
    except (TypeError, ValueError):
        return ()


def _check(name: str, status: str, details: str) -> dict[str, str]:
    return {"name": name, "status": status, "details": details}


def inspect_environment(config: dict[str, Any], *, disk_path: str | None = None) -> dict[str, Any]:
    """Inspect configured environment properties without exposing variable values."""
    checks: list[dict[str, str]] = []
    current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    minimum = config["minimum_python"]
    py_ok = _version_tuple(current)[:2] >= _version_tuple(minimum)[:2]
    checks.append(_check("python", "ok" if py_ok else "fail", f"Python {current}; minimum required {minimum}"))

    target = Path(disk_path or Path.home())
    try:
        usage = shutil.disk_usage(target)
        free_mb = usage.free // (1024 * 1024)
        required_mb = config["minimum_free_disk_mb"]
        checks.append(_check("disk_space", "ok" if free_mb >= required_mb else "fail",
                             f"{free_mb} MiB free at {target}; minimum required {required_mb} MiB"))
    except OSError as exc:
        checks.append(_check("disk_space", "fail", f"Cannot inspect {target}: {exc}"))

    for variable in sorted(config["required_env"]):
        present = bool(os.environ.get(variable, "").strip())
        checks.append(_check(f"env:{variable}", "ok" if present else "fail",
                             "variable is set" if present else "required variable is missing or empty"))

    for tool in sorted(config["tools"], key=lambda item: (item["name"].casefold(), item["command"])):
        name, command = tool["name"], tool["command"]
        executable = shutil.which(command)
        if not executable:
            checks.append(_check(f"tool:{name}", "fail", f"Command '{command}' was not found on PATH"))
            continue
        try:
            completed = subprocess.run(
                [executable, *tool.get("version_args", ["--version"])],
                capture_output=True, text=True, timeout=5, check=False,
            )
            output = (completed.stdout or completed.stderr).strip().splitlines()
            first_line = output[0][:200] if output else "version output unavailable"
            status = "ok" if completed.returncode == 0 else "fail"
            checks.append(_check(f"tool:{name}", status, f"{first_line} (exit {completed.returncode})"))
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks.append(_check(f"tool:{name}", "fail", f"Could not run '{command}': {exc}"))

    checks.sort(key=lambda item: item["name"])
    failed = sum(item["status"] == "fail" for item in checks)
    return {
        "schema_version": 1,
        "tool": "envdoctor",
        "status": "healthy" if failed == 0 else "unhealthy",
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [f"EnvDoctor environment report: {report['status'].upper()}",
             f"Checks: {summary['passed']} passed, {summary['failed']} failed, {summary['total']} total", ""]
    for item in report["checks"]:
        lines.append(f"[{item['status'].upper():4}] {item['name']}: {item['details']}")
    return "\n".join(lines) + "\n"


def render_json(report: dict[str, Any]) -> str:
    """Stable JSON: sorted keys, fixed indentation, no timestamps."""
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
