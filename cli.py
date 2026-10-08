"""Command-line interface."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from .core import ConfigurationError, inspect_environment, load_config, render_json, render_text

EXIT_OK = 0
EXIT_UNHEALTHY = 1
EXIT_ERROR = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdoctor",
        description="Inspect Python, free disk space, required environment-variable names, and developer tools.",
        epilog="Exit codes: 0=healthy, 1=checks failed, 2=configuration or runtime error.",
    )
    parser.add_argument("--config", help="Path to a JSON configuration file")
    parser.add_argument("--json", action="store_true", help="Print the report as structured JSON")
    parser.add_argument("--output", help="Write the report to a file instead of stdout")
    parser.add_argument("--disk-path", help="Path whose filesystem should be checked (defaults to home directory)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        report = inspect_environment(config, disk_path=args.disk_path)
        output = render_json(report) if args.json else render_text(report)
        if args.output:
            try:
                Path(args.output).write_text(output, encoding="utf-8")
            except OSError as exc:
                print(f"envdoctor: cannot write output '{args.output}': {exc}", file=sys.stderr)
                return EXIT_ERROR
        else:
            sys.stdout.write(output)
        return EXIT_OK if report["status"] == "healthy" else EXIT_UNHEALTHY
    except ConfigurationError as exc:
        print(f"envdoctor: configuration error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as exc:  # Keep unexpected operational errors user-friendly.
        print(f"envdoctor: unexpected error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
