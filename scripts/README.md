# scripts

- `validate.py MAP.json [...]` checks maps against the `rammaps/1` rules (see `docs/schema.md`). With no arguments it checks every `maps/*/*.json`. Exits non-zero on any error.
- `gen_index.py` regenerates the games table in the top-level `README.md` from the maps. `--check` exits non-zero if the table is out of date.
- `export_gs1.py` is the **Golden Sun exporter** only. It turns a maintainers' profile JSON (format not published) into `maps/gba/golden-sun-usa.json`. It is not a general tool; other games are written by hand or with their own exporter.

All scripts use only the Python standard library. Run them as `python3 -I scripts/<name>.py`.
