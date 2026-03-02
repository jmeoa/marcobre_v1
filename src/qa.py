from __future__ import annotations
import pandas as pd
import numpy as np

def completeness_table(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    out = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(t) for t in df.dtypes],
        "non_null": [df[c].notna().sum() for c in df.columns],
    })
    out["null"] = n - out["non_null"]
    out["pct_non_null"] = (out["non_null"] / max(n, 1)).round(4)
    out = out.sort_values(["pct_non_null","column"], ascending=[True, True]).reset_index(drop=True)
    return out

def numeric_summary(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    cols = [c for c in cols if c in df.columns]
    if not cols:
        return pd.DataFrame(columns=["column","n","mean","std","p10","p50","p90","min","max"])
    desc = df[cols].describe(percentiles=[0.1,0.5,0.9]).T
    desc = desc.rename(columns={"10%":"p10","50%":"p50","90%":"p90"})
    desc.insert(0, "column", desc.index)
    desc = desc.reset_index(drop=True)
    desc["n"] = desc["count"].astype(int)
    return desc[["column","n","mean","std","p10","p50","p90","min","max"]]

def infer_key_duplicates(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    keys = [k for k in keys if k in df.columns]
    if not keys:
        return pd.DataFrame({"issue":["no_keys_found"], "details":["Keys not found in df"]})
    dup = df.duplicated(subset=keys, keep=False)
    ndup = int(dup.sum())
    return pd.DataFrame({
        "keys": [",".join(keys)],
        "duplicate_rows": [ndup],
        "duplicate_rate": [ndup / max(len(df),1)]
    })
