# Marcobre Bateas — Quarto EDA (Fase 0)

Este repo genera un reporte HTML reproducible (Quarto) para auditoría de datos y EDA.

## Estructura
- `data/raw/` : inputs (bateas.csv, turnos.csv)
- `data/processed/` : outputs procesados (se generan al render)
- `src/` : funciones para ventanas operacionales y agregación de turnos
- `index.qmd` : reporte principal
- `.devcontainer/` : configuración para GitHub Codespaces

## Ejecutar en Codespaces
1. Abrir el repo en Codespaces.
2. Esperar `postCreateCommand` (instala dependencias + Quarto).
3. Render:
   - `quarto render` (genera `_site/`)
   - o `quarto preview --no-watch-inputs --no-browse`

## Ejecutar local
- Crear venv, instalar `requirements.txt`
- Instalar Quarto (https://quarto.org)
- Render: `quarto preview index.qmd`
