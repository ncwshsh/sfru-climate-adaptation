# -*- coding: utf-8 -*-
"""路线 2：把研究面板代号从地理暗示型改为中性 P1–P6。

映射（按数据量降序，P1 = 最大面板）：
    US -> P1   (n = 143)
    BR -> P2   (n = 24 分析队列 / 30 下载)
    AF -> P3   (n = 16)
    AM -> P4   (n = 15)
    CN -> P5   (n = 10)
    FL -> P6   (n = 6)

设计原则：
  * 绝不就地改写原始数据文件——一律生成新的 P 版文件，旧的保留为溯源
  * 映射表落盘为 panel_map.tsv，供编辑与审稿人核对
  * 只动「作为标签出现」的代码，不动可能误伤的单词（如 US 在英文里是代词）
"""
import io, os, re, sys

MAP = {"US": "P1", "BR": "P2", "AF": "P3", "AM": "P4", "CN": "P5", "FL": "P6"}
REV = {v: k for k, v in MAP.items()}

REPORT = r"C:\SF_data\tools\report"

# ---------------------------------------------------------------- 1. 映射表
def write_map():
    rows = [
        ("new_code", "old_code", "n_analysis", "n_downloaded", "coordinate_precision",
         "countries", "note"),
        ("P1", "US", "143", "143", "county-level (high)", "2 (USA, Puerto Rico)",
         "137 continental USA + 6 Puerto Rico"),
        ("P2", "BR", "24", "30", "county-level (high)", "1 (Brazil)",
         "6 low-mapping libraries excluded before analysis"),
        ("P3", "AF", "16", "16", "country centroid (low)", "8",
         "Zambia, China, Malaysia, Ghana, Malawi, Rwanda, Kenya, Sudan (2 each)"),
        ("P4", "AM", "15", "15", "country centroid (low)", "5",
         "Brazil, USA, Puerto Rico, Argentina, Kenya (3 each)"),
        ("P5", "CN", "10", "10", "province-level (medium)", "1 (China)", ""),
        ("P6", "FL", "6", "6", "county-level (high)", "1 (USA, Florida)", ""),
    ]
    out = os.path.join(REPORT, "panel_map.tsv")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write("\t".join(r) + "\n")
    print(f"[map] wrote {out}")
    return out


# ------------------------------------------------- 2. 数据表：只换 module 列
def convert_table(src, dst, sep="\t"):
    with io.open(src, encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split(sep)
        body = [ln.rstrip("\n").split(sep) for ln in f if ln.strip()]
    mi = head.index("module")
    n_changed = 0
    for row in body:
        if row[mi] in MAP:
            row[mi] = MAP[row[mi]]
            n_changed += 1
    with io.open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(sep.join(head) + "\n")
        for row in body:
            f.write(sep.join(row) + "\n")
    print(f"[table] {os.path.basename(src)} -> {os.path.basename(dst)} "
          f"({n_changed}/{len(body)} rows recoded)")
    return n_changed


def main():
    write_map()
    to_convert = ["gea_input.tsv", "qc_s2_bm2k15.tsv",
                  "strain_covariate.tsv", "strain_predicted.tsv"]
    for fn in to_convert:
        src = os.path.join(REPORT, fn)
        if not os.path.exists(src):
            print(f"[skip] {fn} not found")
            continue
        base, ext = os.path.splitext(fn)
        dst = os.path.join(REPORT, f"{base}_P{ext}")
        convert_table(src, dst)
    print("\n完成。原文件保留未动；新文件后缀 _P.tsv。")
    print("下一步：改写 paper_figs_pub.py 用 PALETTE/PNAME，并指向 _P.tsv。")


if __name__ == "__main__":
    main()
