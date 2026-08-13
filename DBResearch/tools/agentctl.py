#!/usr/bin/env python3
"""Zero-dependency local-state command harness for DBResearch."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from typing import Any, Sequence

from agentlib import (
    ACTIVE_PATH,
    HISTORY_DIR,
    PENDING_DIR,
    ROOT,
    ensure_local_state,
    expand_argv,
    field_value,
    heading_sections,
    load_config,
    local_now,
    meaningful_text,
    parse_frontmatter,
    read_text,
    render_empty_task,
    render_task,
    resolve_cwd,
    safe_relative,
    validation_findings,
    write_text,
)

def cmd_validate(_: argparse.Namespace) -> int:
    errors, warnings = validation_findings()
    for warning in warnings:
        print(f"WARN  {warning}")
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        print(f"FAIL  {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS  harness validation ({len(warnings)} warning(s))")
    return 0


def git_summary() -> str:
    if not shutil.which("git"):
        return "Git executable not found"
    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return "Directory is not a Git work tree"
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if status.returncode != 0:
        return "Git status failed"
    count = len([line for line in status.stdout.splitlines() if line.strip()])
    return f"Git work tree; {count} changed path(s)"


def cmd_init(_: argparse.Namespace) -> int:
    created = ensure_local_state()
    if created:
        for path in created:
            print(f"CREATED {safe_relative(path)}")
    else:
        print("READY local state already exists")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    created = ensure_local_state()
    print(f"Root: {ROOT}")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"Git: {git_summary()}")
    print(f"Local state: {'initialized ' + str(len(created)) + ' item(s)' if created else 'ready'}")
    print(f"Skills: {'present' if (ROOT / '.github' / 'skills').is_dir() else 'missing'}")
    print(f"Custom agents: {'present' if (ROOT / '.github' / 'agents').is_dir() else 'missing'}")
    print("Managed capabilities: inspect in VS Code; repository files cannot override company policy")
    return cmd_validate(args)


def cmd_status(_: argparse.Namespace) -> int:
    ensure_local_state()
    if not ACTIVE_PATH.exists():
        print(f"ERROR Missing {safe_relative(ACTIVE_PATH)}")
        return 1
    text = read_text(ACTIVE_PATH)
    sections = heading_sections(text)
    print(f"Status: {field_value(text, 'Status') or '<missing>'}")
    print(f"Title: {field_value(text, 'Title') or '<none>'}")
    next_action = sections.get("next action", "").replace("\n", " ").strip()
    blockers = sections.get("blockers", "").replace("\n", " ").strip()
    print(f"Next: {next_action or '<none>'}")
    print(f"Blockers: {blockers or '<none>'}")
    print(f"Repository: {git_summary()}")
    return 0


def cmd_new_task(args: argparse.Namespace) -> int:
    ensure_local_state()
    if ACTIVE_PATH.exists():
        current = read_text(ACTIVE_PATH)
        status = field_value(current, "Status").upper()
        if status in {"ACTIVE", "BLOCKED", "IN_REVIEW"} and not args.force:
            print(f"ERROR An existing task is {status}. Archive, complete, or use --force explicitly.")
            return 2
    task = render_task(
        title=args.title,
        goal=args.goal,
        done_when=args.done_when,
        non_goals=args.non_goal,
        proof=args.proof,
    )
    write_text(ACTIVE_PATH, task)
    print(f"CREATED {safe_relative(ACTIVE_PATH)}")
    return 0


def command_entries(tier: str) -> list[dict[str, Any]]:
    config = load_config()
    verification = config.get("verification", {})
    if not isinstance(verification, dict) or tier not in verification:
        raise ValueError(f"Unknown verification tier: {tier}")
    entries = verification[tier]
    if not isinstance(entries, list):
        raise ValueError(f"Verification tier {tier!r} must be an array.")
    return entries


def cmd_verify(args: argparse.Namespace) -> int:
    ensure_local_state()
    if cmd_validate(args) != 0:
        print("ABORT Verification did not start because harness validation failed.")
        return 1
    try:
        entries = command_entries(args.tier)
    except ValueError as exc:
        print(f"ERROR {exc}")
        return 2
    if not entries:
        print(f"ERROR Verification tier {args.tier!r} contains no commands.")
        return 2

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            print(f"ERROR Verification entry {index} is not an object.")
            return 2
        name = str(entry.get("name", f"Command {index}"))
        try:
            argv_value = entry.get("argv")
            argv = expand_argv(argv_value if isinstance(argv_value, list) else [])
            cwd = resolve_cwd(str(entry.get("cwd", ".")))
        except ValueError as exc:
            print(f"ERROR {name}: {exc}")
            return 2
        timeout = int(entry.get("timeout_seconds", 300))
        print(f"RUN   {name}")
        try:
            completed = subprocess.run(argv, cwd=cwd, check=False, timeout=timeout)
        except FileNotFoundError:
            print(f"FAIL  {name}: executable not found: {argv[0]}")
            return 1
        except subprocess.TimeoutExpired:
            print(f"FAIL  {name}: exceeded {timeout}s")
            return 1
        if completed.returncode != 0:
            print(f"FAIL  {name}: exit {completed.returncode}")
            return completed.returncode or 1
        print(f"PASS  {name}")

    print(f"PASS  verification tier: {args.tier}")
    return 0


def compact(value: str, limit: int = 800) -> str:
    value = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    lines: list[str] = []
    for line in value.splitlines():
        line = re.sub(r"^\s*-\s*(?:\[[ xX]\]\s*)?", "", line).strip()
        if line:
            lines.append(line)
    value = "; ".join(lines)
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def cmd_archive_task(_: argparse.Namespace) -> int:
    ensure_local_state()
    if not ACTIVE_PATH.exists():
        print(f"ERROR Missing {safe_relative(ACTIVE_PATH)}")
        return 1
    text = read_text(ACTIVE_PATH)
    status = field_value(text, "Status").upper()
    if status != "DONE":
        print(f"ERROR Task status must be DONE, not {status or '<missing>'}.")
        return 2
    sections = heading_sections(text)
    evidence = sections.get("evidence", "")
    result = sections.get("result", "")
    if not meaningful_text(result) or not meaningful_text(evidence):
        print("ERROR A DONE task requires meaningful Result and Evidence sections.")
        return 2

    now = local_now()
    title = field_value(text, "Title") or "Untitled task"
    goal = sections.get("core goal", "")
    learnings = sections.get("learnings", "")
    history_path = HISTORY_DIR / f"{now:%Y-%m}.md"
    if history_path.exists():
        history = read_text(history_path).rstrip() + "\n\n"
    else:
        history = f"# Completed Tasks — {now:%Y-%m}\n\n"
    entry = (
        f"## {now:%Y-%m-%d} — {title}\n\n"
        f"- Goal: {compact(goal)}\n"
        f"- Result: {compact(result)}\n"
        f"- Evidence: {compact(evidence)}\n"
        f"- Learnings: {compact(learnings) if meaningful_text(learnings) else 'No promoted learning.'}\n"
    )
    write_text(history_path, history + entry)
    write_text(ACTIVE_PATH, render_empty_task())
    print(f"ARCHIVED {safe_relative(history_path)}")
    print(f"RESET {safe_relative(ACTIVE_PATH)}")
    return 0


def cmd_pending(_: argparse.Namespace) -> int:
    ensure_local_state()
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    proposals = sorted(path for path in PENDING_DIR.glob("*.md") if path.name != ".gitkeep")
    if not proposals:
        print("No pending learning proposals.")
        return 0
    for path in proposals:
        print(safe_relative(path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create ignored local runtime state from templates.")
    init.set_defaults(func=cmd_init)

    doctor = subparsers.add_parser("doctor", help="Initialize, show environment, and validate the harness.")
    doctor.set_defaults(func=cmd_doctor)

    validate = subparsers.add_parser("validate", help="Validate harness files and contracts.")
    validate.set_defaults(func=cmd_validate)

    status = subparsers.add_parser("status", help="Show active task and repository status.")
    status.set_defaults(func=cmd_status)

    new_task = subparsers.add_parser("new-task", help="Create a structured active task.")
    new_task.add_argument("--title", required=True)
    new_task.add_argument("--goal", required=True)
    new_task.add_argument("--done-when", action="append", required=True, dest="done_when")
    new_task.add_argument("--non-goal", action="append", default=[])
    new_task.add_argument("--proof", action="append", default=[])
    new_task.add_argument("--force", action="store_true", help="Replace an existing active task explicitly.")
    new_task.set_defaults(func=cmd_new_task)

    verify = subparsers.add_parser("verify", help="Run an allowlisted verification tier.")
    verify.add_argument("tier", choices=["fast", "full"])
    verify.set_defaults(func=cmd_verify)

    archive = subparsers.add_parser("archive-task", help="Archive a proven DONE task and reset state.")
    archive.set_defaults(func=cmd_archive_task)

    pending = subparsers.add_parser("pending", help="List staged learning proposals.")
    pending.set_defaults(func=cmd_pending)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ValueError as exc:
        print(f"ERROR {exc}")
        return 2
    except KeyboardInterrupt:
        print("ABORT Interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
