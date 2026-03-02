from __future__ import annotations
import pandas as pd
import numpy as np

TURN_A_START_H = 8
TURN_A_END_H = 20

def _to_dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")

def add_batea_time_window(df_bateas: pd.DataFrame) -> pd.DataFrame:
    """Define ventana operacional de lixiviación por batea.
    - timestamp_end: fecha_rebose
    - timestamp_start: fecha_rebose - tiempo_de_lixiviacion_h (horas)
    """
    df = df_bateas.copy()
    df["fecha_rebose"] = _to_dt(df["fecha_rebose"])
    # prefer 'tiempo_de_lixiviacion_h' if present; fallback to 'horas_de_lixiviacion'
    hcol = "tiempo_de_lixiviacion_h" if "tiempo_de_lixiviacion_h" in df.columns else "horas_de_lixiviacion"
    df[hcol] = pd.to_numeric(df[hcol], errors="coerce")
    df["timestamp_end"] = df["fecha_rebose"]
    df["timestamp_start"] = df["fecha_rebose"] - pd.to_timedelta(df[hcol], unit="h")
    return df

def build_turno_intervals(df_turnos: pd.DataFrame) -> pd.DataFrame:
    """Construye intervalos inicio-fin de turnos A/B (12h) a partir de columna dia (YYYY-MM-DD)."""
    df = df_turnos.copy()
    df["dia"] = pd.to_datetime(df["dia"], errors="coerce").dt.floor("D")
    df["turno"] = df["turno"].astype(str).str.upper().str.strip()

    # Start/end timestamps per shift
    start = []
    end = []
    for d, t in zip(df["dia"], df["turno"]):
        if pd.isna(d):
            start.append(pd.NaT); end.append(pd.NaT); continue
        if t == "A":
            s = d + pd.Timedelta(hours=TURN_A_START_H)
            e = d + pd.Timedelta(hours=TURN_A_END_H)
        else:
            # Turno B: 20:00 to next day 08:00
            s = d + pd.Timedelta(hours=TURN_A_END_H)
            e = (d + pd.Timedelta(days=1)) + pd.Timedelta(hours=TURN_A_START_H)
        start.append(s); end.append(e)
    df["turno_start"] = start
    df["turno_end"] = end
    df["turno_hours"] = (df["turno_end"] - df["turno_start"]).dt.total_seconds() / 3600.0
    return df

def _overlap_hours(a0, a1, b0, b1) -> float:
    latest_start = max(a0, b0)
    earliest_end = min(a1, b1)
    if earliest_end <= latest_start:
        return 0.0
    return (earliest_end - latest_start).total_seconds() / 3600.0

def attach_turno_features(
    df_bateas_tw: pd.DataFrame,
    df_turnos_iv: pd.DataFrame,
    features_mean: list[str] | None = None,
    features_sum: list[str] | None = None,
) -> pd.DataFrame:
    """Agrega features de 'turnos' sobre la ventana [timestamp_start, timestamp_end] de cada batea.
    - Para variables de operación continua (flujos, pH): promedio ponderado por horas de solapamiento.
    - Para base masa (tms_x_turno): suma proporcional por horas de solapamiento.
    - Para dosis ácido (kg/t): promedio ponderado por horas (y además se deja una proxy total_acid_index = mean * tms_sum si ambas existen).
    """
    df_b = df_bateas_tw.copy()
    df_t = df_turnos_iv.copy()

    if features_mean is None:
        # default continuous variables (ignore non-numeric)
        features_mean = [c for c in df_t.columns if c not in ("dia","turno","turno_start","turno_end","turno_hours")]
        # prefer these as mean, excluding tms_x_turno (sum)
        if "tms_x_turno" in features_mean:
            features_mean.remove("tms_x_turno")
    if features_sum is None:
        features_sum = []
        if "tms_x_turno" in df_t.columns:
            features_sum.append("tms_x_turno")

    # Ensure numeric for features
    for c in set(features_mean + features_sum):
        df_t[c] = pd.to_numeric(df_t[c], errors="coerce")

    out_rows = []
    for idx, r in df_b.iterrows():
        w0, w1 = r["timestamp_start"], r["timestamp_end"]
        if pd.isna(w0) or pd.isna(w1):
            out_rows.append({}); continue

        # candidate shifts overlapping window
        mask = (df_t["turno_end"] > w0) & (df_t["turno_start"] < w1)
        cand = df_t.loc[mask].copy()
        if cand.empty:
            out_rows.append({}); continue

        # overlap weights
        cand["ov_h"] = [
            _overlap_hours(w0, w1, a0, a1)
            for a0, a1 in zip(cand["turno_start"], cand["turno_end"])
        ]
        total_h = cand["ov_h"].sum()
        if total_h <= 0:
            out_rows.append({}); continue

        feats = {}
        # weighted means
        for c in features_mean:
            x = cand[c].to_numpy(dtype=float)
            w = cand["ov_h"].to_numpy(dtype=float)
            m = np.nan
            if np.isfinite(x).any():
                # ignore nans in x by zeroing weights
                ww = w.copy()
                ww[~np.isfinite(x)] = 0.0
                if ww.sum() > 0:
                    m = np.sum(x * ww) / ww.sum()
            feats[f"turno_mean__{c}"] = m

        # proportional sums
        for c in features_sum:
            x = cand[c].to_numpy(dtype=float)
            w = cand["ov_h"].to_numpy(dtype=float)
            s = np.nan
            if np.isfinite(x).any():
                # scale by overlap fraction of 12h shift
                # use turno_hours (should be 12)
                denom = cand["turno_hours"].to_numpy(dtype=float)
                frac = np.where(denom>0, w/denom, 0.0)
                s = np.nansum(x * frac)
            feats[f"turno_sum__{c}"] = s

        feats["window_hours"] = float(total_h)
        out_rows.append(feats)

    df_feats = pd.DataFrame(out_rows, index=df_b.index)
    df_out = pd.concat([df_b, df_feats], axis=1)

    # convenience derived indices
    if "turno_sum__tms_x_turno" in df_out.columns and "turno_mean__dosificacion_acido_x_dia_kg_tms" in df_out.columns:
        df_out["acid_index_kg"] = df_out["turno_sum__tms_x_turno"] * df_out["turno_mean__dosificacion_acido_x_dia_kg_tms"]
    return df_out
