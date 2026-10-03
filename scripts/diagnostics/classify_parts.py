# -*- coding: utf-8 -*-
"""残块分类：判定哪些 .partN 块可以安全删除。

遵循 win-bulk-safe-delete 技能流程：
  ① 量 ② 按业务实体归类 ③ 验真「被删的确实冗余」 ④ 护栏 ⑤ 分批删 ⑥ 回查

业务实体 = (样本, 读向, PCT)，例如 SRR29141596_2 / pct=95
  产物链：碎片 X.partial95.part12  →  合并体 X.partial95  →  （裁尾后仍叫 X.partial95 + .nrec 凭证）

判定规则：
  【可删·已被取代】同实体已有合并体（或已成文件）存在 ⇒ 碎片是合并后的残渣
  【可删·已废弃】样本不在 S2 队列中，或队列要求的 PCT 与碎片 PCT 不一致
               ⇒ 该碎片永远不可能被复用（dl_ena.sh 按 PCT 命名块）
  【不可删·可续传】样本在队列中、PCT 一致、且尚无合并体 ⇒ 这是有效进度
  【不可删·正在进行】当前正在下载的样本 ⇒ 绝不能碰
"""
import csv, os, re, sys, collections, json

RAW = r"C:\SF_data\01_raw"
TOOLS = r"C:\SF_data\tools"
INV = os.path.join(TOOLS, "inv_raw_snapshot.tsv")
COHORT = os.path.join(TOOLS, "cohort_formal_s2.tsv")
LOG = os.path.join(TOOLS, "dl_US.log")

# ---------- 读清单 ----------
files = []          # (size, mtime, posix_path, basename)
for line in open(INV, encoding="utf-8"):
    p = line.rstrip("\n").split("\t")
    if len(p) != 3:
        continue
    files.append((int(p[0]), float(p[1]), p[2], os.path.basename(p[2])))

# ---------- 队列：sample -> 计划 PCT ----------
plan = {}
if os.path.exists(COHORT):
    for r in csv.DictReader(open(COHORT, encoding="utf-8"), delimiter="\t"):
        plan[r["run"]] = int(r["pct"])
print(f"队列样本 {len(plan)} 个")

# ---------- 正在下载的样本 ----------
inflight = set()
if os.path.exists(LOG):
    txt = open(LOG, encoding="utf-8", errors="replace").read()
    m = re.findall(r"^=== (SRR\d+)\s+PCT=(\d+)", txt, re.M)
    if m:
        inflight.add(m[-1][0])
print(f"正在下载: {sorted(inflight) or '(无法判定)'}")

# ---------- 归类 ----------
# 存在的「合并体/成文件」集合：把路径归一化成 (dir, name)
present = {os.path.basename(p) for _, _, p, b in files}

FRAG = re.compile(r"^(SRR\d+)_([12])\.fastq\.gz(?:\.partial(\d+))?\.part(\d+)$")
ASSEMBLED = re.compile(r"^(SRR\d+)_([12])\.fastq\.gz(?:\.partial(\d+))?$")

groups = collections.defaultdict(lambda: {"frags": [], "bytes": 0})
for sz, mt, path, base in files:
    m = FRAG.match(base)
    if not m:
        continue
    sample, mate, pct, blk = m.group(1), m.group(2), m.group(3), m.group(4)
    key = (sample, mate, pct)
    groups[key]["frags"].append(base)
    groups[key]["bytes"] += sz

delete, keep, reasons = [], [], collections.Counter()
for (sample, mate, pct), g in groups.items():
    pct_i = int(pct) if pct else 100
    assembled = None
    for cand in (f"{sample}_{mate}.fastq.gz" + (f".partial{pct}" if pct else ""),
                 f"{sample}_{mate}.fastq.gz"):
        if cand in present:
            assembled = cand
            break
    if sample in inflight:
        keep.append(((sample, mate, pct), g))
        reasons["正在进行"] += 1
    elif assembled:
        delete.append(((sample, mate, pct), g, f"已被 {assembled} 取代"))
        reasons["已被取代"] += 1
    elif sample not in plan:
        delete.append(((sample, mate, pct), g, "样本不在 S2 队列（废弃轮次）"))
        reasons["已废弃"] += 1
    elif plan[sample] != pct_i:
        delete.append(((sample, mate, pct), g,
                       f"PCT 不符（碎片 {pct_i} vs 队列 {plan[sample]}），无法续传"))
        reasons["PCT不符"] += 1
    else:
        keep.append(((sample, mate, pct), g))
        reasons["可续传进度"] += 1

print("\n================ 分类结果 ================")
for k, v in reasons.most_common():
    print(f"  {k:<14} {v} 组")
db = sum(g["bytes"] for _, g, _ in delete)
kb = sum(g["bytes"] for _, g in keep)
print(f"\n  可删: {sum(len(g['frags']) for _,g,_ in delete)} 文件 / {db/1073741824:.2f} GB")
print(f"  保留: {sum(len(g['frags']) for _,g in keep)} 文件 / {kb/1073741824:.2f} GB")

print("\n--- 保留明细（必须逐条看）---")
for (s, m, p), g in sorted(keep):
    print(f"  {s}_{m} pct={p or 100:<4} {len(g['frags']):>4} 块 {g['bytes']/1048576:>8.1f} MB")

print("\n--- 可删明细（前 20 组）---")
for (s, m, p), g, why in sorted(delete, key=lambda x: -x[1]["bytes"])[:20]:
    print(f"  {s}_{m} pct={p or 100:<4} {len(g['frags']):>4} 块 {g['bytes']/1048576:>8.1f} MB  ← {why}")

# ---------- 写清单 ----------
with open(os.path.join(TOOLS, "delete_list.txt"), "w", encoding="utf-8", newline="\n") as f:
    for (s, m, p), g, why in delete:
        for b in sorted(g["frags"]):
            f.write(f"{RAW}/{b}\n")
with open(os.path.join(TOOLS, "keep_list.txt"), "w", encoding="utf-8", newline="\n") as f:
    for (s, m, p), g in keep:
        for b in sorted(g["frags"]):
            f.write(f"{RAW}/{b}\n")
json.dump({"delete_bytes": db, "keep_bytes": kb,
           "delete_files": sum(len(g['frags']) for _, g, _ in delete),
           "keep_files": sum(len(g['frags']) for _, g in keep)},
          open(os.path.join(TOOLS, "del_stats.json"), "w"), ensure_ascii=False, indent=1)
print(f"\n[写出] delete_list.txt / keep_list.txt / del_stats.json")
