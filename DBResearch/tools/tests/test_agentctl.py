from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import agentctl  # noqa: E402


class AgentCtlTests(unittest.TestCase):
    def test_parse_frontmatter_reads_scalars(self) -> None:
        metadata = agentctl.parse_frontmatter(
            "---\nname: example-skill\ndescription: 'Useful skill'\n---\n# Body\n"
        )
        self.assertEqual(metadata["name"], "example-skill")
        self.assertEqual(metadata["description"], "Useful skill")

    def test_parse_frontmatter_rejects_unclosed_header(self) -> None:
        self.assertEqual(agentctl.parse_frontmatter("---\nname: broken\n"), {})

    def test_heading_sections_extracts_second_level_sections(self) -> None:
        sections = agentctl.heading_sections("# T\n\n## One\nA\n\n## Two\nB\n")
        self.assertEqual(sections, {"one": "A", "two": "B"})

    def test_field_value_does_not_cross_lines(self) -> None:
        text = "Title:\nLast updated:\n"
        self.assertEqual(agentctl.field_value(text, "Title"), "")

    def test_render_task_contains_contract(self) -> None:
        task = agentctl.render_task(
            title="Fix issue",
            goal="Restore behavior.",
            done_when=["The flow succeeds."],
            non_goals=["Do not redesign UI."],
            proof=["Run the acceptance check."],
        )
        self.assertEqual(agentctl.field_value(task, "Status"), "ACTIVE")
        self.assertIn("- [ ] The flow succeeds.", task)
        self.assertIn("## Real proof", task)

    def test_resolve_cwd_rejects_escape(self) -> None:
        with self.assertRaises(ValueError):
            agentctl.resolve_cwd("../")

    def test_expand_argv_replaces_markers_without_shell(self) -> None:
        argv = agentctl.expand_argv(["{python}", "-c", "print('{root}')"])
        self.assertEqual(argv[0], sys.executable)
        self.assertIn(str(agentctl.ROOT), argv[2])

    def test_starter_harness_validates(self) -> None:
        errors, _warnings = agentctl.validation_findings()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
