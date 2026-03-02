from __future__ import annotations
import pandas as pd

def join_turnos_to_bateas_asof(
    bateas: pd.DataFrame,
    turnos: pd.DataFrame,
    date_bateas: str,
    date_turnos: str,
    turno_col: str,
    tolerance: str = "36h",
) -> pd.DataFrame:
    """
    Strategy:
    - Ensure datetime columns
    - Sort
    - Use merge_asof within each Turno (A/B) to attribute the closest turno record
      to each batea record, constrained by a tolerance.
    This is robust when turnos is at turno/day grain and bateas is at lote/batea grain.

    If your business rule is different (e.g., start-end window overlap), implement
    an interval join instead.
    """
    b = bateas.copy()
    t = turnos.copy()
    b[date_bateas] = pd.to_datetime(b[date_bateas], errors="coerce")
    t[date_turnos] = pd.to_datetime(t[date_turnos], errors="coerce")

    b = b.sort_values([turno_col, date_bateas])
    t = t.sort_values([turno_col, date_turnos])

    out = pd.merge_asof(
        b,
        t,
        left_on=date_bateas,
        right_on=date_turnos,
        by=turno_col,
        direction="nearest",
        tolerance=pd.Timedelta(tolerance),
        suffixes=("", "_turno")
    )
    return out
