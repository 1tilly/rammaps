# Contributing

Thank you for adding to rammaps. This repository holds address maps only: where things live in a game's RAM and ROM, never the content itself. Read `docs/schema.md` (format) and `docs/method.md` (how entries are found) first.

## Adding a map

1. Use a ROM you legitimately own. Do not share it, and do not send it to us.
2. Create `maps/<platform>/<game-slug>.json`.
   - `<platform>` is a lower-case slug: `gba`, `nes`, `snes`, `nds`, `gb`, `gbc`, `n64`, `psx`, and so on. It must equal the map's `system`.
   - `<game-slug>` is the lower-kebab-case title plus the region: `golden-sun-usa`, `golden-sun-the-lost-age-usa`, `fire-emblem-the-sacred-stones-usa`. Allowed regions: `usa`, `europe`, `japan`, `world`, `korea`, `australia`, `germany`, `france`, `spain`, `italy`. One file per ROM release; no hashes in the name, the SHA-1 goes inside under `rom.sha1`.
3. Fill in the format described in `docs/schema.md`. Start from the minimal example there.
4. Run `python3 -I scripts/validate.py maps/<platform>/<game-slug>.json`, then `python3 -I scripts/gen_index.py` to refresh the README table, then `python3 -I -m unittest discover tests`.
5. Open a merge request with the map, the regenerated README table, and a description of how you found the entries.

## Evidence and provenance are required

Every entry must be backed by evidence you can describe, and the description goes in the merge request and in the entry's `how` list (`capture`, `diff`, `perturbation`, `code`) plus `sources.method`.

- **How it was found**: your own RAM capture, snapshot diff, perturbation (change a value or zero a block and watch what the game does), or reading the game's machine code on your own ROM.
- **Say what could have failed.** An entry is confirmed only if a stated expectation could have gone wrong and did not (a level-1 party showing 30/30 HP, a counter that rises by a fixed amount per step). "It looked right once" is not enough.
- **Third-party leads are leads only.** An address from a wiki, a decompilation project, a cheat list or another map counts as a suggestion. It becomes an entry only after it holds on your own captures. Credit it under `sources.acknowledgements` and say exactly what you took (an offset to test) and what you did not.
- The existing Golden Sun map predates per-entry `how`; its provenance is recorded map-wide in `sources`. New maps should record it per entry.

## Confirmed and unconfirmed

Entries are `"confirmed"` unless marked otherwise. Mark a candidate `"status": "unconfirmed"` if it has some evidence but has not passed a test that could have failed. Do not publish candidates with no evidence. Promote an entry by removing the status once the test has been done, and say how in the merge request.

## What must never be added

- ROM bytes, or anything from which they can be rebuilt: no dumps, byte strings, tables of contents.
- Game text of any kind: no dialog, names lists, item or enemy name tables, string dumps. A `str` field records only its offset and length. `validate.py` rejects keys such as `text` or `dialog`, strings over 80 characters outside `sources`, and hex strings that are not addresses.
- Graphics, audio, video or save data.
- Decompiled or disassembled code, and tables or offsets lists copied from third parties, unless their licence is compatible with CC0 for data and they are credited. When in doubt, treat it as a lead and re-derive it.

## Licences

Data (maps, docs, schema) is CC0 1.0; scripts and tests are MIT. By contributing you agree your contribution is released under the licence of the directory it goes in. See `LICENSE`.

## Review checklist

- [ ] Filename and directory follow the naming rule; `system` matches the directory
- [ ] `python3 -I scripts/validate.py` passes, README table regenerated, tests pass
- [ ] `rom.sha1` is the only 40-digit hex string; it matches the ROM you used
- [ ] Every entry has evidence you can describe; confirmed entries had a test that could have failed
- [ ] Third-party leads re-verified and credited, with what was and was not taken
- [ ] No ROM bytes, game text, names dumps, graphics, audio, save data or copied code
- [ ] No personal paths, host names, IP addresses, e-mail addresses or tokens anywhere in the change, including the merge request text and commit metadata
- [ ] Addresses follow the platform conventions in `docs/schema.md`

## Security and privacy

Check your files before committing. Maps, descriptions and commit messages must not contain home-directory paths, machine or host names, IP addresses, e-mail addresses or credentials. Use a no-reply commit address.

## Conduct

Be kind and assume good faith. A formal code of conduct may be added later.
