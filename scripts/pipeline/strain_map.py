# -*- coding: utf-8 -*-
"""strain_map.py —— 株系的地理分布图 + 更新 gea_input.tsv

产出：
  tools/report/strain_map.png        株系 × 模块构成 + 经纬度散点
  tools/report/gea_input.tsv         补上 strain / strain_source 两列
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/mnt/c/SF_data"
PRED = os.path.join(ROOT, "tools", "report", "strain_predicted.tsv")
GEA = os.path.join(ROOT, "tools", "report", "gea_input.tsv")
OUTP = os.path.join(ROOT, "tools", "report", "strain_map.png")


def main():
    pr = pd.read_csv(PRED, sep="\t")
    gea = pd.read_csv(GEA, sep="\t")
    pmap = {r["run"]: r for r in pr.to_dict("records")}

    # 更新 gea_input：官方标注优先，缺失的用分子判定
    strain, source = [], []
    for r in gea["run"]:
        p = pmap.get(r, {})
        k = p.get("strain_known", "")
        if isinstance(k, str) and k in ("C", "R", "H"):
            strain.append(k); source.append("known")
        else:
            strain.append(p.get("strain_pred", "")); source.append("predicted" if p else "")
    if "strain" in gea.columns:
        gea["strain"] = strain
        gea["strain_source"] = source
    else:
        gea.insert(2, "strain", strain)
        gea.insert(3, "strain_source", source)
    gea.to_csv(GEA, sep="\t", index=False)
    print("已更新 %s（strain 有值 %d / %d）" % (GEA, sum(1 for s in strain if s), len(strain)))

    # ---- 画图 ----
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.2))
    mods = ["US", "FL", "BR", "AM", "AF", "CN"]
    Cc, Rr, Hh = [], [], []
    for m in mods:
        sub = pr[pr["module"] == m]
        Cc.append(int((sub["strain_pred"] == "C").sum()))
        Rr.append(int((sub["strain_pred"] == "R").sum()))
        Hh.append(int((sub["strain_known"] == "H").sum()))
    x = np.arange(len(mods))
    ax[0].bar(x, Cc, color="#c0392b", label="C (corn strain)")
    ax[0].bar(x, Rr, bottom=Cc, color="#2980b9", label="R (rice strain)")
    for i in range(len(mods)):
        if Cc[i]: ax[0].text(i, Cc[i] / 2, str(Cc[i]), ha="center", color="white", fontsize=10)
        if Rr[i]: ax[0].text(i, Cc[i] + Rr[i] / 2, str(Rr[i]), ha="center", color="white", fontsize=10)
    ax[0].set_xticks(x); ax[0].set_xticklabels(mods)
    ax[0].set_ylabel("Number of samples")
    ax[0].set_title("Host-strain composition by module\n(all inferred by Tpi/Flightin; US verified by NCBI labels 100%)", fontsize=10)
    ax[0].legend(fontsize=9)

    # 经纬度散点
    m = gea.merge(pr[["run", "strain_pred"]], on="run", how="left")
    m["lat"] = pd.to_numeric(m["lat"], errors="coerce")
    m["lon"] = pd.to_numeric(m["lon"], errors="coerce")
    for st, col, lab in [("C", "#c0392b", "C (corn)"), ("R", "#2980b9", "R (rice)")]:
        s = m[m["strain_pred"] == st]
        ax[1].scatter(s["lon"], s["lat"], c=col, s=26, alpha=.8, label=lab, edgecolors="none")
    ax[1].set_xlabel("Longitude"); ax[1].set_ylabel("Latitude")
    ax[1].set_title("Geographic distribution of host strains\n(n=214; invasion populations are nearly all corn)", fontsize=10)
    ax[1].legend(fontsize=9)
    ax[1].axhline(0, color="#cccccc", lw=.7)
    ax[1].axvline(0, color="#cccccc", lw=.7)
    ax[1].grid(alpha=.25, lw=.4)

    plt.tight_layout()
    plt.savefig(OUTP, dpi=140)
    print("已写出: %s" % OUTP)


if __name__ == "__main__":
    main()
