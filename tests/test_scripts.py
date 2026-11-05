import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


validate = load("validate")
gen_index = load("gen_index")

GOOD = {
    "format": "rammaps/1",
    "game": "Test Game",
    "system": "gba",
    "rom": {"sha1": ["a1" * 20], "header_code": "TEST"},
    "memory_regions": [{"name": "ewram", "start": "0x02000000", "size": "0x40000"}],
    "pointers": {"work": "0x03001000"},
    "values": {"coins": {"type": "u32", "at": "0x02000250", "how": ["capture"]},
               "hp": {"type": "u16", "at": {"ptr": "work", "off": "0x10"}, "status": "unconfirmed"}},
    "structs": {"unit": {"size": "0x20", "fields": {
        "name": {"type": "str", "off": "0x00", "len": 15},
        "level": {"type": "u8", "off": "0x0F"}}}},
    "entities": {"party": {"struct": "unit", "at": "0x02000500", "count": 4}},
    "flags": {"base": "0x02000040", "bits": 64},
    "rom_tables": {"items": {"table": "0x7B6A8", "stride": 44, "count": 10}},
    "sources": {"method": "Found by diffing captures. " * 5},
}


def write_map(root, d, system="gba", name="test-game-usa.json"):
    p = Path(root, "maps", system)
    p.mkdir(parents=True, exist_ok=True)
    f = p / name
    f.write_text(json.dumps(d), encoding="utf-8")
    return f


class ValidateTests(unittest.TestCase):
    def errs(self, mutate):
        d = copy.deepcopy(GOOD)
        mutate(d)
        return validate.validate_map(d)

    def test_good_map(self):
        self.assertEqual(validate.validate_map(GOOD), [])

    def test_real_maps_valid(self):
        for p in ROOT.glob("maps/*/*.json"):
            self.assertEqual(validate.validate_file(p), [], str(p))

    def test_missing_required(self):
        self.assertTrue(self.errs(lambda d: d.pop("rom")))

    def test_unknown_top_key(self):
        self.assertTrue(self.errs(lambda d: d.update(extra=1)))

    def test_unknown_pointer(self):
        self.assertTrue(self.errs(lambda d: d["values"]["hp"]["at"].update(ptr="nope")))

    def test_bad_type(self):
        self.assertTrue(self.errs(lambda d: d["values"]["coins"].update(type="u24")))

    def test_str_needs_len(self):
        self.assertTrue(self.errs(lambda d: d["structs"]["unit"]["fields"]["name"].pop("len")))

    def test_field_past_struct(self):
        self.assertTrue(self.errs(lambda d: d["structs"]["unit"]["fields"]["level"].update(off="0x20")))

    def test_unknown_struct(self):
        self.assertTrue(self.errs(lambda d: d["entities"]["party"].update(struct="x")))

    def test_banned_key(self):
        self.assertTrue(self.errs(lambda d: d["values"].update(dialog={"type": "u8", "at": "0x02000001"})))

    def test_long_string_outside_sources(self):
        self.assertTrue(self.errs(lambda d: d.update(game="x" * 81)))

    def test_long_string_in_sources_ok(self):
        self.assertEqual(self.errs(lambda d: d["sources"].update(method="y" * 200)), [])

    def test_extra_sha1_sized_hex(self):
        self.assertTrue(self.errs(lambda d: d["sources"].update(method="a1" * 20)))
        self.assertTrue(self.errs(lambda d: d["rom"]["sha1"].append("not-a-hash")))

    def test_hex_string_outside_address_position(self):
        self.assertTrue(self.errs(lambda d: d["sources"].update(method="0x1234")))

    def test_personal_path(self):
        self.assertTrue(self.errs(lambda d: d["sources"].update(method="see /home/someone/x")))

    def test_filename_rules(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(validate.validate_file(write_map(t, GOOD)), [])
            self.assertTrue(validate.validate_file(write_map(t, GOOD, name="Bad Name.json")))
            self.assertTrue(validate.validate_file(write_map(t, GOOD, system="snes")))

    def test_main_exit_codes(self):
        with tempfile.TemporaryDirectory() as t:
            good = write_map(t, GOOD)
            bad = dict(GOOD, format="nope")
            badf = write_map(t, bad, name="bad-game-usa.json")
            self.assertEqual(validate.main([str(good)]), 0)
            self.assertEqual(validate.main([str(good), str(badf)]), 1)
            self.assertEqual(validate.main([str(Path(t, "missing.json"))]), 1)


class GenIndexTests(unittest.TestCase):
    def test_row_and_counts(self):
        total, unconf, text = gen_index.counts(GOOD)
        self.assertEqual((total, unconf), (2 + 2 + 1 + 1 + 1, 1))
        self.assertIn("64 flags", text)
        with tempfile.TemporaryDirectory() as t:
            f = write_map(t, GOOD)
            r = gen_index.row(f, GOOD)
        self.assertIn("| GBA | Test Game | USA |", r)
        self.assertIn("1 unconfirmed", r)
        self.assertIn("`a1a1a1a1`", r)

    def test_render_replaces_only_marked_region(self):
        with tempfile.TemporaryDirectory() as t:
            write_map(t, GOOD)
            text = "head\n%s\nOLD\n%s\ntail\n" % (gen_index.BEGIN, gen_index.END)
            out = gen_index.render(text, t)
            self.assertTrue(out.startswith("head\n"))
            self.assertTrue(out.endswith("\n%s\ntail\n" % gen_index.END))
            self.assertIn("Test Game", out)
            self.assertNotIn("OLD", out)
            self.assertEqual(gen_index.render(out, t), out)

    def test_missing_markers(self):
        with self.assertRaises(ValueError):
            gen_index.render("no markers", ROOT)

    def test_repo_readme_current(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(gen_index.render(text, ROOT), text)


if __name__ == "__main__":
    unittest.main()
