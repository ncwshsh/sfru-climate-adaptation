# -*- coding: utf-8 -*-
"""extract_climate.py —— 按样本坐标从 WorldClim 栅格提取生物气候变量

数据源：WorldClim v2.1，2.5 arc-min（约 5 km），1970-2000 气候常态值
  19 个生物气候变量（BIO1~BIO19）+ 海拔（elev）

为什么用 2.5 arc-min 而不是 30 秒（1 km）：
  本队列坐标精度参差——美国是县级（level=2、置信 high），但很多旧世界样本只有
  国家质心（level=0、置信 low），用 1 km 栅格是"假精度"，且体积大 20 倍。
  5 km 已经匹配最精细的定位精度，也足以刻画气温/降水梯度。

⚠️ 关键提醒（写进论文局限）：
  质心坐标提取的气候值是"该国的平均气候"，不等于采样点的真实气候。
  分析时要么只用高精度点（美国 143 个县级点），要么把坐标置信度作为敏感性分析的分层因素。

用法（WSL gea 环境）:
  python /mnt/c/SF_data/tools/extract_climate.py
"""
import os
import glob
import zipfile

import numpy as np
import rasterio

CLIM_DIR = "/home/hugo/data/climate"
GEO = "/mnt/c/SF_data/tools/cohort_s2_geo.tsv"
OUT = "/mnt/c/SF_data/tools/report/climate_s2.tsv"

os.makedirs(os.path.dirname(OUT), exist_ok=True)


def ensure_unzipped():
    zips = sorted(glob.glob(os.path.join(CLIM_DIR, "*.zip")))
    for zp in zips:
        try:
            zf0 = zipfile.ZipFile(zp)
            zf0.close()
        except zipfile.BadZipFile:
            print("  [跳过] %s 不是有效 zip（多半是上次没下完的残片）" % os.path.basename(zp))
            continue
        with zipfile.ZipFile(zp) as zf:
            names = zf.namelist()
            # 只需要 19 层 bio 和 elev，不要月度数据
            want = [n for n in names if n.endswith(".tif") and ("_bio_" in n or "_elev" in n)]
            have = set(os.path.basename(p) for p in glob.glob(os.path.join(CLIM_DIR, "*.tif")))
            todo = [n for n in want if os.path.basename(n) not in have]
            if todo:
                print("  解压 %s 中的 %d 个文件" % (os.path.basename(zp), len(todo)))
                zf.extractall(CLIM_DIR, members=todo)


def load_layers():
    layers = {}
    for i in range(1, 20):
        # ⚠️ 必须精确匹配 "_bio_N.tif"：用 "*bio_1*.tif" 会连 bio_10~bio_19 一起命中
        for cand in sorted(glob.glob(os.path.join(CLIM_DIR, "*_bio_%d.tif" % i))):
            layers["bio%d" % i] = rasterio.open(cand)
            break
    for cand in sorted(glob.glob(os.path.join(CLIM_DIR, "*elev*.tif"))):
        layers["elev"] = rasterio.open(cand)
        break
    return layers


def main():
    print("=== WorldClim 提取 ===")
    ensure_unzipped()
    layers = load_layers()
    names = ["bio%d" % i for i in range(1, 20)] + (["elev"] if "elev" in layers else [])
    print("  已载入 %d 层: %s" % (len(names), ",".join(names[:5]) + " ... " + ",".join(names[-3:])))

    # 读坐标
    rows = []
    with open(GEO, encoding="utf-8") as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        ci = {k: i for i, k in enumerate(hdr)}
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 5:
                continue
            lat = p[ci["lat"]] if "lat" in ci else ""
            lon = p[ci["lon"]] if "lon" in ci else ""
            try:
                lat = float(lat); lon = float(lon)
            except ValueError:
                lat = lon = None
            rows.append(dict(run=p[0], module=p[ci.get("module", 2)],
                             country=p[ci["country"]] if "country" in ci else "",
                             subnational=p[ci["subnational"]] if "subnational" in ci else "",
                             level=p[ci["level"]] if "level" in ci else "",
                             conf=p[ci["confidence"]] if "confidence" in ci else "",
                             lat=lat, lon=lon))
    print("  队列样本: %d 个" % len(rows))

    # 逐点采样
    out = []
    nodata_pts = []
    for r in rows:
        rec = dict(r)
        if r["lat"] is None:
            rec.update({k: "" for k in names})
            nodata_pts.append(r["run"])
            out.append(rec)
            continue
        pt = [(r["lon"], r["lat"])]
        for k in names:
            src = layers[k]
            try:
                v = list(src.sample(pt))[0][0]
            except Exception:
                v = np.nan
            if src.nodata is not None and v == src.nodata:
                v = np.nan
            rec[k] = "" if (v is None or (isinstance(v, float) and np.isnan(v))) else round(float(v), 2)
            if rec[k] == "":
                nodata_pts.append(r["run"])
        out.append(rec)

    cols = ["run", "module", "country", "subnational", "level", "conf", "lat", "lon"] + names
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for rec in out:
            fh.write("\t".join("" if rec.get(c) is None else str(rec.get(c)) for c in cols) + "\n")
    print("  已写出: %s" % OUT)
    if nodata_pts:
        print("  ⚠ 落在栅格空值（多半是海面）的样本 %d 个: %s"
              % (len(set(nodata_pts)), ",".join(sorted(set(nodata_pts))[:8])))

    # ---- 各模块气候概况 ----
    print()
    print("=== 各模块气候概况（BIO1 年均温 ℃ / BIO12 年降水 mm）===")
    by = {}
    for rec in out:
        by.setdefault(rec["module"], []).append(rec)
    print("%-4s %5s %10s %10s %12s %10s" % ("模块", "样本", "BIO1均值", "BIO1范围", "BIO12均值", "BIO12范围"))
    for m in sorted(by, key=lambda k: -len(by[k])):
        v1 = [float(x["bio1"]) for x in by[m] if x["bio1"] != ""]
        v12 = [float(x["bio12"]) for x in by[m] if x["bio12"] != ""]
        if not v1:
            continue
        print("%-4s %5d %10.1f %10s %12.0f %10s" % (
            m, len(by[m]), sum(v1) / len(v1), "%.1f~%.1f" % (min(v1), max(v1)),
            sum(v12) / len(v12), "%.0f~%.0f" % (min(v12), max(v12))))

    # ---- 美国内部气候梯度（能做 GEA 的战场）----
    us = [x for x in out if x["module"] == "US" and x["lat"] and x["bio1"] != ""]
    if len(us) > 10:
        print()
        print("=== 美国模块内部：纬度 vs 气候（这是唯一能做梯度分析的模块）===")
        lat = np.array([float(x["lat"]) for x in us])
        b1 = np.array([float(x["bio1"]) for x in us])
        b4 = np.array([float(x["bio4"]) for x in us])   # 温度季节性
        b12 = np.array([float(x["bio12"]) for x in us])
        b11 = np.array([float(x["bio11"]) for x in us])  # 最冷季均温
        for lbl, v in [("BIO1 年均温", b1), ("BIO4 温度季节性", b4),
                       ("BIO12 年降水", b12), ("BIO11 最冷季均温", b11)]:
            print("  %-16s 与纬度 r = %+.3f   （范围 %.1f ~ %.1f）"
                  % (lbl, float(np.corrcoef(lat, v)[0, 1]), v.min(), v.max()))


if __name__ == "__main__":
    main()
