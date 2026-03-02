import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.preprocessing import StandardScaler

def build_oxi_dominant(df: pd.DataFrame, oxi_cols=None) -> pd.Series:
    if oxi_cols is None:
        oxi_cols = ["pctoxi_2","pctoxi_3","pctoxi_3m","pctoxi_4","pctoxi_4m"]
    present = [c for c in oxi_cols if c in df.columns]
    if not present:
        return pd.Series(["SIN_OXI"]*len(df), index=df.index)

    tmp = df[present].copy()
    tmp = tmp.fillna(0)
    max_col = tmp.idxmax(axis=1)
    label = max_col.str.replace("pct", "", regex=False).str.upper()
    label = label.str.replace("OXI_", "OXI ", regex=False)
    # Handle rows where all zeros -> SIN_OXI
    all_zero = tmp.sum(axis=1).eq(0)
    label = label.where(~all_zero, "SIN_OXI")
    return label

def characterize_by_oxi(df: pd.DataFrame, col_y: str, group_col: str="oxi_dominante") -> pd.DataFrame:
    def q(x, p):
        return np.nanpercentile(x, p) if np.isfinite(x).any() else np.nan

    rows = []
    for g, d in df.groupby(group_col, dropna=False):
        x = d[col_y].to_numpy(dtype=float)
        x = x[np.isfinite(x)]
        n = int(len(x))
        mean = float(np.mean(x)) if n else np.nan
        std = float(np.std(x, ddof=1)) if n>1 else np.nan
        cv = float(std/mean) if (n>1 and mean not in (0, np.nan) and np.isfinite(mean)) else np.nan
        rows.append({
            group_col: g,
            "N_efectivo": n,
            "p10": q(x,10) if n else np.nan,
            "p25": q(x,25) if n else np.nan,
            "p50": q(x,50) if n else np.nan,
            "p75": q(x,75) if n else np.nan,
            "p90": q(x,90) if n else np.nan,
            "media": mean,
            "desv": std,
            "CV": cv,
        })
    return pd.DataFrame(rows).sort_values(group_col)

def compare_oxis(df: pd.DataFrame, col_y: str, group_col: str="oxi_dominante"):
    """
    ANOVA si supuestos razonables; si no, Kruskal.
    Devuelve dict con test usado y p-value.
    """
    from scipy import stats

    groups = []
    labels = []
    for g, d in df.groupby(group_col):
        x = d[col_y].dropna().astype(float).values
        if len(x) >= 5:
            groups.append(x)
            labels.append(g)

    if len(groups) < 2:
        return {"test": "N/A", "p_value": np.nan, "k": len(groups), "labels": labels}

    # Simple heuristic: use Kruskal by default (robust to non-normality)
    stat, p = stats.kruskal(*groups)
    return {"test": "Kruskal-Wallis", "p_value": float(p), "k": len(groups), "labels": labels}

def fit_models_drivers(
    df: pd.DataFrame,
    *,
    y: str = "pctrec_cusac",
    oxi_col: str = "oxi_dominante",
    mineralogical=None,
    operational=None,
    hydraulic=None,
):
    """
    Drivers de recuperación controlando por OXI:
      - OLS con dummies OXI + variables
      - Modelo robusto (RLM Huber)
    Retorna: (ols_result, rlm_result, table_betas, importance_table)
    """
    dfx = df.copy()

    if mineralogical is None:
        mineralogical = ["cut_pct","cusac_pct","pctc","fet_pct","indice_solubilidad"]
    if operational is None:
        operational = ["p80_mm","pcthumedad_inicial","ratio_de_curado_kg_tn","load__dosificacion_acido_x_dia_kg_tms__mean"]
    if hydraulic is None:
        hydraulic = ["leach__flujo_lix_hg__mean","leach__flujo_lix_lg__mean","load__flujo_lix_hg__mean","load__flujo_lix_lg__mean"]

    # Keep only existing columns
    mineralogical = [c for c in mineralogical if c in dfx.columns]
    operational  = [c for c in operational if c in dfx.columns]
    hydraulic    = [c for c in hydraulic if c in dfx.columns]

    features = mineralogical + operational + hydraulic

    # Drop rows with missing in y/features/oxi only for modeling (this is not "cleaning"; it's model input)
    model_df = dfx[[y, oxi_col] + features].copy()
    model_df = model_df.dropna()

    # Build formula with categorical OXI
    rhs = " + ".join([f"C({oxi_col})"] + features) if features else f"C({oxi_col})"
    formula = f"{y} ~ {rhs}"

    ols = smf.ols(formula=formula, data=model_df).fit()
    rlm = smf.rlm(formula=formula, data=model_df, M=sm.robust.norms.HuberT()).fit()

    # Betas table (OLS)
    bt = pd.DataFrame({
        "Variable": ols.params.index,
        "Beta": ols.params.values,
        "p_value": ols.pvalues.values
    })
    bt["significativo_5pct"] = bt["p_value"] <= 0.05

    # Relative importance (optional, simple): standardized betas for numeric vars only
    imp_rows = []
    if features:
        Xnum = model_df[features].astype(float).copy()
        scaler = StandardScaler()
        Xs = scaler.fit_transform(Xnum.values)
        ys = (model_df[y].values - np.mean(model_df[y].values)) / np.std(model_df[y].values)

        # Fit OLS on standardized numeric features only (for relative magnitude) – still controlling by OXI via residualization
        # Residualize y vs OXI, and each x vs OXI
        # (keeps logic transparent and avoids overclaiming)
        y_res = smf.ols(f"{y} ~ C({oxi_col})", data=model_df).fit().resid.values
        for i, col in enumerate(features):
            x_tmp = model_df[[col, oxi_col]].copy()
            x_res = smf.ols(f"{col} ~ C({oxi_col})", data=x_tmp).fit().resid.values
            # standardized
            if np.std(x_res) > 0 and np.std(y_res) > 0:
                beta = np.corrcoef(x_res, y_res)[0,1]  # correlation as proxy effect direction/strength
                imp_rows.append({"Variable": col, "Importancia_relativa_proxy_|corr|": float(abs(beta)), "signo_corr": float(np.sign(beta))})
        importance = pd.DataFrame(imp_rows).sort_values("Importancia_relativa_proxy_|corr|", ascending=False)
    else:
        importance = pd.DataFrame(columns=["Variable","Importancia_relativa_proxy_|corr|","signo_corr"])

    meta = {
        "n_modelo": int(len(model_df)),
        "features_mineralogicas": mineralogical,
        "features_operacionales": operational,
        "features_hidraulicas_turno": hydraulic,
        "r2_ols": float(ols.rsquared),
        "r2_adj_ols": float(ols.rsquared_adj),
    }

    return ols, rlm, bt, importance, meta
