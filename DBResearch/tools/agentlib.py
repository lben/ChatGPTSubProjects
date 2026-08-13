#!/usr/bin/env python3
"""Shared zero-dependency state and validation functions for DBResearch."""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = ROOT / ".agent"
CONFIG_PATH = AGENT_DIR / "harness.json"
TEMPLATES_DIR = AGENT_DIR / "templates"
LOCAL_DIR = AGENT_DIR / "local"
ACTIVE_PATH = LOCAL_DIR / "ACTIVE_TASK.md"
MEMORY_PATH = LOCAL_DIR / "MEMORY.md"
PENDING_DIR = LOCAL_DIR / "pending"
HISTORY_DIR = LOCAL_DIR / "history"

LOCAL_TEMPLATE_MAP = {
    "ACTIVE_TASK.md": TEMPLATES_DIR / "ACTIVE_TASK.md",
    "MEMORY.md": TEMPLATES_DIR / "MEMORY.md",
    "DECISIONS.md": TEMPLATES_DIR / "DECISIONS.md",
    "RECONCILIATION.md": TEMPLATES_DIR / "RECONCILIATION.md",
    "WORKSTYLE.md": TEMPLATES_DIR / "WORKSTYLE.md",
    "LOCAL_TOOLING.json": TEMPLATES_DIR / "LOCAL_TOOLING.example.json",
}
LOCAL_SUBDIRS = (PENDING_DIR, HISTORY_DIR, LOCAL_DIR / "db-requests", LOCAL_DIR / "db-results")

ALLOWED_TASK_STATUSES = {"EMPTY", "ACTIVE", "BLOCKED", "IN_REVIEW", "DONE"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def ensure_local_state() -> list[Path]:
    """Create ignored runtime files from tracked templates when absent."""
    created: list[Path] = []
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    for name, source in LOCAL_TEMPLATE_MAP.items():
        if not source.is_file():
            raise ValueError(f"Missing local-state template: {safe_relative(source)}")
        destination = LOCAL_DIR / name
        if not destination.exists():
            shutil.copyfile(source, destination)
            created.append(destination)
    for directory in LOCAL_SUBDIRS:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)
    return created


def load_config() -> dict[str, Any]:
    try:
        raw = json.loads(read_text(CONFIG_PATH))
    except FileNotFoundError as exc:
        raise ValueError(f"Missing configuration: {CONFIG_PATH.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {CONFIG_PATH.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("Harness configuration must be a JSON object.")
    return raw


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse simple scalar YAML frontmatter without adding a YAML dependency."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return {}

    result: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        result[key] = value
    return result


def heading_sections(text: str) -> dict[str, str]:
    """Return second-level Markdown sections keyed by lowercase heading."""
    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1).strip().lower()] = text[start:end].strip()
    return sections


def field_value(text: str, field: str) -> str:
    match = re.search(rf"(?mi)^{re.escape(field)}:[ \t]*(.*?)[ \t]*$", text)
    return match.group(1).strip() if match else ""


def meaningful_text(value: str) -> bool:
    without_comments = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    ignored = {"", "- not available.", "- not reviewed.", "- none.", "_no active task._"}
    return without_comments.strip().lower() not in ignored


def local_now() -> datetime:
    return datetime.now().astimezone()


def bullet_lines(values: Sequence[str], fallback: str) -> str:
    clean = [value.strip() for value in values if value.strip()]
    return "\n".join(f"- {value}" for value in clean) if clean else f"- {fallback}"


def render_empty_task() -> str:
    return """# Active Task

Status: EMPTY
Title:
Last updated:

## Core goal

_No active task._

## Done when

- [ ] Define an active task.

## Non-goals

- None.

## Real proof

- Not defined.

## Current milestone

- None.

## Next action

- Start a task with Workmate, `/task-cycle`, or `agentctl new-task`.

## Result

- Not available.

## Evidence

- Not available.

## Learnings

- Not reviewed.

## Blockers

- None.
"""


def render_task(
    *,
    title: str,
    goal: str,
    done_when: Sequence[str],
    non_goals: Sequence[str],
    proof: Sequence[str],
) -> str:
    timestamp = local_now().isoformat(timespec="seconds")
    checks = [value.strip() for value in done_when if value.strip()]
    done_block = "\n".join(f"- [ ] {value}" for value in checks)
    return f"""# Active Task

Status: ACTIVE
Title: {title.strip()}
Last updated: {timestamp}

## Core goal

{goal.strip()}

## Done when

{done_block}

## Non-goals

{bullet_lines(non_goals, "No additional work outside the stated goal.")}

## Real proof

{bullet_lines(proof, "Run the canonical verification and observe the requested behavior.")}

## Current milestone

- Inspect the existing behavior and define the smallest complete change.

## Next action

- Read relevant files, decisions, skills, and verification commands.

## Result

- Not available.

## Evidence

- Not available.

## Learnings

- Not reviewed.

## Blockers

- None.
"""


def safe_relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_cwd(raw: str) -> Path:
    candidate = (ROOT / raw).resolve()
    root = ROOT.resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"Command cwd escapes repository: {raw}")
    if not candidate.is_dir():
        raise ValueError(f"Command cwd is not a directory: {raw}")
    return candidate


def expand_argv(values: Sequence[str]) -> list[str]:
    if not values or not all(isinstance(value, str) and value for value in values):
        raise ValueError("Command argv must be a non-empty array of non-empty strings.")
    replacements = {"{python}": sys.executable, "{root}": str(ROOT)}
    expanded: list[str] = []
    for value in values:
        for marker, replacement in replacements.items():
            value = value.replace(marker, replacement)
        expanded.append(value)
    return expanded


def validation_findings() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        config = load_config()
    except ValueError as exc:
        return [str(exc)], warnings

    required_paths = config.get("required_paths", [])
    if not isinstance(required_paths, list) or not all(isinstance(item, str) for item in required_paths):
        errors.append("required_paths must be an array of strings.")
        required_paths = []
    for raw in required_paths:
        if not (ROOT / raw).exists():
            errors.append(f"Missing required path: {raw}")

    if not LOCAL_DIR.exists():
        warnings.append("Local state is not initialized; run agentctl init.")

    if MEMORY_PATH.exists():
        memory_length = len(read_text(MEMORY_PATH))
        limit = config.get("memory_max_chars", 5000)
        if not isinstance(limit, int) or limit < 1:
            errors.append("memory_max_chars must be a positive integer.")
        elif memory_length > limit:
            errors.append(f"MEMORY.md is {memory_length} chars; limit is {limit}.")

    if ACTIVE_PATH.exists():
        active = read_text(ACTIVE_PATH)
        status = field_value(active, "Status").upper()
        if status not in ALLOWED_TASK_STATUSES:
            errors.append(f"ACTIVE_TASK.md has invalid Status: {status or '<missing>'}")
        sections = heading_sections(active)
        required_headings = config.get("active_task_required_headings", [])
        if not isinstance(required_headings, list):
            errors.append("active_task_required_headings must be an array.")
            required_headings = []
        for heading in required_headings:
            if not isinstance(heading, str) or heading.lower() not in sections:
                errors.append(f"ACTIVE_TASK.md is missing heading: {heading}")

    skills_root = ROOT / ".github" / "skills"
    if skills_root.is_dir():
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                errors.append(f"Skill directory lacks SKILL.md: {safe_relative(skill_dir)}")
                continue
            metadata = parse_frontmatter(read_text(skill_file))
            name = metadata.get("name", "")
            description = metadata.get("description", "")
            if name != skill_dir.name:
                errors.append(
                    f"Skill name mismatch in {safe_relative(skill_file)}: "
                    f"expected {skill_dir.name!r}, found {name!r}"
                )
            if not description:
                errors.append(f"Skill has no description: {safe_relative(skill_file)}")
            if name and not re.fullmatch(r"[a-z0-9-]{1,64}", name):
                errors.append(f"Invalid skill name: {name}")

    agents_root = ROOT / ".github" / "agents"
    if agents_root.is_dir():
        for agent_file in sorted(agents_root.glob("*.agent.md")):
            metadata = parse_frontmatter(read_text(agent_file))
            if not metadata.get("name"):
                errors.append(f"Agent has no name: {safe_relative(agent_file)}")
            if not metadata.get("description"):
                errors.append(f"Agent has no description: {safe_relative(agent_file)}")

    pointer = ROOT / ".github" / "copilot-instructions.md"
    if pointer.exists() and "AGENTS.md" not in read_text(pointer):
        warnings.append("copilot-instructions.md does not reference AGENTS.md.")

    verification = config.get("verification", {})
    if not isinstance(verification, dict):
        errors.append("verification must be a JSON object.")
    else:
        for tier, commands in verification.items():
            if not isinstance(tier, str) or not isinstance(commands, list):
                errors.append("Each verification tier must contain an array of commands.")
                continue
            for index, command in enumerate(commands):
                label = f"verification.{tier}[{index}]"
                if not isinstance(command, dict):
                    errors.append(f"{label} must be an object.")
                    continue
                argv = command.get("argv")
                try:
                    expand_argv(argv if isinstance(argv, list) else [])
                    resolve_cwd(str(command.get("cwd", ".")))
                except ValueError as exc:
                    errors.append(f"{label}: {exc}")
                timeout = command.get("timeout_seconds", 300)
                if not isinstance(timeout, int) or timeout < 1:
                    errors.append(f"{label}.timeout_seconds must be a positive integer.")

    return errors, warnings
