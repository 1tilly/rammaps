#!/usr/bin/env python3
"""Validate rammaps/1 map files (stdlib only).

usage: python3 -I scripts/validate.py MAP.json [MAP.json ...]
With no arguments, validates every maps/*/*.json of this repository.
Exits 1 if any map is invalid, 2 on usage errors.
Rules are described in docs/schema.md.
"""
import json
import re
import sys
from pathlib import Path

HEX = re.compile(r"^0x[0-9A-Fa-f]{1,16}$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")
BARE_HEX = re.compile(r"^[0-9A-Fa-f]{16,}$")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*-(usa|europe|japan|world|korea|australia|germany|france|spain|italy)\.json$")
SYSTEM = re.compile(r"^[a-z0-9]+$")
INT_SIZE = {"u8": 1, "s8": 1, "u16": 2, "s16": 2, "u32": 4, "s32": 4, "u64": 8, "s64": 8}
STATUS = ("confirmed", "unconfirmed")
HOW = ("capture", "diff", "perturbation", "code")
BANNED_KEYS = {"text", "dialog", "dialogue", "rom_text", "string", "strings"}
ADDR_KEYS = {"at", "off", "start", "size", "base", "addr", "table"}
MAX_STR = 80
TOP_REQUIRED = ("format", "game", "system", "rom", "memory_regions", "sources")
TOP_OPTIONAL = ("pointers", "values", "structs", "entities", "flags", "rom_tables")


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def is_hex(x):
    return isinstance(x, str) and bool(HEX.match(x))


class Checker:
    def __init__(self):
        self.errors = []

    def err(self, path, msg):
        self.errors.append("%s: %s" % (path, msg))

    def keys(self, obj, path, required=(), optional=()):
        if not isinstance(obj, dict):
            self.err(path, "must be an object")
            return False
        for k in required:
            if k not in obj:
                self.err(path, "missing required key '%s'" % k)
        for k in obj:
            if k not in required and k not in optional:
                self.err(path, "unknown key '%s'" % k)
        return True

    def hexval(self, v, path):
        if not is_hex(v):
            self.err(path, "must be a hex address string like 0x02000000")

    def posint(self, v, path):
        if not is_int(v) or v < 1:
            self.err(path, "must be an integer >= 1")

    def common(self, e, path):
        if "status" in e and e["status"] not in STATUS:
            self.err(path + ".status", "must be one of %s" % ", ".join(STATUS))
        if "how" in e:
            h = e["how"]
            if not (isinstance(h, list) and h and all(x in HOW for x in h)):
                self.err(path + ".how", "must be a non-empty list from %s" % ", ".join(HOW))

    def at(self, v, path, pointers):
        if isinstance(v, dict):
            self.keys(v, path, ("ptr", "off"))
            if "off" in v:
                self.hexval(v["off"], path + ".off")
            if "ptr" in v and v["ptr"] not in pointers:
                self.err(path + ".ptr", "unknown pointer '%s'" % v["ptr"])
        else:
            self.hexval(v, path)


def walk_content(c, node, path, in_sources, addr_ok):
    """Content rules over every key and string in the map."""
    if isinstance(node, dict):
        for k, v in node.items():
            kl = k.lower()
            if kl in BANNED_KEYS or kl.endswith("_text") or kl.startswith("dialog"):
                c.err(path, "key '%s' looks like game text; not allowed" % k)
            walk_content(c, v, "%s.%s" % (path, k), in_sources or (path == "$" and k == "sources"),
                         k in ADDR_KEYS)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk_content(c, v, "%s[%d]" % (path, i), in_sources, addr_ok)
    elif isinstance(node, str):
        if path.startswith("$.rom.sha1["):
            return
        if SHA1.match(node) or BARE_HEX.match(node):
            c.err(path, "long hex string only allowed as rom.sha1")
        if HEX.match(node) and not (addr_ok or path.startswith("$.pointers.")):
            c.err(path, "hex string only allowed as an address or offset")
        if len(node) > MAX_STR and not in_sources:
            c.err(path, "string longer than %d characters" % MAX_STR)
        if "/home/" in node or "\\Users\\" in node or re.match(r"^[A-Za-z]:\\", node) or "@" in node:
            c.err(path, "looks like a personal path or e-mail address")


def validate_map(d, filename=None):
    """Return a list of error strings (empty if valid). filename is optional."""
    c = Checker()
    if not c.keys(d, "$", TOP_REQUIRED, TOP_OPTIONAL):
        return c.errors
    if d.get("format") != "rammaps/1":
        c.err("$.format", "must be 'rammaps/1'")
    g = d.get("game")
    if not (isinstance(g, str) and g):
        c.err("$.game", "must be a non-empty string")
    s = d.get("system")
    if not (isinstance(s, str) and SYSTEM.match(s)):
        c.err("$.system", "must be a lower-case platform slug")
    if filename is not None:
        p = Path(filename)
        if not SLUG.match(p.name):
            c.err("$", "file name '%s' must be <lower-kebab-title>-<region>.json (usa, europe, japan, ...)" % p.name)
        if isinstance(s, str) and p.parent.name != s:
            c.err("$", "directory '%s' must equal system '%s'" % (p.parent.name, s))

    rom = d.get("rom")
    if c.keys(rom, "$.rom", ("sha1",), ("header_code",)):
        sha = rom.get("sha1")
        if not (isinstance(sha, list) and sha and all(isinstance(x, str) and SHA1.match(x) for x in sha)):
            c.err("$.rom.sha1", "must be a non-empty list of lower-case 40-digit hex strings")
        hc = rom.get("header_code")
        if hc is not None and not (isinstance(hc, str) and re.match(r"^[A-Za-z0-9]{3,6}$", hc)):
            c.err("$.rom.header_code", "must be 3-6 letters/digits")

    regions = d.get("memory_regions")
    if not isinstance(regions, list):
        c.err("$.memory_regions", "must be a list")
    else:
        for i, r in enumerate(regions):
            p = "$.memory_regions[%d]" % i
            if c.keys(r, p, ("name", "start", "size")):
                if not isinstance(r.get("name"), str):
                    c.err(p + ".name", "must be a string")
                c.hexval(r.get("start"), p + ".start")
                c.hexval(r.get("size"), p + ".size")

    pointers = d.get("pointers", {})
    if not isinstance(pointers, dict):
        c.err("$.pointers", "must be an object")
        pointers = {}
    for k, v in pointers.items():
        c.hexval(v, "$.pointers.%s" % k)

    values = d.get("values", {})
    if not isinstance(values, dict):
        c.err("$.values", "must be an object")
        values = {}
    for k, e in values.items():
        p = "$.values.%s" % k
        if c.keys(e, p, ("type", "at"), ("count", "status", "how")):
            if e.get("type") not in INT_SIZE:
                c.err(p + ".type", "must be one of %s" % " ".join(INT_SIZE))
            if "at" in e:
                c.at(e["at"], p + ".at", pointers)
            if "count" in e:
                c.posint(e["count"], p + ".count")
            c.common(e, p)

    structs = d.get("structs", {})
    if not isinstance(structs, dict):
        c.err("$.structs", "must be an object")
        structs = {}
    for k, st in structs.items():
        p = "$.structs.%s" % k
        if not c.keys(st, p, ("size", "fields")):
            continue
        c.hexval(st.get("size"), p + ".size")
        size = int(st["size"], 16) if is_hex(st.get("size")) else None
        fields = st.get("fields")
        if not isinstance(fields, dict):
            c.err(p + ".fields", "must be an object")
            continue
        for fk, f in fields.items():
            fp = "%s.fields.%s" % (p, fk)
            if not c.keys(f, fp, ("type", "off"), ("len", "count", "status", "how")):
                continue
            t = f.get("type")
            if t != "str" and t not in INT_SIZE:
                c.err(fp + ".type", "must be one of %s or str" % " ".join(INT_SIZE))
                continue
            c.hexval(f.get("off"), fp + ".off")
            if "count" in f:
                c.posint(f["count"], fp + ".count")
            if t == "str":
                if "len" not in f:
                    c.err(fp, "str field needs 'len'")
                else:
                    c.posint(f["len"], fp + ".len")
            elif "len" in f:
                c.err(fp, "'len' only allowed on str fields")
            c.common(f, fp)
            if size is not None and is_hex(f.get("off")):
                unit = f["len"] if t == "str" and is_int(f.get("len")) else INT_SIZE.get(t, 1)
                n = f["count"] if is_int(f.get("count")) else 1
                if int(f["off"], 16) + unit * n > size:
                    c.err(fp, "field extends past struct size")

    ents = d.get("entities", {})
    if not isinstance(ents, dict):
        c.err("$.entities", "must be an object")
        ents = {}
    for k, e in ents.items():
        p = "$.entities.%s" % k
        if c.keys(e, p, ("struct", "at", "count"), ("status", "how")):
            if e.get("struct") not in structs:
                c.err(p + ".struct", "unknown struct '%s'" % e.get("struct"))
            if "at" in e:
                c.at(e["at"], p + ".at", pointers)
            if "count" in e:
                c.posint(e["count"], p + ".count")
            c.common(e, p)

    if "flags" in d:
        fl = d["flags"]
        if isinstance(fl, dict) and fl:
            if c.keys(fl, "$.flags", ("base", "bits")):
                c.hexval(fl.get("base"), "$.flags.base")
                c.posint(fl.get("bits"), "$.flags.bits")
        elif not isinstance(fl, dict):
            c.err("$.flags", "must be an object")

    rt = d.get("rom_tables", {})
    if not isinstance(rt, dict):
        c.err("$.rom_tables", "must be an object")
        rt = {}
    for k, t in rt.items():
        p = "$.rom_tables.%s" % k
        if c.keys(t, p, ("count", "stride"), ("addr", "table", "status", "how")):
            if ("addr" in t) == ("table" in t):
                c.err(p, "needs exactly one of 'addr' or 'table'")
            for n in ("addr", "table"):
                if n in t:
                    c.hexval(t[n], "%s.%s" % (p, n))
            c.posint(t.get("count"), p + ".count")
            c.posint(t.get("stride"), p + ".stride")
            c.common(t, p)

    src = d.get("sources")
    if c.keys(src, "$.sources", ("method",), ("acknowledgements",)):
        if not (isinstance(src.get("method"), str) and src["method"]):
            c.err("$.sources.method", "must be a non-empty string")
        acks = src.get("acknowledgements", [])
        if not isinstance(acks, list):
            c.err("$.sources.acknowledgements", "must be a list")
            acks = []
        for i, a in enumerate(acks):
            p = "$.sources.acknowledgements[%d]" % i
            if c.keys(a, p, ("name", "use"), ("urls",)):
                for n in ("name", "use"):
                    if not isinstance(a.get(n), str):
                        c.err("%s.%s" % (p, n), "must be a string")
                urls = a.get("urls", [])
                if not (isinstance(urls, list) and all(isinstance(u, str) and u.startswith("https://") for u in urls)):
                    c.err(p + ".urls", "must be a list of https:// URLs")

    walk_content(c, d, "$", False, False)
    return c.errors


def validate_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        return ["cannot read JSON: %s" % e]
    return validate_map(d, path)


def default_maps():
    return sorted((Path(__file__).resolve().parent.parent / "maps").glob("*/*.json"))


def main(argv):
    paths = argv or [str(p) for p in default_maps()]
    if not paths:
        print("no maps given and none found", file=sys.stderr)
        return 2
    bad = 0
    for p in paths:
        errs = validate_file(p)
        if errs:
            bad += 1
            print("INVALID %s" % p)
            for e in errs:
                print("  " + e)
        else:
            print("ok %s" % p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
