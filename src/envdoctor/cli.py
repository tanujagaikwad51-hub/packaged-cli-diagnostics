"""Command-line interface for EnvDoctor."""

import argparse
import json

from envdoctor.core import run_diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check developer environment health."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument("--config", help="Path to JSON configuration")
    parser.add_argument("--disk-path", default=None, help="Path to check")
    parser.add_argument("--output", help="Write report to a file")
    args = parser.parse_args()

    try:
        report = run_diagnostics(args.config, args.disk_path)
        output = (
            json.dumps(report, indent=2, sort_keys=True)
            if args.json
            else report_to_text(report)
        )
        if args.output:
            with open(args.output, "w", encoding="utf-8") as file:
                file.write(output + "\n")
        else:
            print(output)

        return 0 if report.get("status") == "healthy" else 1
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Configuration/runtime error: {error}")
        return 2


def report_to_text(report: dict) -> str:
    lines = [
        f"EnvDoctor status: {report.get('status', 'unknown')}",
        f"Checks: {report.get('summary', {})}",
    ]
    for check in report.get("checks", []):
        lines.append(
            f"- {check.get('name')}: {check.get('status')} — "
            f"{check.get('details')}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
