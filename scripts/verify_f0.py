"""Run the repeatable F0-08 handover gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from failure_demo import run_demo as run_failure_demo
from provider_replacement_demo import run_demo as run_provider_demo

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "scripts/start.cmd",
    "scripts/stop.cmd",
    "scripts/start.sh",
    "scripts/stop.sh",
    "scripts/provider_replacement_demo.py",
    "scripts/failure_demo.py",
    "docs/handover-runbook.md",
    "docs/releases/v0.1.0.md",
    "CHANGELOG.md",
)
EXPECTED_SERVICES = {"api", "postgres", "redis", "web", "worker"}


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )


def _verify_repository() -> dict[str, object]:
    missing = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    if missing:
        raise AssertionError(f"missing F0 delivery files: {', '.join(missing)}")
    with (ROOT / "pyproject.toml").open("rb") as stream:
        version = tomllib.load(stream)["project"]["version"]
    if version != "0.1.0":
        raise AssertionError(f"expected project version 0.1.0, found {version}")
    return {"required_files": len(REQUIRED_FILES), "project_version": version}


def _verify_docker() -> dict[str, object]:
    _run(["docker", "compose", "config", "--quiet"])
    output = _run(["docker", "compose", "ps", "--format", "json"]).stdout
    try:
        payload = json.loads(output)
        rows = payload if isinstance(payload, list) else [payload]
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in output.splitlines() if line.strip()]
    running = {row["Service"] for row in rows if row.get("State") == "running"}
    unhealthy = {
        row["Service"]: row.get("Health")
        for row in rows
        if row.get("Service") in EXPECTED_SERVICES and row.get("Health") != "healthy"
    }
    if not EXPECTED_SERVICES.issubset(running):
        raise AssertionError(f"services not running: {sorted(EXPECTED_SERVICES - running)}")
    if unhealthy:
        raise AssertionError(f"services not healthy: {unhealthy}")
    smoke = _run([sys.executable, "tests/e2e_smoke.py"])
    return {
        "healthy_services": sorted(EXPECTED_SERVICES),
        "e2e": json.loads(smoke.stdout.strip().splitlines()[-1]),
    }


def run_gate(*, docker: bool) -> dict[str, object]:
    result: dict[str, object] = {
        "gate": "F0-08",
        "status": "passed",
        "repository": _verify_repository(),
        "provider_replacement": run_provider_demo(),
        "structured_failure": run_failure_demo(),
    }
    if docker:
        result["docker"] = _verify_docker()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--docker",
        action="store_true",
        help="also require five healthy services and run the async Docker E2E test",
    )
    args = parser.parse_args()
    print(json.dumps(run_gate(docker=args.docker), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
