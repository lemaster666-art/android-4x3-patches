#!/usr/bin/env python3
"""Route project commands, check preserved repair sources and print Mac delivery."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from android4x3.errors import PatchError
from android4x3.repair_workshop import load_repair_profile, repair_mac_command, route_invocation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    route = commands.add_parser("route", help="Resolve explicit standalone/combined project commands")
    route.add_argument("text")
    verify = commands.add_parser("verify", help="Check immutable repair source pins; no APK execution")
    verify.add_argument("repair")
    command = commands.add_parser("command", help="Generate a source-only Mac builder command")
    command.add_argument("repair")
    command.add_argument("--workflow", choices=["exit", "startup-exit"])
    command.add_argument("--ref", default="main")
    command.add_argument("--repository", default="lemaster666-art/android-4x3-patches")
    args = parser.parse_args()
    if args.command == "route":
        print(json.dumps(route_invocation(args.text), indent=2))
    elif args.command == "verify":
        p = load_repair_profile(REPO, args.repair)
        print(json.dumps({"repair": args.repair, "sources_checked": len(p["source_checksums"]),
                          "state": "source pins match", "hardware_validation": p.get("hardware_validation", {})}, indent=2))
    else:
        print(repair_mac_command(REPO, args.repair, args.ref, args.repository, workflow=args.workflow))


if __name__ == "__main__":
    try:
        main()
    except (PatchError, OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"Repair workshop stopped: {exc}")
