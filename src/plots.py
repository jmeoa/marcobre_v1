from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def missingness_bar(df: pd.DataFrame, top: int = 25):
    miss = df.isna().mean().sort_values(ascending=False).head(top)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(miss.index.astype(str), miss.values)
    ax.set_ylabel("Fracción de nulos")
    ax.set_title(f"Top {top} columnas con mayor % de nulos")
    ax.tick_params(axis="x", rotation=75)
    plt.tight_layout()
    return fig

def hist(df: pd.DataFrame, col: str, bins: int = 40):
    x = pd.to_numeric(df[col], errors="coerce")
    fig, ax = plt.subplots(figsize=(8,4))
    ax.hist(x.dropna().values, bins=bins)
    ax.set_title(f"Distribución: {col}")
    ax.set_xlabel(col)
    ax.set_ylabel("Frecuencia")
    plt.tight_layout()
    return fig

def scatter(df: pd.DataFrame, x: str, y: str):
    xx = pd.to_numeric(df[x], errors="coerce")
    yy = pd.to_numeric(df[y], errors="coerce")
    m = xx.notna() & yy.notna()
    fig, ax = plt.subplots(figsize=(6,5))
    ax.scatter(xx[m], yy[m], s=10)
    ax.set_xlabel(x); ax.set_ylabel(y)
    ax.set_title(f"{y} vs {x}")
    plt.tight_layout()
    return fig

def corr_heatmap(df: pd.DataFrame, cols: list[str]):
    d = df[cols].apply(pd.to_numeric, errors="coerce")
    c = d.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(c.values, aspect="auto")
    ax.set_xticks(range(len(cols))); ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=75, ha="right"); ax.set_yticklabels(cols)
    ax.set_title("Correlación (Pearson) — variables seleccionadas")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    return fig
