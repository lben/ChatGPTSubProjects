#!/usr/bin/env python3
"""Bounded client for the external DBResearch run-db-query service."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parent.parent
LOCAL_DIR = ROOT / ".agent" / "local"
CONFIG_PATH = LOCAL_DIR / "LOCAL_TOOLING.json"
REQUEST_DIR = LOCAL_DIR / "db-requests"
RESULT_DIR = LOCAL_DIR / "db-results"

FORBIDDEN_KEYS = {
    "api_key",
    "apikey",
    "access_token",
    "authorization",
    "connection_string",
    "connectionstring",
    "credential",
    "credentials",
    "dsn",
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "user",
    "username",
}


class ToolError(ValueError):
    """A safe user-facing tool error."""


def read_json(path: Path, max_bytes: int) -> Any:
    try:
        size = path.stat().st_size
    except FileNotFoundError as exc:
        raise ToolError(f"Missing file: {relative(path)}") from exc
    if size > max_bytes:
        raise ToolError(f"File exceeds {max_bytes} bytes: {relative(path)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ToolError(f"Invalid JSON in {relative(path)}: line {exc.lineno}, column {exc.colno}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    path.write_text(payload, encoding="utf-8", newline="\n")


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def normalize_key(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum() or char == "_")


def find_forbidden_key(value: Any, prefix: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            if normalize_key(key_text) in FORBIDDEN_KEYS:
                return f"{prefix}.{key_text}"
            found = find_forbidden_key(nested, f"{prefix}.{key_text}")
            if found:
                return found
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found = find_forbidden_key(nested, f"{prefix}[{index}]")
            if found:
                return found
    return None


def require_safe_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ToolError(f"{label} must be a JSON object.")
    forbidden = find_forbidden_key(value)
    if forbidden:
        raise ToolError(f"{label} contains a forbidden credential field at {forbidden}.")
    return value


def require_local_path(raw: str, directory: Path, *, must_exist: bool) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    allowed = directory.resolve()
    if resolved != allowed and allowed not in resolved.parents:
        raise ToolError(f"Path must stay under {relative(directory)}: {raw}")
    if must_exist and not resolved.is_file():
        raise ToolError(f"Missing file: {relative(resolved)}")
    return resolved


def positive_int(config: dict[str, Any], key: str, default: int, maximum: int) -> int:
    value = config.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= maximum:
        raise ToolError(f"{key} must be an integer from 1 through {maximum}.")
    return value


def validate_loopback_url(raw: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise ToolError("base_url is invalid.") from exc
    if parsed.scheme != "http":
        raise ToolError("base_url must use http on loopback.")
    if parsed.username or parsed.password:
        raise ToolError("base_url must not contain credentials.")
    if (parsed.hostname or "").lower() not in {"127.0.0.1", "localhost", "::1"}:
        raise ToolError("base_url must target loopback only.")
    if port is None:
        raise ToolError("base_url must include an explicit port.")
    if parsed.query or parsed.fragment:
        raise ToolError("base_url must not contain a query or fragment.")
    return raw.rstrip("/")


def endpoint_path(config: dict[str, Any], key: str, default: str) -> str:
    value = config.get(key, default)
    if not isinstance(value, str) or not value.startswith("/") or "?" in value or "#" in value:
        raise ToolError(f"{key} must be an absolute URL path without query or fragment.")
    return value


def load_config() -> dict[str, Any]:
    raw = read_json(CONFIG_PATH, 100_000)
    config = require_safe_object(raw, "Local tooling configuration")
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    transport = config.get("transport")
    if transport not in {"command", "rest"}:
        raise ToolError("transport must be 'command' or 'rest'.")
    positive_int(config, "timeout_seconds", 60, 600)
    positive_int(config, "max_result_bytes", 5_000_000, 50_000_000)

    if transport == "command":
        argv = config.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
            raise ToolError("command transport requires a non-empty argv string array.")
        if not any("{request}" in item for item in argv):
            raise ToolError("command argv must include {request}.")
        if not any("{output}" in item for item in argv):
            raise ToolError("command argv must include {output}.")
        for item in argv:
            candidate = Path(item)
            if candidate.is_absolute():
                resolved = candidate.resolve()
                if resolved == ROOT.resolve() or ROOT.resolve() in resolved.parents:
                    raise ToolError("The trusted command or script must live outside DBResearch.")
    else:
        base_url = config.get("base_url")
        if not isinstance(base_url, str):
            raise ToolError("rest transport requires base_url.")
        validate_loopback_url(base_url)
        endpoint_path(config, "health_path", "/health")
        endpoint_path(config, "query_path", "/v1/query")
        positive_int(config, "max_request_bytes", 1_000_000, 10_000_000)


def expand_command(argv: list[str], request: Path, output: Path) -> list[str]:
    replacements = {
        "{request}": str(request),
        "{output}": str(output),
        "{root}": str(ROOT),
    }
    expanded: list[str] = []
    for item in argv:
        for marker, replacement in replacements.items():
            item = item.replace(marker, replacement)
        expanded.append(item)
    return expanded


def check_command_available(argv: list[str]) -> None:
    executable = argv[0]
    candidate = Path(executable)
    if candidate.is_absolute() or candidate.parent != Path("."):
        if not candidate.exists():
            raise ToolError("Configured external command does not exist.")
    elif shutil.which(executable) is None:
        raise ToolError("Configured external command is not on PATH.")


def execute_command(config: dict[str, Any], request: Path, output: Path) -> None:
    argv = expand_command(config["argv"], request, output)
    check_command_available(argv)
    timeout = positive_int(config, "timeout_seconds", 60, 600)
    if output.exists():
        output.unlink()
    try:
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            capture_output=True,
            text=False,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ToolError(f"External runner exceeded {timeout} seconds.") from exc
    except OSError as exc:
        raise ToolError("External runner could not start.") from exc
    if completed.returncode != 0:
        raise ToolError(f"External runner failed with exit code {completed.returncode}. Inspect its approved local diagnostics.")
    if not output.is_file():
        raise ToolError("External runner reported success but did not create the result file.")


def execute_rest(config: dict[str, Any], request_value: dict[str, Any], output: Path) -> None:
    base_url = validate_loopback_url(str(config["base_url"]))
    path = endpoint_path(config, "query_path", "/v1/query")
    timeout = positive_int(config, "timeout_seconds", 60, 600)
    max_request = positive_int(config, "max_request_bytes", 1_000_000, 10_000_000)
    max_result = positive_int(config, "max_result_bytes", 5_000_000, 50_000_000)
    payload = json.dumps(request_value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(payload) > max_request:
        raise ToolError(f"Request exceeds {max_request} bytes.")
    request = urllib.request.Request(
        base_url + path,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(max_result + 1)
    except urllib.error.HTTPError as exc:
        raise ToolError(f"Local runner returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise ToolError("Local runner is unavailable.") from exc
    if len(data) > max_result:
        raise ToolError(f"Runner response exceeds {max_result} bytes.")
    try:
        result = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolError("Runner response is not valid UTF-8 JSON.") from exc
    require_safe_object(result, "Runner result")
    write_json(output, result)


def validate_result_file(path: Path, max_bytes: int) -> None:
    result = read_json(path, max_bytes)
    require_safe_object(result, "Runner result")


def cmd_doctor(_: argparse.Namespace) -> int:
    config = load_config()
    transport = config["transport"]
    if transport == "command":
        argv = config["argv"]
        check_command_available(argv)
        print("PASS command transport is configured and executable is available")
        return 0

    base_url = validate_loopback_url(str(config["base_url"]))
    path = endpoint_path(config, "health_path", "/health")
    timeout = min(10, positive_int(config, "timeout_seconds", 60, 600))
    request = urllib.request.Request(base_url + path, method="GET", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(4097)
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        raise ToolError(f"Local runner health check returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise ToolError("Local runner health check failed.") from exc
    if not 200 <= status < 300:
        raise ToolError(f"Local runner health check returned HTTP {status}.")
    print("PASS loopback REST runner is reachable")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    REQUEST_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    request_path = require_local_path(args.request, REQUEST_DIR, must_exist=True)
    output_path = require_local_path(args.output, RESULT_DIR, must_exist=False)
    config = load_config()
    max_request = positive_int(config, "max_request_bytes", 1_000_000, 10_000_000) if config["transport"] == "rest" else 10_000_000
    request_value = require_safe_object(read_json(request_path, max_request), "Query request")

    if config["transport"] == "command":
        execute_command(config, request_path, output_path)
        max_result = positive_int(config, "max_result_bytes", 5_000_000, 50_000_000)
        validate_result_file(output_path, max_result)
    else:
        execute_rest(config, request_value, output_path)

    print(f"PASS result written to {relative(output_path)} ({output_path.stat().st_size} bytes)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Validate and probe the configured external runner.")
    doctor.set_defaults(func=cmd_doctor)

    query = subparsers.add_parser("query", help="Run one reviewed local request through the external runner.")
    query.add_argument("--request", required=True)
    query.add_argument("--output", required=True)
    query.set_defaults(func=cmd_query)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ToolError as exc:
        print(f"ERROR {exc}")
        return 2
    except KeyboardInterrupt:
        print("ABORT Interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
