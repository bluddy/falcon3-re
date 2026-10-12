"""Tests for tools/naming.py (the rename/annotation system).

Run:  venv\\Scripts\\python -m unittest discover -s tests -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import naming  # noqa: E402


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def make_fixture(tmp):
    """Ledger + function_bytes + data_symbols + src tree in tmp."""
    ledger = {
        "schema": 1,
        "symbols": [
            {"ida": "sub_A", "name": "widget_init", "kind": "function", "notes": "t"},
            {"ida": "sub_B", "name": None, "kind": "function"},           # undecided
            {"ida": "word_100", "name": "k_state", "kind": "global"},
        ],
    }
    fb = {
        "sub_A": {"ea": 0x1000, "size": 4, "bytes": "9090c3cb", "is_far": True},
        "sub_B": {"ea": 0x2000, "size": 4, "bytes": "9090c3cb", "is_far": True},
        "sub_1": {"ea": 0x3000, "size": 4, "bytes": "9090c3cb", "is_far": True},
    }
    ds = [{"ea": 0x100, "size": 2, "ida_name": "word_100", "name": None, "kind": "word"}]
    paths = {
        "ledger": os.path.join(tmp, "naming.yaml"),
        "fb": os.path.join(tmp, "function_bytes.json"),
        "ds": os.path.join(tmp, "data_symbols.json"),
        "routines": os.path.join(tmp, "routines.yaml"),
        "structs": os.path.join(tmp, "structs.yaml"),
        "src": os.path.join(tmp, "src"),
    }
    write(paths["ledger"], _dump_yaml(ledger))
    json.dump(fb, open(paths["fb"], "w"))
    json.dump(ds, open(paths["ds"], "w"))
    write(paths["routines"], "routines: []\n")
    write(paths["structs"], "schema: 1\nstructs: []\n")
    write(os.path.join(paths["src"], "main.c"),
          "/* sub_A here */\nint sub_A(void) { return sub_1; }\nint sub_12_unrelated(void);\n")
    write(os.path.join(paths["src"], "asm", "notes.asm"),
          "; uses sub_A and word_100\nnop\n")
    return paths


def _dump_yaml(doc):
    import yaml
    import io
    s = yaml.dump(doc, default_flow_style=False, sort_keys=False)
    return s


class NamingCase(unittest.TestCase):
    def fixture(self):
        self.tmp = tempfile.mkdtemp(prefix="falcon3_naming_")
        self.paths = make_fixture(self.tmp)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def load(self):
        return naming.load_ledger(self.paths["ledger"])

    def apply_kw(self, **kw):
        defaults = dict(doc=self.load(), fb_path=self.paths["fb"],
                        ds_path=self.paths["ds"], roots=[self.paths["src"]])
        defaults.update(kw)
        return naming.apply(**defaults)

    def check_kw(self, **kw):
        defaults = dict(doc=self.load(), fb_path=self.paths["fb"],
                        ds_path=self.paths["ds"], roots=[self.paths["src"]],
                        routines=self.paths["routines"], structs=self.paths["structs"])
        defaults.update(kw)
        return naming.check(**defaults)


class TestResolve(NamingCase):
    def test_resolve_by_ida(self):
        self.fixture()
        self.assertEqual(naming.resolve("sub_A", self.load()),
                         ("sub_A", "widget_init"))

    def test_resolve_by_semantic(self):
        self.fixture()
        self.assertEqual(naming.resolve("widget_init", self.load()),
                         ("sub_A", "widget_init"))

    def test_resolve_unknown_passthrough(self):
        self.fixture()
        self.assertEqual(naming.resolve("r33_e85", self.load()),
                         ("r33_e85", "r33_e85"))

    def test_resolve_undecided(self):
        self.fixture()
        self.assertEqual(naming.resolve("sub_B", self.load()), ("sub_B", "sub_B"))


class TestApplyText(NamingCase):
    def test_word_boundary_no_partial(self):
        text = "sub_1 sub_12 sub_1x _sub_1 sub_A"
        new, n = naming.apply_text(text, [("sub_1", "renamed")])
        self.assertIn("renamed sub_12 sub_1x _sub_1 sub_A", new)
        self.assertEqual(new.split().count("renamed"), 1)

    def test_forward_and_reverse_roundtrip(self):
        text = "call widget_init ; widget_init"
        back, _ = naming.apply_text(text, [("sub_A", "widget_init")], forward=False)
        self.assertEqual(back, "call sub_A ; sub_A")

    def test_idempotent(self):
        pairs = [("sub_A", "widget_init")]
        once, _ = naming.apply_text("int widget_init(void);", pairs)
        twice, n = naming.apply_text(once, pairs)
        self.assertEqual(once, twice)
        self.assertEqual(n, 0)


class TestApply(NamingCase):
    def test_apply_updates_all_targets(self):
        self.fixture()
        s = self.apply_kw()
        self.assertEqual(s["ledger_renames"], 2)  # sub_A + word_100
        fb = json.load(open(self.paths["fb"]))
        self.assertEqual(fb["sub_A"]["name"], "widget_init")
        self.assertIn("sub_A", fb)              # keys immutable
        ds = json.load(open(self.paths["ds"]))
        self.assertEqual(ds[0]["name"], "k_state")
        main_c = open(os.path.join(self.paths["src"], "main.c")).read()
        self.assertIn("widget_init", main_c)
        self.assertNotIn("sub_A", main_c)
        # sub_12 must be untouched (word boundary)
        self.assertIn("sub_12_unrelated", main_c)
        asm = open(os.path.join(self.paths["src"], "asm", "notes.asm")).read()
        self.assertIn("widget_init", asm)
        self.assertIn("k_state", asm)

    def test_apply_idempotent(self):
        self.fixture()
        self.apply_kw()
        s2 = self.apply_kw()
        self.assertEqual(s2["text_hits"], 0)
        self.assertEqual(s2["fb_fields"], 0)

    def test_dry_run_changes_nothing(self):
        self.fixture()
        s = self.apply_kw(dry_run=True)
        self.assertTrue(s["dry_run"])
        fb = json.load(open(self.paths["fb"]))
        self.assertIsNone(fb["sub_A"].get("name"))

    def test_revert_restores(self):
        self.fixture()
        self.apply_kw()
        # revert via API needs ledger file on disk + ledger_path (never repo default)
        naming.revert("sub_A", doc=naming.load_ledger(self.paths["ledger"]),
                      fb_path=self.paths["fb"], ds_path=self.paths["ds"],
                      roots=[self.paths["src"]],
                      ledger_path=self.paths["ledger"])
        fb = json.load(open(self.paths["fb"]))
        self.assertIsNone(fb["sub_A"].get("name"))
        main_c = open(os.path.join(self.paths["src"], "main.c")).read()
        self.assertIn("sub_A", main_c)
        self.assertNotIn("widget_init", main_c)
        led = naming.load_ledger(self.paths["ledger"])
        self.assertIsNone(next(e for e in led["symbols"]
                               if e["ida"] == "sub_A")["name"])


class TestCheck(NamingCase):
    def test_green_after_apply(self):
        self.fixture()
        self.apply_kw()
        self.assertEqual(self.check_kw(), [])

    def test_flags_stale_text(self):
        self.fixture()
        # ledger has rename but apply not run
        probs = self.check_kw()
        self.assertTrue(any("run apply" in p for p in probs), probs)

    def test_flags_bad_identifier(self):
        self.fixture()
        led = self.load()
        led["symbols"][0]["name"] = "Not-An-Ident"
        probs = naming.check(doc=led, fb_path=self.paths["fb"],
                             ds_path=self.paths["ds"], roots=[self.paths["src"]],
                             routines=self.paths["routines"],
                             structs=self.paths["structs"])
        self.assertTrue(any("not a C identifier" in p for p in probs), probs)

    def test_flags_duplicate_target(self):
        self.fixture()
        led = self.load()
        led["symbols"].append({"ida": "sub_B", "name": "widget_init",
                               "kind": "function"})
        probs = naming.check(doc=led, fb_path=self.paths["fb"],
                             ds_path=self.paths["ds"], roots=[self.paths["src"]],
                             routines=self.paths["routines"],
                             structs=self.paths["structs"])
        self.assertTrue(any("both ->" in p for p in probs), probs)

    def test_flags_missing_ida_symbol(self):
        self.fixture()
        led = self.load()
        led["symbols"].append({"ida": "sub_ZZZ", "name": "nope_fn",
                               "kind": "function"})
        probs = naming.check(doc=led, fb_path=self.paths["fb"],
                             ds_path=self.paths["ds"], roots=[self.paths["src"]],
                             routines=self.paths["routines"],
                             structs=self.paths["structs"])
        self.assertTrue(any("sub_ZZZ" in p and "function_bytes" in p for p in probs), probs)


class TestStructs(NamingCase):
    def test_repo_seed_valid(self):
        self.assertEqual(naming.validate_structs(os.path.join(ROOT, "registry", "structs.yaml")), [])

    def test_bad_field_overflow(self):
        self.fixture()
        write(self.paths["structs"], """schema: 1
structs:
  - name: Bad
    size: 4
    status: hypothesis
    source: t
    fields:
      - {offset: 2, size: 4, name: x, type: uint16}
""")
        probs = naming.validate_structs(self.paths["structs"])
        self.assertTrue(any("extends past struct" in p for p in probs), probs)

    def test_duplicate_struct_name(self):
        self.fixture()
        write(self.paths["structs"], """schema: 1
structs:
  - {name: Dup, size: 4, status: hypothesis, source: t, fields: []}
  - {name: Dup, size: 4, status: hypothesis, source: t, fields: []}
""")
        probs = naming.validate_structs(self.paths["structs"])
        self.assertTrue(any("duplicate name" in p for p in probs), probs)


class TestPortcheckResolve(unittest.TestCase):
    """portcheck must extract with the C name but compare against the IDA name."""

    def test_resolve_integration(self):
        # use the REPO ledger (read-only)
        ida, sem = naming.resolve("sub_19CB0")
        self.assertEqual(ida, "sub_19CB0")
        self.assertEqual(sem, "farptr_field_reader")
        ida2, sem2 = naming.resolve("farptr_field_reader")
        self.assertEqual((ida2, sem2), ("sub_19CB0", "farptr_field_reader"))
        ida3, sem3 = naming.resolve("totally_unknown_fn")
        self.assertEqual((ida3, sem3), ("totally_unknown_fn", "totally_unknown_fn"))


class TestRepoConsistency(unittest.TestCase):
    """The real repo must be green (ledger applied)."""

    def test_repo_check_green(self):
        probs = naming.check()
        self.assertEqual(probs, [], "\n".join(probs))


if __name__ == "__main__":
    unittest.main()
