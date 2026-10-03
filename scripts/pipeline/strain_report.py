# -*- coding: utf-8 -*-
"""strain_report.py —— 株系（玉米型 C / 水稻型 R / 杂交型 H）协变量的挖掘与诊断

★ 为什么株系必须当协变量：
  草地贪夜蛾的玉米型与水稻型在寄主偏好、迁飞行为上不同。若两个株系的地理分布
  （从而气候）系统性不同，不控制株系就会把"寄主适应"误读成"气候适应"。

★ 好消息（2026-09-23 发现）：美国模块 143 个样本在 NCBI SRA 的 isolate 字段里
  全都带有株系判定文本（"...identified as C- strain"），无需做分子分型即可直接用作协变量。
  其他模块（BR/AF/AM/CN）没有该标注，只有 host 字段（采集寄主），且大量缺失。

产出：
  tools/report/strain_covariate.tsv   株系协变量表
  tools/report/strain_diagnostic.png  株系 × 纬度/气候/PC 诊断图
"""
import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/mnt/c/SF_data"
HOST = os.path.join(ROOT, "tools", "report", "host_sra.tsv")
GEA = os.path.join(ROOT, "tools", "report", "gea_input.tsv")
PCA = "/home/hugo/data/angsd/pca_scores.tsv"
OUTT = os.path.join(ROOT, "tools", "report", "strain_covariate.tsv")
OUTP = os.path.join(ROOT, "tools", "report", "strain_diagnostic.png")

PAT = re.compile(r"identified as ([CRH])[- ]*strain", re.I)


def rd(path, sep="\t"):
    rows = [l.rstrip("\n").split(sep) for l in open(path, encoding="utf-8")]
    return [dict(zip(rows[0], r)) for r in rows[1:] if len(r) > 1]


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    host = rd(HOST)
    strain = {}
    for r in host:
        blob = " ".join(v for k, v in r.items() if k != "run")
        m = PAT.search(blob)
        if m:
            strain[r["run"]] = m.group(1).upper()
    print("有株系标注的样本: %d 个" % len(strain))

    gea = {r["run"]: r for r in rd(GEA)}
    pca = {r["run"]: [f(r["PC%d" % i]) for i in range(1, 5)] for r in rd(PCA)}

    us = [s for s in strain if gea.get(s, {}).get("module") == "US"]
    print("其中美国样本: %d 个" % len(us))

    # ---- 写协变量表 ----
    with open(OUTT, "w", encoding="utf-8") as fh:
        fh.write("run\tmodule\tstrain\tlat\tbio1\tbio11\tbio4\tbio12\tPC1\tPC2\n")
        for s in sorted(gea):
            g = gea[s]
            p = pca.get(s, [None] * 4)
            fh.write("\t".join([s, g.get("module", ""), strain.get(s, ""), g.get("lat", ""),
                                g.get("bio1", ""), g.get("bio11", ""), g.get("bio4", ""),
                                g.get("bio12", ""),
                                "" if p[0] is None else "%.5f" % p[0],
                                "" if p[1] is None else "%.5f" % p[1]]) + "\n")
    print("已写出: %s" % OUTT)

    # ---- 诊断 ----
    print()
    print("=== 株系 × 纬度（美国内部）===")
    latst = {}
    for st in ["C", "R", "H"]:
        v = [f(gea[s]["lat"]) for s in us if strain[s] == st]
        v = [x for x in v if x is not None]
        if v:
            latst[st] = v
            print("  %s 型 n=%-3d  纬度均值 %.1f  范围 %.1f~%.1f"
                  % (st, len(v), sum(v) / len(v), min(v), max(v)))

    print()
    print("=== 株系 × 气候（美国内部）===")
    clst = {}
    for key, lbl in [("bio1", "年均温℃"), ("bio11", "最冷季℃"), ("bio4", "温度季节性")]:
        line = "  %-10s" % lbl
        for st in ["C", "R"]:
            v = [f(gea[s][key]) for s in us if strain[s] == st]
            v = [x for x in v if x is not None]
            clst[(key, st)] = v
            if v:
                line += "   %s型 %7.2f (n=%d)" % (st, sum(v) / len(v), len(v))
        print(line)

    print()
    print("=== 株系 × 主成分（遗传结构是否主要就是株系？）===")
    pcst = {}
    for k in range(4):
        c = [pca[s][k] for s in strain if s in pca and strain[s] == "C"]
        r = [pca[s][k] for s in strain if s in pca and strain[s] == "R"]
        pcst[(k, "C")] = c
        pcst[(k, "R")] = r
        if c and r:
            print("  PC%d  C型 %+.3f (n=%d)   R型 %+.3f (n=%d)   差 %+.3f"
                  % (k + 1, sum(c) / len(c), len(c), sum(r) / len(r), len(r),
                     sum(c) / len(c) - sum(r) / len(r)))

    # 株系与纬度的点二列相关（美国内部）
    if "C" in latst and "R" in latst:
        y = np.array([1.0] * len(latst["C"]) + [0.0] * len(latst["R"]))
        x = np.array(latst["C"] + latst["R"])
        rb = float(np.corrcoef(x, y)[0, 1])
        print()
        print("  ★ 株系(C=1/R=0) 与纬度的点二列相关 r = %+.3f" % rb)
        print("    判读：|r|<0.2 基本不纠缠；0.2~0.4 必须在模型里加株系协变量；>0.4 严重纠缠")

    # ---- 画图 ----
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
    col = {"C": "#c0392b", "R": "#2980b9", "H": "#7f8c8d"}

    # 1. 株系 × 纬度
    data = [latst.get(st, []) for st in ["C", "R"]]
    ax[0].boxplot([d for d in data if d], tick_labels=[s for s, d in zip(["C", "R"], data) if d],
                  patch_artist=True, widths=.55)
    for b, st in zip(ax[0].artists if hasattr(ax[0], "artists") else [], ["C", "R"]):
        b.set_facecolor(col[st]); b.set_alpha(.6)
    for i, st in enumerate(["C", "R"]):
        v = latst.get(st, [])
        if v:
            ax[0].scatter(np.random.normal(i + 1, .06, len(v)), v, s=10, alpha=.5,
                          c=col[st], edgecolors="none")
    ax[0].set_ylabel("Latitude (deg)")
    ax[0].set_title("US: latitude by host strain", fontsize=11)

    # 2. 株系 × 最冷季温度（越冬关键变量）
    data2 = [clst.get(("bio11", st), []) for st in ["C", "R"]]
    ax[1].boxplot([d for d in data2 if d], tick_labels=[s for s, d in zip(["C", "R"], data2) if d],
                  patch_artist=True, widths=.55)
    for b, st in zip(ax[1].artists if hasattr(ax[1], "artists") else [], ["C", "R"]):
        b.set_facecolor(col[st]); b.set_alpha(.6)
    ax[1].set_ylabel("BIO11 coldest quarter (C)")
    ax[1].set_title("US: winter cold by host strain", fontsize=11)

    # 3. PC1 × 株系
    data3 = [pcst.get((0, st), []) for st in ["C", "R"]]
    ax[2].boxplot([d for d in data3 if d], tick_labels=[s for s, d in zip(["C", "R"], data3) if d],
                  patch_artist=True, widths=.55)
    for b, st in zip(ax[2].artists if hasattr(ax[2], "artists") else [], ["C", "R"]):
        b.set_facecolor(col[st]); b.set_alpha(.6)
    ax[2].set_ylabel("PC1")
    ax[2].set_title("PC1 by host strain (C=corn, R=rice)", fontsize=11)

    plt.tight_layout()
    plt.savefig(OUTP, dpi=140)
    print()
    print("已写出: %s" % OUTP)


if __name__ == "__main__":
    main()
