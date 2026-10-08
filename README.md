# EnvDoctor CLI — Packaged CLI Diagnostics Tool

EnvDoctor is a small, dependency-free Python CLI that checks whether a developer environment meets configurable requirements. It creates stable human-readable or JSON reports and returns automation-friendly exit codes.

## Features

- Checks the running Python version against a configured minimum.
- Checks free disk space on the selected path (home directory by default).
- Checks required environment variables without printing their values.
- Checks configured developer commands and captures their version output.
- Reports missing commands and malformed/unreadable configuration with useful messages.
- Stable JSON key ordering, sorted checks, no report timestamps, and consistent exit codes.
- Python 3.10+, installable package, `envdoctor` console entry point, and automated tests.

## Install in an isolated virtual environment

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

## Usage

```bash
envdoctor
envdoctor --json
envdoctor --config samples/config.json
envdoctor --config samples/config.json --json --output report.json
envdoctor --disk-path . --json
```

If running before installation, use `python -m envdoctor.cli --json` after setting `PYTHONPATH=src` (PowerShell: `$env:PYTHONPATH='src'`).

## Configuration

Configuration is optional JSON. Unknown keys are ignored; provided keys override defaults.

```json
{
  "minimum_python": "3.10",
  "minimum_free_disk_mb": 500,
  "required_env": ["PATH", "GITHUB_TOKEN"],
  "tools": [
    {"name": "git", "command": "git", "version_args": ["--version"]},
    {"name": "node", "command": "node", "version_args": ["--version"]}
  ]
}
```

For security, EnvDoctor reports only whether a required environment variable is present; it never prints the variable's value. Only configure variables whose presence is actually required. `version_args` can be customized for tools with a different version command. Tool checks have a five-second timeout.

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | All checks passed |
| `1` | One or more environment checks failed |
| `2` | Invalid/missing configuration, output write error, or unexpected runtime error |

## Report format

JSON includes `schema_version`, `tool`, overall `status`, a `summary` with counts, and sorted `checks` entries (`name`, `status`, `details`). Example output is in `samples/report.json`. Machine-dependent values in a live report (such as free disk space and installed tool versions) naturally reflect the machine being inspected; for the same observed inputs, formatting and ordering are stable.

## Run tests

```bash
python -m pip install -e ".[test]"
pytest
```

Tests cover a healthy environment, a missing developer dependency, a missing required environment variable, malformed JSON, and a nonexistent config path.

## Repository layout

```text
pyproject.toml
src/envdoctor/       # CLI and diagnostic engine
tests/               # pytest unit tests
samples/config.json  # example configuration
samples/report.json  # illustrative JSON report
samples/diagnostic-events.json  # illustrative event fixture
```

## Diagnostic event sample

The task links to the official [diagnostic event samples](https://rabtechacademy.in/starter-files/python/diagnostic-events.json). The fixture included here is illustrative, not a copy of that official file. If the official sample uses a required schema, replace/adapt `samples/diagnostic-events.json` after downloading and reviewing the official JSON.

## License

MIT
