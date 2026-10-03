# -*- coding: utf-8 -*-
"""gea_fdr.py —— 候选位点的多重检验校正（BH-FDR）+ 群体结构残留诊断

为什么必须先查 λ（基因组膨胀因子）：
  如果群体结构没控制干净，所有位点的统计量会**整体膨胀**，
  这时直接做 FDR 会得到一堆假阳性。λ 是用 z 的中位数反推的膨胀倍数，
  λ≈1 说明控制得好；λ 明显>1 就要先做 genomic control 校正（z/√λ）再算 p。

为什么还要做 LD 剪枝版：
  相邻 SNP 高度连锁，1623 万个位点并不是 1623 万次独立检验。
  按物理距离（默认 50 kb）每窗只留最强位点，得到"有效检验数 m_eff"，
  用它做 BH 更贴近真实（文献常用的近似）。

用法: python /mnt/c/SF_data/tools/gea_fdr.py [z表路径] [剪枝窗口bp]
"""
import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = "/mnt/c/SF_data"
ZFILE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "report", "gea_rda_z_full.tsv")
WIN = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
OUT = os.path.join(ROOT, "tools", "report", "gea_fdr_significant.tsv")
ALPHA = 0.05


def bh(p, alpha=ALPHA, m_denom=None):
    """Benjamini-Hochberg：返回 (显著布尔数组, p 值阈值)

    ⚠️ 关键：**必须在"原始全量"的 p 向量上判定**。
    我曾把 BH 用在"每窗口挑最强位点"的剪枝子集上——那个子集的 p 值是
    被挑选过的、系统性偏小，BH 的均匀性假设直接崩掉，结果 7643 个位点了
    7639 个"显著"（|z| 阈值只有 1.94），荒谬。
    正确做法：p 用全量，只是把阈值里的分母 m 换成有效检验数 m_eff。
    """
    m = len(p)
    md = m_denom if m_denom else m
    order = np.argsort(p)
    ps = p[order]
    thresh = alpha * (np.arange(1, m + 1) / md)
    passed = ps <= thresh
    if not passed.any():
        return np.zeros(m, bool), 0.0
    kmax = int(np.where(passed)[0].max())
    cutoff = ps[kmax]
    sig = p <= cutoff
    return sig, cutoff


def main():
    print("读取 z 表: %s" % ZFILE)
    d = pd.read_csv(ZFILE, sep="\t")
    z = d["z"].values.astype(np.float64)
    marker = d["marker"].values
    m = len(z)
    print("  位点 %d 个" % m)

    # ---------- 1. 基因组膨胀因子 λ ----------
    med = np.median(z ** 2)
    lam = med / 0.4549364          # 卡方(1df)中位数 0.4549
    print()
    print("=== 群体结构残留诊断 ===")
    print("  z²中位数 = %.4f  ⇒ 基因组膨胀因子 λ = %.4f" % (med, lam))
    if lam < 1.02:
        print("  判读：λ≈1，群体结构控制得住，p 值可信")
    elif lam < 1.10:
        print("  判读：轻度膨胀，建议做 genomic control 校正后再算 p")
    else:
        print("  判读：⚠ 明显膨胀（λ>1.1），必须先 genomic control，否则 FDR 全是假阳性")
    # ⚠️ λ<1 说明没有膨胀，此时**不要**做 genomic control（除以 √λ 会把统计量人为放大）
    if lam >= 1.0:
        zc = z / np.sqrt(lam)
        print("  已按 λ 做 genomic control 校正")
    else:
        zc = z.copy()
        print("  λ<1，不做校正（否则人为放大统计量）— 下面两组 p 值实际相同")

    # ---------- 2. p 值 ----------
    p_raw = 2.0 * norm.sf(np.abs(z))
    p_adj = 2.0 * norm.sf(np.abs(zc))

    # ---------- 3. BH-FDR（全量）----------
    sig_raw, cut_raw = bh(p_raw)
    sig_adj, cut_adj = bh(p_adj)
    print()
    print("=== BH-FDR（全量 m = %d）===" % m)
    print("  未校正（用原始 z） : FDR<%.2f 的位点 %d 个（|z| 阈值 %.3f）"
          % (ALPHA, sig_raw.sum(), np.abs(z[sig_raw]).min() if sig_raw.any() else 0))
    print("  genomic control 后 : FDR<%.2f 的位点 %d 个（|z| 阈值 %.3f）"
          % (ALPHA, sig_adj.sum(), np.abs(z[sig_adj]).min() if sig_adj.any() else 0))

    # ---------- 4. LD 剪枝版 ----------
    chrom = np.array([str(x).rsplit("_", 1)[0] for x in marker])
    pos = np.array([int(str(x).rsplit("_", 1)[1]) for x in marker])
    # 无偏剪枝：每 WIN bp 窗口取**位置最小**的那个位点（与统计量无关 ⇒ 子集分布仍均匀）
    # ⚠️ 绝不能"取 |z| 最大的"——那样子集被挑选过，p 值系统性偏小，BH 假设直接崩塌
    keep_idx = []
    for c in pd.unique(chrom):
        sel = np.where(chrom == c)[0]
        sel = sel[np.argsort(pos[sel])]               # 按位置升序
        seen = set()
        for i in sel:
            b = pos[i] // WIN
            if b in seen:
                continue
            seen.add(b)
            keep_idx.append(i)
    keep_idx = np.array(sorted(keep_idx))
    m_eff = len(keep_idx)
    print()
    print("=== LD 剪枝（每 %d bp 窗口保留最强位点）===" % WIN)
    print("  原始位点 %d → 近似独立位点 m_eff = %d（压缩 %.1f 倍）" % (m, m_eff, m / m_eff))

    # 在无偏独立位点子集上做 BH（这才是"用 m_eff"的正确姿势）
    p_ind = p_adj[keep_idx]
    sig_ind, cut_ind = bh(p_ind, ALPHA)
    idx_sig = keep_idx[sig_ind]
    print("  独立位点子集上做 BH: FDR<%.2f 的位点 %d 个（|z| 阈值 %.3f）"
          % (ALPHA, sig_ind.sum(), np.abs(z[idx_sig]).min() if sig_ind.any() else 0))

    sig10i, cut10i = bh(p_ind, 0.10)
    print("  FDR<0.10 的位点 %d 个（|z| 阈值 %.3f）"
          % (sig10i.sum(), np.abs(z[keep_idx[sig10i]]).min() if sig10i.any() else 0))

    # ---------- 5. 输出显著位点 ----------
    # 主名单 = 全量严格 BH（最保守、最经得起审稿）；附加独立位点子集的结果
    out_idx = np.where(sig_adj)[0]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("marker\tchrom\tpos\tz\tp_adj\tfdr_level\n")
        sig5 = set(idx_sig.tolist())
        for i in out_idx:
            lvl = "0.05" if i in sig5 else "0.10"
            fh.write("%s\t%s\t%d\t%.3f\t%.3e\t%s\n"
                     % (marker[i], chrom[i], pos[i], z[i], p_adj[i], lvl))
    print()
    print("已写出显著位点表（FDR<0.10，共 %d 个）: %s" % (len(out_idx), OUT))


if __name__ == "__main__":
    main()
