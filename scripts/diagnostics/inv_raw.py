# -*- coding: utf-8 -*-
"""01_raw 现状盘点：每个样本已下百分比 / 当前可用深度 / 补到 20x 的成本。

⚠️ 关键教训（2026-09-17 傍晚，我自己踩过）：
   **不能从文件名判断已下比例**！早期轮次下载的残片在命名规范变更时被**剥掉了 `.partialN` 后缀**，
   磁盘上看起来像「全量下载」，实际只有 ~15~20%。
   必须按字节反算：pct = 磁盘字节 / (真实深度 × GB_PER_X)
   例：SRR9289279 真实 76.9× -> 全份 ~17.4 GB，磁盘只有 2.68 GB -> 实际 ~15%，不是 100%。

规则（实测确认）：
  - dl_ena.sh 只认「同名 .partial<N> + 隐藏凭证」；换百分比会重下整份，**旧文件不可复用**
  - 当前可用深度 = 真实深度 × 实际已下比例 × 0.6
  - 补到 20x ⇒ 需下载到名义 33.3x ⇒ 需下百分比 = min(100, 33.33/真实深度×100)
"""
import csv, os, re, collections

T = r"C:\SF_data\tools"
RAW = r"C:\SF_data\01_raw"
TARGET = 33.33
COEF = 0.6
GB_PER_X = 5.65 / 25.0

m = {r["run"]: r for r in csv.DictReader(
    open(os.path.join(T, "sfru_wgs_matrix.tsv"), encoding="utf-8"), delimiter="\t")}
pool = {r["run"]: r for r in csv.DictReader(
    open(os.path.join(T, "deep_pool_20x.tsv"), encoding="utf-8"), delimiter="\t")}

# 扫 01_raw：按 run 汇总磁盘字节（优先取带 .partialN 的新格式；否则取无后缀的旧格式）
best = {}   # run -> [pct_from_name, bytes]
for fn in os.listdir(RAW):
    if fn.startswith("."):
        continue
    mm = re.match(r"^(SRR\d+|ERR\d+)_([12])\.fastq\.gz(?:\.partial(\d+))?$", fn)
    if not mm:
        continue
    run = mm.group(1)
    pct = int(mm.group(3)) if mm.group(3) else 0   # 0 = 无后缀，比例未知，待按字节反算
    sz = os.path.getsize(os.path.join(RAW, fn))
    cur = best.get(run)
    if cur is None:
        best[run] = [pct, sz]
    elif pct > cur[0]:
        best[run] = [pct, sz]
    elif pct == 0 and cur[0] == 0:
        best[run][1] += sz
    elif pct == cur[0]:
        best[run][1] += sz

rows = []
for run, (pct_name, sz) in sorted(best.items()):
    row = m.get(run)
    d = float(row["depth_x"]) if row and row.get("depth_x") else None
    full_gb = d * GB_PER_X if d else None
    if d:
        pct_real = min(100.0, sz / 1e9 / full_gb * 100)
        have_us = d * pct_real / 100 * COEF
        need_pct = min(100.0, TARGET / d * 100)
        topup_gb = full_gb * need_pct / 100      # 换比例必须整份重下
    else:
        pct_real = have_us = need_pct = topup_gb = None
    rows.append((run, pct_name, pct_real, sz / 1e9, d, full_gb, have_us, need_pct, topup_gb))

print(f"01_raw 样本数 = {len(rows)}\n")
print(f"{'run':<13}{'名标%':>6}{'实算%':>7}{'磁盘GB':>8}{'全份GB':>8}{'当前可用x':>10}{'补下GB':>8}  状态")
print("-" * 84)
ok, marginal, dead, unknown, deadend = [], [], [], [], []
for run, pn, pr, gb, d, fg, hu, np_, tg in sorted(rows, key=lambda x: -(x[6] or 0)):
    if d is None:
        st = "? 不在WGS矩阵"; unknown.append(run)
    elif d < TARGET:
        st = f"✗ 死路(上限{d*COEF:.1f}x)"; deadend.append(run)
    elif hu >= 20:
        st = "✅ 已达 20x"; ok.append(run)
    elif hu >= 18:
        st = "△ 临界(可接受)"; marginal.append(run)
    else:
        st = "↓ 可达，需补下"; dead.append(run)
    print(f"{run:<13}{(pn or '旧'):>6}"
          f"{(f'{pr:.1f}' if pr is not None else '-'):>7}"
          f"{gb:>8.2f}{(f'{fg:.2f}' if fg else '-'):>8}"
          f"{(f'{hu:.1f}' if hu is not None else '-'):>10}"
          f"{(f'{tg:.2f}' if tg else '-'):>8}  {st}")

print(f"\n汇总：已达20x {len(ok)} ｜ 临界 {len(marginal)} ｜ **可达但需补下 {len(dead)}** ｜ "
      f"**深度不足死路 {len(deadend)}** ｜ 不在矩阵 {len(unknown)}")
tot = sum(r[8] for r in rows if r[8] and (r[4] or 0) >= TARGET)
print(f"把「可达但未达标」的补到 20x：合计重下 {tot:.1f} GB ({tot/1000:.2f} TB)")
print(f"死路样本（下满也到不了 20x，应剔除）共 {len(deadend)} 个：")
print("  " + ", ".join(f"{r}({next(x for x in rows if x[0]==r)[4]:.1f}x)"
                       for r in sorted(deadend, key=lambda x: next(y for y in rows if y[0]==x)[4])))

# ---- 交叉验证：带 .partialN 名标的文件，其名标% 与字节实算% 是否吻合 ----
# 若不吻合，说明 GB_PER_X 常数对该平台不成立（BGISEQ/DNBSEQ 可能不同）
print("\n=== 交叉验证：名标% vs 字节实算%（带 .partialN 的样本）===")
print(f"{'run':<13}{'名标%':>6}{'实算%':>7}{'偏差':>7}  平台")
bad = 0
for run, pn, pr, gb, d, fg, hu, np_, tg in rows:
    if pn and pr is not None:
        dev = pr - pn
        plat = (m.get(run, {}).get("platform") or "?")
        flag = "  ⚠️偏差大" if abs(dev) > 8 else ""
        print(f"{run:<13}{pn:>6}{pr:>7.1f}{dev:>+7.1f}  {plat}{flag}")
        if abs(dev) > 8:
            bad += 1
print(f"偏差 >8 个百分点的样本数 = {bad}")

print("\n=== 已达 20x（可直接进队列）===")
for run in ok:
    r = next(x for x in rows if x[0] == run)
    print(f"  {run:<13} 实算已下 {r[2]:.1f}%  当前可用 {r[6]:.1f}x")
print("=== 临界 ===")
for run in marginal:
    r = next(x for x in rows if x[0] == run)
    print(f"  {run:<13} 实算已下 {r[2]:.1f}%  当前可用 {r[6]:.1f}x")
