#!/usr/bin/env python3
"""Golden Sun exporter: writes addresses and struct layouts (no ROM data, no text,
no graphics) for Golden Sun (USA, GBA) from a profile JSON.

This script is specific to Golden Sun; other games need their own exporter or
hand-written maps (see CONTRIBUTING.md).

usage: python3 -I export_gs1.py PROFILE.json > maps/gba/golden-sun-usa.json

Only entries the profile marks as confirmed (checked on our own captures) are
exported. Game-derived text in the profile (names, hints, dialog) is never read.
"""
import json
import sys

POINTERS = ("battle_work", "ui_render", "event_work", "map_work", "player_ptr")
# party_order is deliberately absent: it rests on a third-party lead with no capture of our own.
VALUES = ("coins", "party_flags", "ready_flag", "scene", "encounter_steps", "encounter_threshold",
          "encounter_groups", "encounter_bias", "encounter_group", "battle_request", "enemy_group",
          "rng_field")
ENTITIES = ("party", "enemies")
# struct field -> profile confirmation key that must be true for it to be exported
UNIT_FIELDS = {"name": "party.stats", "level": "party.stats", "hp_max": "party.stats",
               "pp_max": "party.stats", "hp": "party.stats", "pp": "party.stats",
               "exp": "party.exp", "elements": "party.elements", "class": "enemy.class"}
RENAME = {"ready_flag": "story_flags_0x20_0x27"}  # that byte holds story flags, not a ready signal

SOURCES = {
    "method": "Addresses were located or checked by the maintainers with emulator RAM captures, "
              "perturbation tests and reading the game's own code on a legitimately owned ROM.",
    "acknowledgements": [
        {"name": "PascalPixel/alchemy, Coaltergeist/goldensun-decomp, kaptanultros/GoldenSun_GSTLA_StatDisplay",
         "use": "some offsets were first suggested by these projects and then re-verified on our own "
                "captures; none of their tables, text or code were copied",
         "urls": ["https://github.com/PascalPixel/alchemy",
                  "https://github.com/Coaltergeist/goldensun-decomp",
                  "https://github.com/kaptanultros/GoldenSun_GSTLA_StatDisplay"]},
        {"name": "Golden Sun Universe wiki (CC BY-SA 4.0), Zombie page",
         "use": "cross-check of element resistances only; no content copied",
         "urls": ["https://goldensunwiki.net/wiki/Zombie"]},
    ],
}


def main():
    d = json.load(open(sys.argv[1]))
    conf = d.get("confirmed", {})
    ok = lambda key: bool(conf.get(key))
    values = {RENAME.get(k, k): {x: v[x] for x in ("type", "at", "count") if x in v}
              for k, v in d["values"].items() if k in VALUES and ok(v.get("confirmed"))}
    entities = {k: {x: v[x] for x in ("struct", "at", "count") if x in v}
                for k, v in d["entities"].items() if k in ENTITIES and ok(v.get("confirmed"))}
    unit = d["structs"]["unit"]
    structs = {"unit": {"size": unit["size"],
                        "fields": {k: v for k, v in unit["fields"].items()
                                   if ok(UNIT_FIELDS.get(k))}}}
    # only the base and size of the story bitfield; named flags are not exported
    flags = {x: d["flags"][x] for x in ("base", "bits")} if ok("party.membership") else {}
    rom_tables = {}
    if ok("rom.tables"):
        rom_tables["zones"] = {x: d["rom_tables"]["zones"][x] for x in ("addr", "count", "stride")}
    if ok("rom.items"):
        rom_tables["items"] = {x: d["rom_items"][x] for x in ("table", "stride", "count")}
    out = {
        "format": "rammaps/1", "game": d["game"], "system": d["system"],
        "rom": {"sha1": d["match"]["sha1"], "header_code": d["match"].get("header_code")},
        "memory_regions": d["memory"]["regions"],
        "pointers": {k: d["pointers"][k] for k in POINTERS},
        "values": values,
        "structs": structs,
        "entities": entities,
        "flags": flags,
        "rom_tables": rom_tables,
        "sources": SOURCES,
    }
    json.dump(out, sys.stdout, indent=1)
    print()


main()
