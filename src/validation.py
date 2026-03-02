import pandas as pd
from dataclasses import dataclass
from typing import Tuple

@dataclass
class RangeRule:
    name: str
    col: str
    low: float
    high: float
    unit: str

def add_month(df: pd.DataFrame, col_fecha: str) -> pd.Series:
    return pd.to_datetime(df[col_fecha]).dt.to_period("M").astype(str)

def _to_numeric_series(s: pd.Series) -> pd.Series:
    """
    Conversión robusta a numérico:
    - Reemplaza coma decimal por punto
    - Remueve % y espacios típicos
    - Coerciona errores a NaN (trazable)
    """
    if pd.api.types.is_numeric_dtype(s):
        return s

    s2 = s.astype("string")
    s2 = s2.str.replace("%", "", regex=False)
    s2 = s2.str.replace(" ", "", regex=False)
    s2 = s2.str.replace(",", ".", regex=False)  # decimal comma -> dot
    return pd.to_numeric(s2, errors="coerce")

def metallurgical_validation_flags(
    df: pd.DataFrame,
    *,
    col_p80: str = "p80_mm",
    col_c: str = "pctc",
    col_rec: str = "pctrec_cusac",
    col_tms: str = "tms",
    col_tl: str = "tiempo_de_lixiviacion_h",
    col_fecha: str = "fecha_rebose",
    tl_low: float = 1.0,
    tl_high: float = 240.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validación metalúrgica: NO elimina automáticamente.
    Crea flags por variable y un flag_outlier consolidado.
    Devuelve cuantificación por OXI y por mes.
    """

    dfv = df.copy()

    # ✅ coerción numérica explícita (evita TypeError y hace trazable lo inválido)
    for c in [col_p80, col_c, col_rec, col_tms, col_tl]:
        if c in dfv.columns:
            dfv[c] = _to_numeric_series(dfv[c])

    rules = [
        RangeRule("P80 fuera de rango", col_p80, 2.0, 25.0, "mm"),
        RangeRule("%C fuera de rango", col_c, 0.0, 5.0, "%"),
        RangeRule("Recuperación fuera de rango", col_rec, 0.0, 100.0, "%"),
        RangeRule("Tiempo lixiviación fuera de rango", col_tl, tl_low, tl_high, "h"),
    ]

    # Individual flags
    for r in rules:
        dfv[f"flag__{r.col}"] = ~dfv[r.col].between(r.low, r.high)

    # Special (TMS > 0)
    dfv["flag__tms"] = dfv[col_tms].le(0) | dfv[col_tms].isna()

    flag_cols = [c for c in dfv.columns if c.startswith("flag__")]
    dfv["flag_outlier"] = dfv[flag_cols].any(axis=1)

    # Month
    dfv["mes"] = add_month(dfv, col_fecha)

    # Ensure OXI exists
    if "oxi_dominante" not in dfv.columns:
        dfv["oxi_dominante"] = "SIN_OXI"

    summary = (
        dfv.groupby(["oxi_dominante", "mes"], dropna=False)
           .agg(
               n=("flag_outlier", "size"),
               n_outliers=("flag_outlier", "sum"),
               pct_outliers=("flag_outlier", "mean"),
           )
           .reset_index()
    )
    summary["pct_outliers"] = summary["pct_outliers"] * 100.0

    # Flags by cause (drilldown)
    flag_long = []
    for r in rules:
        flag_long.append(
            dfv.groupby(["oxi_dominante","mes"])[f"flag__{r.col}"].mean().rename(r.name)
        )
    flag_long.append(
        dfv.groupby(["oxi_dominante","mes"])["flag__tms"].mean().rename("TMS <= 0")
    )
    flags_by_cause = pd.concat(flag_long, axis=1).reset_index()
    for c in flags_by_cause.columns:
        if c not in ("oxi_dominante","mes"):
            flags_by_cause[c] = flags_by_cause[c] * 100.0

    return dfv, summary.merge(flags_by_cause, on=["oxi_dominante","mes"], how="left")
