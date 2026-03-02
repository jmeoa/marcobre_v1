import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def _clean_hover_unit(unit: str | None):
    return unit if unit else ""

def bar_impact(impact_df: pd.DataFrame) -> go.Figure:
    d = impact_df[impact_df["motivo"] != "TOTAL (unión de reglas)"].copy()
    fig = px.bar(
        d,
        x="motivo",
        y="filas_afectadas",
        title="Limpieza técnica auditada — filas afectadas por regla (sin ocultar solapes)",
        labels={"filas_afectadas":"Filas afectadas", "motivo":"Motivo"}
    )
    fig.update_layout(margin=dict(l=20,r=20,t=60,b=20))
    return fig

def waterfall_total(before: int, after: int) -> go.Figure:
    removed = before - after
    fig = go.Figure(go.Waterfall(
        name="",
        orientation="v",
        measure=["absolute","relative","absolute"],
        x=["Filas antes","Eliminadas (unión reglas)","Filas después"],
        y=[before, -removed, after],
        connector={"line":{"width":1}},
    ))
    fig.update_layout(
        title="Impacto total de limpieza técnica",
        showlegend=False,
        margin=dict(l=20,r=20,t=60,b=20)
    )
    return fig

def outlier_rate_heatmap(summary_df: pd.DataFrame) -> go.Figure:
    pivot = summary_df.pivot(index="oxi_dominante", columns="mes", values="pct_outliers")
    fig = px.imshow(
        pivot,
        aspect="auto",
        title="Validación metalúrgica — % de outliers por OXI y mes",
        labels=dict(x="Mes", y="OXI dominante", color="% outliers")
    )
    fig.update_layout(margin=dict(l=20,r=20,t=60,b=20))
    return fig

def histogram_by_oxi(df: pd.DataFrame, col: str, unit: str) -> go.Figure:
    fig = px.histogram(
        df,
        x=col,
        color="oxi_dominante",
        opacity=0.6,
        barmode="overlay",
        marginal="box",
        title=f"Distribución de {col} por OXI dominante",
        labels={col: f"{col} ({unit})", "oxi_dominante":"OXI dominante"}
    )
    fig.update_layout(margin=dict(l=20,r=20,t=60,b=20))
    return fig

def boxplot_by_oxi(df: pd.DataFrame, col: str, unit: str) -> go.Figure:
    fig = px.box(
        df,
        x="oxi_dominante",
        y=col,
        points="outliers",
        title=f"Boxplot de {col} por OXI dominante",
        labels={col: f"{col} ({unit})", "oxi_dominante":"OXI dominante"}
    )
    fig.update_layout(margin=dict(l=20,r=20,t=60,b=20))
    return fig

def stacked_area_mix(mix_df: pd.DataFrame) -> go.Figure:
    fig = px.area(
        mix_df,
        x="mes",
        y="share_pct",
        color="oxi_dominante",
        groupnorm="",
        title="Mix OXI por mes (participación de bateas por OXI dominante)",
        labels={"share_pct":"Participación (%)","mes":"Mes","oxi_dominante":"OXI dominante"}
    )
    fig.update_layout(margin=dict(l=20,r=20,t=60,b=20))
    return fig

def rolling_recovery_plot(ts_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts_df["mes"], y=ts_df["rec_mean"], mode="lines+markers", name="Rec promedio mes"))
    fig.add_trace(go.Scatter(x=ts_df["mes"], y=ts_df["rec_roll3"], mode="lines", name="Media móvil 3 meses"))
    fig.update_layout(
        title="Evolución de recuperación (promedio mensual + media móvil)",
        xaxis_title="Mes",
        yaxis_title="Recuperación (%)",
        margin=dict(l=20,r=20,t=60,b=20)
    )
    return fig

def residuals_plot(res_df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        res_df,
        x="y_hat",
        y="resid",
        color="oxi_dominante",
        title="Diagnóstico — Residuos vs valores ajustados (OLS)",
        labels={"y_hat":"Recuperación ajustada (%)","resid":"Residuo (%)","oxi_dominante":"OXI dominante"}
    )
    fig.update_layout(margin=dict(l=20,r=20,t=60,b=20))
    return fig

def importance_bar(importance_df: pd.DataFrame) -> go.Figure:
    if importance_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Importancia relativa (proxy) — no disponible", margin=dict(l=20,r=20,t=60,b=20))
        return fig

    d = importance_df.copy().head(15)
    fig = px.bar(
        d.sort_values("Importancia_relativa_proxy_|corr|"),
        x="Importancia_relativa_proxy_|corr|",
        y="Variable",
        orientation="h",
        title="Drivers (proxy) — |corr| de variable vs recuperación, controlando por OXI",
        labels={"Importancia_relativa_proxy_|corr|":"|correlación parcial|", "Variable":"Variable"}
    )
    fig.update_layout(margin=dict(l=20,r=20,t=60,b=20))
    return fig

def heatmap_window(df: pd.DataFrame, x: str, y: str, z: str, x_unit: str, y_unit: str, z_unit: str) -> go.Figure:
    # binning for heatmap
    d = df[[x,y,z]].dropna().copy()
    d["x_bin"] = pd.qcut(d[x], q=12, duplicates="drop")
    d["y_bin"] = pd.qcut(d[y], q=12, duplicates="drop")
    pivot = d.groupby(["y_bin","x_bin"])[z].mean().unstack()

    fig = px.imshow(
        pivot,
        aspect="auto",
        title=f"Ventana operacional — {z} vs {x} y {y} (promedio por bins)",
        labels=dict(x=f"{x} ({x_unit})", y=f"{y} ({y_unit})", color=f"{z} ({z_unit})")
    )
    fig.update_layout(margin=dict(l=20,r=20,t=60,b=20))
    return fig
