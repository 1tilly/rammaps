# Method notes

How entries in a map are found, for any game in this repository. No game content is reproduced here. The file format is in `schema.md`; the rules for contributing are in `../CONTRIBUTING.md`.

## Finding and checking an address

1. Run the game in an emulator with the maintainers' own legitimately owned ROM and take RAM snapshots at known moments (idle, walking, battle start, menus).
2. Candidates come from diffing snapshots (what changed when a known thing changed), from perturbation (zero a block, see what the game rebuilds), and from reading the game's own machine code to see which addresses it reads and writes.
3. A candidate is kept only if its behaviour holds across repeated captures: a counter rises by a constant per step, a pointer is non-null exactly while a battle exists, a value equals what the screen shows.
4. Where earlier public reverse-engineering work suggested a candidate, it counts only as a lead; the entry stays only if our own captures agree.

## Status of entries

Entries are confirmed by default. An entry is confirmed when it held in every capture where it was exercised and a stated expectation could have failed (for example a level-1 party showing 30/30 HP, or a counter matching a known per-step constant). A candidate that has some evidence but has not passed that test may be published with `"status": "unconfirmed"`; candidates with no evidence are left out. The optional `how` list on an entry says which of capture, diff, perturbation and code reading found it.

## ROM tables

Table locations are file offsets with an entry count and stride. They were found by structural scans (rows with plausible, regular contents) and by changing a row and watching the effect. Contents are not published; a user reads them from their own ROM.

## Pointers

Some objects are not at fixed addresses. A fixed IWRAM word holds a pointer to the object and `at` gives that word plus an offset. Object locations differ between field and battle; read the pointer each time.

## Per game and platform

Each map is tied to the ROM SHA-1 listed in it; other regions and revisions usually have different addresses and need their own map. Address conventions per platform are in `schema.md`. State the byte order and any bank or CPU choice (for example ARM9 or ARM7 on NDS) in `sources.method` the first time a platform is added.

## Limits

The only map so far (Golden Sun, USA) was exercised mostly in the early game, so values that only matter later are less tested. Maps are partial by design.
