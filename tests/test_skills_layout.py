"""Plugin skill/command layout and the folded-in third-party skills."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FOLDED = (
    "i-have-adhd",
    "ponytail",
    "grill-me",
    "grilling",
    "tdd",
    "diagnosing-bugs",
    "codebase-design",
    "domain-modeling",
    "to-spec",
    "to-tickets",
    "code-review",
    "handoff-brief",
    "wait-what",
)
NOT_FOLDED = (
    "ponytail-audit", "ponytail-debt", "ponytail-gain", "ponytail-help", "ponytail-review",
    "prototype", "research", "pr", "wizard", "zoom-out", "triage",
)


def _frontmatter(path: Path) -> dict:
    text = path.read_text()
    block = text.split("---\n")[1]
    return dict(re.findall(r"^([a-z-]+):\s*(.*)$", block, flags=re.M))


class SkillLayoutTests(unittest.TestCase):
    def test_folded_skills_have_matching_name_and_command(self) -> None:
        for name in FOLDED:
            skill = ROOT / "skills" / name / "SKILL.md"
            self.assertTrue(skill.is_file(), name)
            self.assertEqual(_frontmatter(skill)["name"], name)
            stub = ROOT / "commands" / f"{name}.md"
            self.assertTrue(stub.is_file(), name)
            self.assertIn(f"skills/{name}/SKILL.md", stub.read_text())

    def test_whole_packs_are_not_vendored(self) -> None:
        for name in NOT_FOLDED:
            self.assertFalse((ROOT / "skills" / name).exists(), name)

    def test_no_dependency_on_the_source_plugins(self) -> None:
        for path in list((ROOT / "skills").rglob("*.md")) + list((ROOT / "commands").glob("*.md")):
            text = path.read_text()
            for needle in ("setup-matt-pocock-skills", "Skill tool", "mattpocock/skills"):
                self.assertNotIn(needle, text, f"{path}: {needle}")

    def test_support_files_referenced_by_skills_exist(self) -> None:
        for skill in (ROOT / "skills" / name / "SKILL.md" for name in FOLDED):
            for ref in re.findall(r"\]\((?:\./)?([A-Za-z0-9_-]+\.md)\)", skill.read_text()):
                self.assertTrue((skill.parent / ref).is_file(), f"{skill}: {ref}")

    def test_versions_agree(self) -> None:
        plugin = json.loads((ROOT / "plugin.json").read_text())["version"]
        cursor = json.loads((ROOT / ".cursor-plugin" / "plugin.json").read_text())["version"]
        self.assertEqual(plugin, cursor)


if __name__ == "__main__":
    unittest.main()
