#!/usr/bin/env python3
"""Best-effort scan for sensitive files or high-confidence secrets before commit."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
MAX_TEXT_BYTES = 2_000_000

SENSITIVE_EXTENSIONS = {
    ".avro",
    ".csv",
    ".db",
    ".duckdb",
    ".feather",
    ".key",
    ".orc",
    ".p12",
    ".parquet",
    ".pem",
    ".pfx",
    ".pickle",
    ".pkl",
    ".sav",
    ".sqlite",
    ".sqlite3",
    ".tsv",
    ".xls",
    ".xlsm",
    ".xlsx",
}
SENSITIVE_DIRS = {"data", "input", "inputs", "output", "outputs", "results", "work"}
SKIP_DIRS = {".git", ".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"}

SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("GitHub token", re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{30,}\b")),
    ("Slack token", re.compile(r"\bxox(?:a|b|p|r|s)-[A-Za-z0-9-]{20,}\b")),
    ("bearer token", re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    (
        "credential in URI",
        re.compile(r"(?i)\b[a-z][a-z0-9+.-]{1,20}://[^\s/:@]+:[^\s/@]{4,}@[^\s]+"),
    ),
)


def git_paths(root: Path) -> list[Path] | None:
    if not shutil.which("git"):
        return None
    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return None
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "."],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return [root / item.decode("utf-8", errors="surrogateescape") for item in result.stdout.split(b"\0") if item]


def walk_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if relative.parts[:2] == (".agent", "local"):
            continue
        if path.is_file():
            paths.append(path)
    return paths


def candidate_paths(root: Path = ROOT) -> list[Path]:
    return git_paths(root) or walk_paths(root)


def path_findings(path: Path, root: Path = ROOT) -> list[str]:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return [f"path is outside repository: {path}"]
    normalized_parts = tuple(part.lower() for part in relative.parts)
    findings: list[str] = []

    if normalized_parts[:2] == (".agent", "local"):
        findings.append("private local state is present in the commit candidate set")
    if any(part in SENSITIVE_DIRS for part in normalized_parts[:-1]):
        findings.append("file is under a data or result directory")
    if path.suffix.lower() in SENSITIVE_EXTENSIONS:
        findings.append(f"sensitive file extension {path.suffix.lower()}")

    name = path.name.lower()
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        findings.append("environment file")
    if name.startswith("credentials.") or name.startswith("secrets."):
        findings.append("credential-named file")
    return findings


def text_findings(path: Path) -> list[str]:
    try:
        size = path.stat().st_size
    except OSError:
        return ["file could not be inspected"]
    if size > MAX_TEXT_BYTES:
        return []
    try:
        raw = path.read_bytes()
    except OSError:
        return ["file could not be read"]
    if b"\0" in raw:
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return []

    findings: list[str] = []
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    return findings


def scan(paths: Iterable[Path], root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    for path in sorted(set(paths)):
        relative = path.relative_to(root) if root == path or root in path.parents else path
        for issue in path_findings(path, root):
            findings.append(f"{relative}: {issue}")
        for issue in text_findings(path):
            findings.append(f"{relative}: possible {issue}")
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    del argv
    findings = scan(candidate_paths(ROOT), ROOT)
    if findings:
        for finding in findings:
            print(f"ERROR {finding}")
        print(f"FAIL  sensitive-content scan found {len(findings)} issue(s)")
        return 1
    print("PASS  sensitive-content scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
