#!/usr/bin/env python3
"""命令注册表与 anote 入口一致性测试。"""
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from anote.commands import COMMAND_META  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def entry_case_labels() -> set[str]:
    text = (PROJECT_ROOT / "anote").read_text(encoding="utf-8")
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip().startswith('case "$cmd" in'))
    depth = 1
    labels = set()
    for ln in lines[start + 1:]:
        if re.match(r"^\s*case\b.*\bin\b", ln):
            depth += 1
            continue
        if re.match(r"^\s*esac\b", ln):
            depth -= 1
            if depth == 0:
                break
            continue
        if depth != 1:
            continue
        m = re.match(r"^  ([A-Za-z0-9_|读论文-]+)\)", ln)
        if m:
            for part in m.group(1).split("|"):
                part = part.strip()
                if part and part != "*":
                    labels.add(part)
    return labels


class TestCommandRegistry(unittest.TestCase):
    def test_every_registered_case_exists_in_entry(self):
        labels = entry_case_labels()
        missing = []
        for meta in COMMAND_META:
            for case in meta.case.split("|"):
                if case not in labels:
                    missing.append(f"{meta.name}:{case}")
        self.assertEqual(missing, [])

    def test_registry_unique_names(self):
        names = [m.name for m in COMMAND_META]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
