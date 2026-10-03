# -*- coding: utf-8 -*-
"""队列候选池的交叉结构透视：国家 × study × 平台，用于避免「地理」与「批次」混淆。"""
import csv, os, collections

T = r"C:\SF_data\tools"
rows = [r for r in csv.DictReader(
    open(os.path.join(T, "cohort_pool_1215x.tsv"), encoding="utf-8"), delimiter="\t")]

print(f"合格池 = {len(rows)}\n")

# 国家 × study
print("=" * 96)
print("【国家 × study × 平台】")
print("=" * 96)
by = collections.defaultdict(list)
for r in rows:
    ct = (r["country"] or "?").split(":")[0].strip()
    by[(ct, r["study"])].append(r)

byc = collections.defaultdict(list)
for (ct, st), v in by.items():
    byc[ct].append((st, v))

for ct in sorted(byc, key=lambda c: -sum(len(v) for _, v in byc[c])):
    tot = sum(len(v) for _, v in byc[ct])
    print(f"\n■ {ct}  ({tot} 样本)")
    for st, v in sorted(byc[ct], key=lambda x: -len(x[1])):
        plats = collections.Counter(x["platform"] for x in v)
        provs = collections.Counter((x["country"].split(":", 1)[1].strip()
                                     if ":" in x["country"] else "(无次级地名)") for x in v)
        depth = [float(x["depth_true_x"]) for x in v]
        host = collections.Counter(x["host"] or "(空)" for x in v)
        print(f"    {st:<15} n={len(v):<3} 平台={dict(plats)}")
        print(f"        深度 {min(depth):.0f}~{max(depth):.0f}x   "
              f"次级地名: {dict(provs.most_common(6))}")
        print(f"        host: {dict(host.most_common(3))}")
        print(f"        run: {', '.join(x['run'] for x in v[:4])}{' …' if len(v) > 4 else ''}")

# 平台 × 区域
print("\n" + "=" * 96)
print("【平台 × 区域】—— 看平台是否与地理混杂")
print("=" * 96)
cross = collections.defaultdict(collections.Counter)
for r in rows:
    cross[r["region"]][r["platform"]] += 1
plats = sorted({r["platform"] for r in rows})
print(f"{'区域':<22}" + "".join(f"{p:>12}" for p in plats))
for reg in sorted(cross, key=lambda x: -sum(cross[x].values())):
    print(f"{reg:<22}" + "".join(f"{cross[reg].get(p,0):>12}" for p in plats))
