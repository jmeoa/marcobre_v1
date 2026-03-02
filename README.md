# Marcobre Bateas — Fase 0 (EDA + Data Quality) — Quarto (Codespaces-ready)

This repo is a **reproducible** Quarto project to:
- Validate **completeness + quality** of the database (Bateas + Turnos)
- Build **operational windows** and **multivariable drivers** for recovery
- Answer standard questions by **OXI**, time, and operating conditions

## Quick start (GitHub Codespaces)
1. Create a repo in GitHub and upload this template (or unzip + push).
2. Open the repo in **Codespaces** (it will build the devcontainer).
3. Put your CSVs into `data/` (see below).
4. Render:
   ```bash
   quarto render
   ```
5. Preview locally in Codespaces:
   ```bash
   quarto preview --to html --no-watch-inputs --no-browse
   ```

## Expected inputs
Place files in `data/`:

- `bateas.csv` (lote/batea grain) — must contain at least:
  - `fecha` (date or datetime)
  - `turno` (A/B or equivalent)
  - `batea_id` or `id_lote` (unique lot id)
  - `oxi` (OXI2 / OXI3 / OXI3M / OXI4 / OXI4M)
  - `toneladas` (treated)
  - optional: `c_total`, `carbonatos`, `p80`, `recuperacion`, etc.

- `turnos.csv` (turno/day grain) — must contain at least:
  - `fecha` (date or datetime)
  - `turno` (A/B)
  - process / SX / EW / hydraulic / chemistry variables (see `docs/data_request_sx_ew.md`)

You can keep your original filenames and set them in `_quarto.yml` (see `params:` section) or via env vars.

## Outputs
Rendered artifacts go to `_site/` (HTML), and key intermediate tables to `out/`.

## Repo structure
- `report/` : QMD chapters
- `src/` : Python utilities (schema, QA, joins, plots)
- `data/` : input CSVs (gitignored)
- `out/` : exported intermediate tables (gitignored)
