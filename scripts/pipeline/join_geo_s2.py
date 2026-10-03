# -*- coding: utf-8 -*-
"""把 S2 队列与坐标 join 成 run 级分析输入表。

输出 cohort_s2_geo.tsv：run 级，含 module / 国家 / 行政区 / 平台 / 深度 / 坐标 / 坐标可信度
坐标可信度（confidence）：
  high   —— 市级行政区（level 3），经纬度即采样点附近
  medium —— 州/省级（level 2），误差约百公里量级
  low    —— 国家级质心（level 0），仅作跨大陆背景，**不可用于国家内梯度**
"""
import csv, os, collections

T = r"C:\SF_data\tools"
CO = os.path.join(T, "cohort_formal_s2.tsv")
GE = os.path.join(T, "site_geo_s2.tsv")
OUT = os.path.join(T, "cohort_s2_geo.tsv")

geo = {}
for r in csv.DictReader(open(GE, encoding="utf-8"), delimiter="\t"):
    geo[(r["module"], r["geo_string"])] = r


STATE_LIKE = {"guangdong", "yunnan", "zhejiang", "zhejiang province",
              "selangor", "malacca", "negeri sembilan", "casamance",
              "maranhao", "parana", "mato grosso", "mato grosso do sul",
              "rio grande do sul", "santa catarina", "sao paulo", "minas gerais",
              "goias", "bahia", "arizona", "california", "georgia", "florida",
              "texas", "illinois", "colorado", "pennsylvania"}


def conf(level, sub):
    """可信度按「行政区层级是否真的低于州/省」判定，不能只看 Nominatim 返回的 type。
    US County 与巴西 município 同级（都是州以下真实行政单元）=> 同为 high；
    Citra/Jacksonville 是城镇 => high；仅州/省名或国家名 => medium/low。"""
    s = (sub or "").strip().lower()
    if s in ("", "(国)", "(country)", "-", "n/a"):
        return "low"                      # 国家级质心
    if "county" in s:
        return "high"                     # 县级
    if s in STATE_LIKE or s.rstrip(".") in STATE_LIKE:
        return "medium"                   # 州/省/大区级
    return "high"                         # 市/镇级（巴西市镇、Citra、Jacksonville）


rows = list(csv.DictReader(open(CO, encoding="utf-8"), delimiter="\t"))
out = []
miss = 0
for r in rows:
    g = f"{r['country']}: {r['subnational']}" if r["subnational"] else r["country"]
    g2 = f"{r['country']}:{r['subnational']}" if r["subnational"] else r["country"]
    key = (r["module"], g)
    rec = geo.get(key) or geo.get((r["module"], g2))
    if not rec:
        # 回退：忽略行政区格式（AF/AM 的国家级、以及冒号空格差异）
        cand = [v for (m, s), v in geo.items()
                if m == r["module"] and s.split(":")[0].strip() == r["country"].split(":")[0].strip()]
        rec = cand[0] if cand else None
    if not rec:
        miss += 1
        continue
    out.append({
        "run": r["run"], "study": r["study"], "module": r["module"],
        "country": r["country"].split(":")[0].strip(),
        "subnational": r["subnational"], "platform": r["platform"],
        "depth_x": r["depth_x"], "pct": r["pct"], "dl_GB": r["dl_GB"],
        "lat": rec["lat"], "lon": rec["lon"], "level": rec["level"],
        "confidence": conf(rec["level"], r["subnational"]),
    })

with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()), delimiter="\t")
    w.writeheader()
    w.writerows(out)

print(f"[写出] {OUT}  {len(out)} 行  (未匹配 {miss})")
print("\n坐标可信度分布")
c = collections.Counter(r["confidence"] for r in out)
for k in ("high", "medium", "low"):
    print(f"  {k:<7} {c[k]:>4} 样本")
print("\n按模块")
for m in sorted({r['module'] for r in out}):
    sub = [r for r in out if r["module"] == m]
    cc = collections.Counter(r["confidence"] for r in sub)
    pts = len({(r["lat"], r["lon"]) for r in sub})
    print(f"  {m:<4}{len(sub):>4} 样本  唯一坐标 {pts:>3}  "
          f"high/medium/low = {cc['high']}/{cc['medium']}/{cc['low']}")
