import pandas as pd
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class CleaningRule:
    name: str
    mask: pd.Series

def technical_cleaning_audit(
    df: pd.DataFrame,
    *,
    col_rec: str = "pctrec_cusac",
    col_p80: str = "p80_mm",
    col_tms: str = "tms",
    col_tl: str = "tiempo_de_lixiviacion_h",
    col_fecha: str = "fecha_rebose",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Limpieza técnica (auditada):
      - NO borra silenciosamente: devuelve tabla de impacto por regla + totales.
      - Aplica filtros obligatorios del usuario.
    """

    df0 = df.copy()
    n_before = int(len(df0))

    rules = [
        CleaningRule("recuperacion NaN", df0[col_rec].isna()),
        CleaningRule("p80 NaN", df0[col_p80].isna()),
        CleaningRule("tms NaN", df0[col_tms].isna()),
        CleaningRule("tiempo_lixiviacion <= 0", df0[col_tl].le(0) | df0[col_tl].isna()),
        CleaningRule("fecha_rebose NaT", df0[col_fecha].isna()),
    ]

    # Impact per rule (overlaps allowed)
    impact = []
    removal_mask = pd.Series(False, index=df0.index)

    for r in rules:
        affected = int(r.mask.sum())
        impact.append({
            "motivo": r.name,
            "filas_afectadas": affected,
        })
        removal_mask |= r.mask

    df_clean = df0.loc[~removal_mask].copy()
    n_after = int(len(df_clean))
    removed = n_before - n_after
    pct_removed = (removed / n_before * 100.0) if n_before else 0.0

    impact_df = pd.DataFrame(impact)
    impact_df["filas_antes"] = n_before
    impact_df["filas_despues"] = n_after
    impact_df["filas_eliminadas_total"] = removed
    impact_df["%_eliminado_total"] = pct_removed

    # Add totals row (useful for reporting)
    totals = pd.DataFrame([{
        "motivo": "TOTAL (unión de reglas)",
        "filas_afectadas": int(removal_mask.sum()),
        "filas_antes": n_before,
        "filas_despues": n_after,
        "filas_eliminadas_total": removed,
        "%_eliminado_total": pct_removed
    }])

    impact_df = pd.concat([impact_df, totals], ignore_index=True)

    return df_clean, impact_df
