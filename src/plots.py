from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt

def hist(df: pd.DataFrame, col: str, bins: int = 40, title: str | None = None):
    x = df[col].dropna()
    plt.figure()
    plt.hist(x, bins=bins)
    plt.title(title or f"Histograma — {col}")
    plt.xlabel(col)
    plt.ylabel("Frecuencia")
    plt.tight_layout()

def scatter(df: pd.DataFrame, x: str, y: str, hue: str | None = None, title: str | None = None):
    plt.figure()
    if hue and hue in df.columns:
        for k, g in df[[x,y,hue]].dropna().groupby(hue):
            plt.scatter(g[x], g[y], s=12, alpha=0.6, label=str(k))
        plt.legend(title=hue)
    else:
        d = df[[x,y]].dropna()
        plt.scatter(d[x], d[y], s=12, alpha=0.6)
    plt.title(title or f"{y} vs {x}")
    plt.xlabel(x)
    plt.ylabel(y)
    plt.tight_layout()
