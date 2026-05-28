#!/usr/bin/env python3
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Generate SBOM artifact manifests from a charmcraft YAML input."""

import argparse
import sys

try:
    import yaml  # pyright: ignore[reportMissingModuleSource]
except ImportError:
    print("This script requires PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

SERVICE_URL = "https://sbom-request.canonical.com"

SERIES_TO_BASE = {
    "focal": "ubuntu@20.04",
    "jammy": "ubuntu@22.04",
    "noble": "ubuntu@24.04",
}


class FlowList(list):
    """List subtype represented in inline YAML flow style."""


def _flow_list_representer(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


yaml.SafeDumper.add_representer(FlowList, _flow_list_representer)


def load_yaml(stream):
    """Load a YAML document from a file-like stream."""
    return yaml.safe_load(stream)


def gen_artifacts(document: dict, clients_for_artifacts: list[str]) -> list[dict]:
    """Generate one artifact from a charmcraft YAML document."""
    charm_name = document.get("name")
    if not charm_name:
        return []

    artifact = {
        "name": charm_name,
        "type": "charm",
        "clients": FlowList(list(clients_for_artifacts)),
    }

    channel = document.get("channel")
    if channel:
        artifact["channel"] = channel

    series = document.get("series")
    if series and series in SERIES_TO_BASE:
        artifact["base"] = SERIES_TO_BASE[series]

    return [artifact]


def parse_clients_arg(clients_arg: str) -> list[str]:
    """Parse and validate a comma-separated clients value."""
    parts = [part.strip() for part in clients_arg.split(",") if part.strip()]
    valid = {"sbom", "secscan"}
    unknown = [part for part in parts if part not in valid]

    if unknown:
        raise ValueError(
            f"Unknown client(s): {', '.join(unknown)} (valid: sbom, secscan)"
        )

    if "sbom" not in parts:
        raise ValueError("At least 'sbom' must be included.")

    ordered = []
    if "sbom" in parts:
        ordered.append("sbom")
    if "secscan" in parts:
        ordered.append("secscan")
    return ordered


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Generate artifact list YAML from application-style YAML."
    )
    parser.add_argument(
        "input_yaml",
        nargs="?",
        help="Path to input YAML. If omitted, reads from STDIN.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="manifest.yaml",
        help="Output file path (default: manifest.yaml)",
    )

    parser.add_argument("--department", default="charm_engineering")
    parser.add_argument("--email", default="your.email@canonical.com")
    parser.add_argument("--team", default="analytics")

    parser.add_argument(
        "--clients",
        default="sbom",
        help=(
            "Comma-separated list of clients to assign to each artifact. "
            "Allowed: 'sbom' or 'sbom,secscan'. Default: sbom"
        ),
    )
    parser.add_argument(
        "--with-secscan",
        action="store_true",
        help="Shorthand for --clients sbom,secscan",
    )

    args = parser.parse_args()

    if args.with_secscan:
        clients_list = ["sbom", "secscan"]
    else:
        try:
            clients_list = parse_clients_arg(args.clients)
        except ValueError as error:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(2)

    if args.input_yaml:
        with open(args.input_yaml, "r", encoding="utf-8") as stream:
            input_document = load_yaml(stream)
    else:
        input_document = load_yaml(sys.stdin)

    clients_block = {
        "sbom": {
            "service_url": SERVICE_URL,
            "department": args.department,
            "email": args.email,
            "team": args.team,
        }
    }

    if "secscan" in clients_list:
        clients_block["secscan"] = {}

    try:
        artifacts = gen_artifacts(input_document, clients_list)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(2)

    output = {
        "clients": clients_block,
        "artifacts": artifacts,
    }

    with open(args.output, "w", encoding="utf-8") as stream:
        yaml.safe_dump(
            output,
            stream,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            indent=2,
        )

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()