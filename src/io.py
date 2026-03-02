from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def _project_path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


def read_csv_safely(path: Path, **kwargs) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path} (cwd={Path.cwd()})")
    return pd.read_csv(path, **kwargs)


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Lower snake_case, remove double spaces, keep ascii-ish where possible
    cols = []
    for c in df.columns:
        c2 = str(c).strip().lower()
        c2 = re.sub(r"\s+", "_", c2)
        c2 = c2.replace("%", "pct")
        c2 = re.sub(r"[^0-9a-zA-Z_]+", "_", c2)
        c2 = re.sub(r"_+", "_", c2).strip("_")
        cols.append(c2)
    df = df.copy()
    df.columns = cols
    return df


@dataclass
class CoerceReport:
    column: str
    n_total: int
    n_non_null_before: int
    n_numeric_after: int
    n_new_nan: int

    @property
    def success_rate(self) -> float:
        denom = max(self.n_non_null_before, 1)
        return self.n_numeric_after / denom


_NUM_CLEAN_RE = re.compile(r"[^0-9,\.\-]+")


def _clean_numeric_series(s: pd.Series) -> pd.Series:
    # Keep original as string, strip, remove thousand sep, normalize decimal comma.
    x = s.astype(str).str.strip()

    # Common missing markers
    x = x.replace({"": pd.NA, "nan": pd.NA, "none": pd.NA, "null": pd.NA, "-": pd.NA})

    # Remove percent sign / units / spaces, keep digits, comma, dot, minus
    x = x.str.replace(_NUM_CLEAN_RE, "", regex=True)

    # If it contains both '.' and ',', assume '.' is thousand sep and ',' decimal (common LATAM)
    both = x.str.contains(r"\.") & x.str.contains(",")
    x.loc[both] = x.loc[both].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)

    # If it contains only ',', treat as decimal comma
    only_comma = x.str.contains(",") & (~x.str.contains(r"\."))
    x.loc[only_comma] = x.loc[only_comma].str.replace(",", ".", regex=False)

    return x


def coerce_numeric_columns(df: pd.DataFrame, cols: list[str], keep_raw: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    reports: list[CoerceReport] = []

    for col in cols:
        if col not in df.columns:
            continue

        before = df[col]
        n_total = len(before)
        n_non_null = int(before.notna().sum())

        if keep_raw and f"{col}__raw" not in df.columns:
            df[f"{col}__raw"] = before

        # Already numeric?
        if pd.api.types.is_numeric_dtype(before):
            n_numeric_after = int(before.notna().sum())
            reports.append(CoerceReport(col, n_total, n_non_null, n_numeric_after, 0))
            continue

        cleaned = _clean_numeric_series(before)
        numeric = pd.to_numeric(cleaned, errors="coerce")
        df[col] = numeric

        n_numeric_after = int(numeric.notna().sum())
        n_new_nan = max(n_non_null - n_numeric_after, 0)
        reports.append(CoerceReport(col, n_total, n_non_null, n_numeric_after, n_new_nan))

    rep_df = pd.DataFrame([r.__dict__ | {"success_rate": r.success_rate} for r in reports])
    return df, rep_df


def parse_date_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def read_bateas_raw() -> pd.DataFrame:
    path = _project_path("data", "raw", "bateas.csv")
    df = read_csv_safely(path)
    df = standardize_columns(df)
    # Try to parse canonical date columns if present
    df = parse_date_columns(df, ["fecha", "fecha_rebose", "rebose_fecha", "timestamp"])
    return df


def read_turnos_raw() -> pd.DataFrame:
    path = _project_path("data", "raw", "turnos.csv")
    df = read_csv_safely(path)
    df = standardize_columns(df)
    df = parse_date_columns(df, ["fecha", "timestamp", "inicio_turno", "fin_turno"])
    return df


def write_processed(df: pd.DataFrame, name: str) -> Path:
    out_dir = _project_path("data", "processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / name
    df.to_csv(out_path, index=False)
    return out_path
