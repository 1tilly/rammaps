# Schema: `rammaps/1`

A map is one JSON file at `maps/<platform>/<game-slug>.json`. `schema/rammaps-1.schema.json` is the machine-readable JSON Schema; `scripts/validate.py` checks the same rules plus a few that JSON Schema cannot express (cross references, struct bounds, content rules). Where they differ, `validate.py` is stricter.

A map holds addresses, offsets, sizes and field names only. Never ROM bytes, game text, graphics, audio, decompiled code or save data.

## Value kinds

- **address / offset / size**: a hex string `"0x"` followed by 1 to 16 hex digits, for example `"0x02000250"`. Hex strings are allowed only in address positions (`at`, `off`, `start`, `size`, `base`, `addr`, `table`, and the values of `pointers`). Counts, strides and bit counts are plain JSON integers.
- **type**: one of `u8 s8 u16 s16 u32 s32 u64 s64`. Struct fields may also use `str`.
- **pointer form** (an `at` that is not fixed): `{"ptr": "<name in pointers>", "off": "<offset>"}`. Read the 32-bit pointer stored at the address `pointers[<name>]`, then add `off`. The named pointer must exist.
- **status**: `"confirmed"` or `"unconfirmed"`, optional on any entry, default `"confirmed"`.
- **how**: optional array naming how an entry was found, from `capture`, `diff`, `perturbation`, `code`. See `CONTRIBUTING.md`.

## Top-level keys

| key | required | content |
|---|---|---|
| `format` | yes | the string `"rammaps/1"` |
| `game` | yes | display title, at most 80 characters |
| `system` | yes | platform slug, lower case (`gba`, `nes`, `snes`, `nds`, `gb`, `gbc`, `n64`, `psx`, ...). Must equal the directory name under `maps/`. |
| `rom` | yes | identifies the ROM the addresses were verified on, see below |
| `memory_regions` | yes | array of `{"name", "start", "size"}`, all hex strings except `name` |
| `sources` | yes | method and acknowledgements, see below |
| `pointers` | no | object: name to address of a 32-bit pointer word |
| `values` | no | object: name to value entry |
| `structs` | no | object: name to struct layout |
| `entities` | no | object: name to array-of-records entry |
| `flags` | no | bitfield description, or `{}` |
| `rom_tables` | no | object: name to ROM table location |

Unknown top-level keys are rejected.

### `rom`

- `sha1` (required): non-empty array of lower-case 40-digit hex strings, the SHA-1 of every ROM image the map was verified against. This is the only 40-hex string allowed anywhere in a map.
- `header_code` (optional): the cartridge/game code from the header, 3 to 6 letters or digits (for example the four-letter GBA game code).

### `values`

Each entry: `type` (required), `at` (required, address or pointer form), `count` (optional integer, makes it an array of that many elements), `status`, `how`.

### `structs`

`structs.<name>` has `size` (required, hex) and `fields` (required, object). Each field: `type` (required, includes `str`), `off` (required, hex, relative to the record start), `count` (optional, array), `len` (required for `str`, forbidden otherwise: byte length of the fixed-size field), `status`, `how`. A `str` field lists only its offset and length, never its contents. `validate.py` checks that every field ends within `size`.

### `entities`

Arrays of records. Each entry: `struct` (required, must name a struct), `at` (required, address or pointer form), `count` (required integer, at least 1), `status`, `how`.

### `flags`

A bitfield: `base` (hex address) and `bits` (positive integer). Flag n is bit n%8 of the byte at `base + n/8`. Individual flag meanings are not part of the format. `{}` means none.

### `rom_tables`

Locations in the ROM file (not in RAM). Each entry: exactly one of `addr` or `table` (hex file offset; the two names are equivalent), `count` (integer), `stride` (bytes, integer), `status`, `how`. Layout only; the table contents are never published.

### `sources`

- `method` (required): one or two sentences on how the addresses were found.
- `acknowledgements` (optional): array of `{"name", "use", "urls"}`, where `urls` is an array of `https://` links. Say exactly what was taken from each (a lead, a cross-check) and what was not (tables, text, code).

`sources` is the only place where strings may exceed 80 characters. Every other string is at most 80 characters.

## Status and confirmed semantics

- **confirmed** (the default): the entry held in every capture where it was exercised, and a stated expectation could have failed (a level-1 party showing 30/30 HP, a counter matching a known per-step constant). Third-party leads count only after they agree with our own captures.
- **unconfirmed**: a candidate with some evidence that has not passed that test. It must carry `"status": "unconfirmed"`. Consumers should not rely on it.
- Candidates with no evidence at all are not published.

## Address-space conventions

Addresses are those the emulated CPU uses on its own bus, written in full. Ranges below are the main RAM areas; map only what you verified. Only GBA has a map so far; the other rows are the intended conventions and will be tightened when the first map for that platform arrives.

| platform | convention |
|---|---|
| `gba` | EWRAM `0x02000000` (256 KiB), IWRAM `0x03000000` (32 KiB), I/O `0x04000000`, palette `0x05000000`, VRAM `0x06000000`, OAM `0x07000000`. ROM file offsets are separate from the `0x08000000` bus mapping: `rom_tables` use file offsets. |
| `nds` | ARM9 bus addresses: main RAM `0x02000000` (4 MiB). Say in `sources.method` if ARM7 addresses are used. |
| `nes` | CPU bus: internal RAM `0x0000` to `0x07FF`, cartridge RAM `0x6000` to `0x7FFF`. |
| `snes` | 24-bit bus: WRAM `0x7E0000` to `0x7FFFFF`. Use bank-qualified addresses. |
| `gb`, `gbc` | CPU bus: WRAM `0xC000` to `0xDFFF` (GBC banked area: state the bank in the memory region name), HRAM `0xFF80` to `0xFFFE`. |
| `n64` | KSEG0 virtual addresses, RDRAM `0x80000000` (4 or 8 MiB). |
| `psx` | KSEG0 virtual addresses, main RAM `0x80000000` (2 MiB). |

Multi-byte values use the CPU's native byte order: little-endian on gba, nds, nes, snes, gb, gbc and psx, big-endian on n64. State it in `sources.method` when a platform is first added.

## Minimal example

The `sha1` placeholder must be replaced by a real digest.

```json
{
 "format": "rammaps/1",
 "game": "Example Game",
 "system": "gba",
 "rom": {"sha1": ["<40 lower-case hex digits>"], "header_code": "AAAA"},
 "memory_regions": [{"name": "ewram", "start": "0x02000000", "size": "0x40000"}],
 "values": {"coins": {"type": "u32", "at": "0x02000250", "how": ["capture", "diff"]}},
 "sources": {"method": "Found by diffing RAM captures before and after buying an item."}
}
```
