from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

@dataclass(frozen=True)
class DataPaths:
    data_dir: Path
    bateas_file: str
    turnos_file: str

    @property
    def bateas_path(self) -> Path:
        return self.data_dir / self.bateas_file

    @property
    def turnos_path(self) -> Path:
        return self.data_dir / self.turnos_file


def read_csv_safely(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {path}\n"
            f"Asegúrate de copiarlo a esa ruta o ajustar params.data_dir / params.*_file en _quarto.yml"
        )
    return pd.read_csv(path)


def to_datetime(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = df.copy()
    df[col] = pd.to_datetime(df[col], errors="coerce")
    return df
