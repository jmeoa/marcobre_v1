from __future__ import annotations
from pathlib import Path
import pandas as pd

def project_root() -> Path:
    # index.qmd lives at project root; this keeps paths stable in Codespaces + local.
    return Path(__file__).resolve().parents[1]

def data_dir() -> Path:
    return project_root() / "data"

def read_bateas_raw() -> pd.DataFrame:
    return pd.read_csv(data_dir() / "raw" / "bateas.csv")

def read_turnos_raw() -> pd.DataFrame:
    return pd.read_csv(data_dir() / "raw" / "turnos.csv")

def write_processed(df: pd.DataFrame, name: str) -> Path:
    out = data_dir() / "processed" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out
