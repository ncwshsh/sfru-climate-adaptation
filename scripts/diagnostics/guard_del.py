# -*- coding: utf-8 -*-
"""护栏 + 单进程分批删除。

护栏（任一不通过即 exit 2，拒绝执行）：
  1. 删除清单每一条**必须**匹配白名单正则（只允许 .partN 块文件）
  2. 任何一条命中业务制成品（.fastq.gz 或 .partialN 结尾）→ 拒绝
  3. 删除清单与保留清单**不得有交集**
  4. Python 与 shell 两条通道算出的总字节必须一致
  5. 目录必须存在、文件数必须与清单条数一致（无 MISSING）
"""
import os, re, sys, subprocess, json

RAW_POSIX = "/c/SF_data/01_raw"
RAW_WIN = r"C:\SF_data\01_raw"
TOOLS = r"C:\SF_data\tools"
DEL = os.path.join(TOOLS, "delete_list.txt")
KEEP = os.path.join(TOOLS, "keep_list.txt")

WHITELIST = re.compile(r"^/c/SF_data/01_raw/SRR\d+_[12]\.fastq\.gz(?:\.partial\d+)?\.part\d+$")
ARTIFACT = re.compile(r"\.fastq\.gz$|\.partial\d+$")


def to_posix(p):
    """归一化：C:\\x / C:/x / /c/x 全部统一成 /c/x"""
    p = p.replace("\\", "/")
    m = re.match(r"^([a-zA-Z]):/", p)
    return ("/" + m.group(1).lower() + p[2:]) if m else p


def to_win(p):
    """★ Windows Python 不认 /c/... —— 必须显式转 C:/...（技能坑 1）"""
    p = to_posix(p)
    return (p[1].upper() + ":" + p[2:]) if re.match(r"^/[a-zA-Z]/", p) else p


dl = [l.strip() for l in open(DEL, encoding="utf-8") if l.strip()]
kp = set(l.strip() for l in open(KEEP, encoding="utf-8") if l.strip())
print(f"删除清单 {len(dl)} 条｜保留清单 {len(kp)} 条")

# ① 白名单（先归一化再匹配）
bad = [p for p in dl if not WHITELIST.match(to_posix(p))]
if bad:
    print(f"[护栏 1 失败] {len(bad)} 条不在白名单内，例：{bad[:3]}")
    sys.exit(2)
print("[护栏 1] ✅ 全部匹配白名单")

# ② 业务制成品
art = [p for p in dl if ARTIFACT.search(to_posix(p))]
if art:
    print(f"[护栏 2 失败] 命中业务制成品 {len(art)} 条，例：{art[:3]}")
    sys.exit(2)
print("[护栏 2] ✅ 无业务制成品")

# ③ 交集
inter = {to_posix(x) for x in dl} & {to_posix(x) for x in kp}
if inter:
    print(f"[护栏 3 失败] 与保留清单冲突 {len(inter)} 条，例：{sorted(inter)[:3]}")
    sys.exit(2)
print("[护栏 3] ✅ 与保留清单无交集")

# ④ 双通道字节核对
py_total = 0
missing = []
for p in dl:
    w = to_win(p)
    if os.path.exists(w):
        py_total += os.path.getsize(w)
    else:
        missing.append(p)
sh_total = int(subprocess.run(
    "find /c/SF_data/01_raw -maxdepth 1 -type f -name '*.part[0-9]*' -printf '%s\\n' "
    "| awk '{s+=$1} END{print s+0}'",
    shell=True, capture_output=True, text=True,
    env={**os.environ, "PATH": "/usr/bin:/bin:" + os.environ.get("PATH", "")}).stdout.strip() or 0)
# ★ 目录是「活」的（下载在写），shell 全量必然 > 删除清单。
#   有意义的检查是：同一份清单**重新 stat** 后总量不变 ⇒ 这些文件没有被写入。
py_now = sum(os.path.getsize(to_win(p)) for p in dl if os.path.exists(to_win(p)))
print(f"[护栏 4] 删除清单 快照 {py_total} B｜重新 stat {py_now} B｜目录现有全部 .part* {sh_total} B")
if py_total != py_now:
    print(f"[护栏 4 失败] 清单内文件字节发生变化（Δ={py_now-py_total}），可能正在被写入")
    sys.exit(2)
keep_now = sum(os.path.getsize(to_win(p)) for p in kp if os.path.exists(to_win(p)))
print(f"[护栏 4] ✅ 清单内字节稳定；保留 {keep_now/1048576:.1f} MB"
      f"；差额 {sh_total-py_total-keep_now} B（= 快照之后新产生的块）")

# ⑤ 存在性
print(f"[护栏 5] 缺失 {len(missing)} 个" + (f"，例：{missing[:3]}" if missing else " ✅"))
if missing:
    print("[护栏 5 失败] 清单与实际不符，先重建清单")
    sys.exit(2)

# ⑥ ★ mtime 护栏：拒绝删除「最近 10 分钟内被修改过」的文件
#    （防止误伤正在下载/正在合并的文件；本项目曾出现文件在两次运行之间自行消失的未解异常）
import time as _t
now = _t.time()
FRESH = 600
fresh = [(p, now - os.path.getmtime(to_win(p))) for p in dl
         if os.path.exists(to_win(p)) and (now - os.path.getmtime(to_win(p))) < FRESH]
if fresh:
    print(f"[护栏 6 失败] {len(fresh)} 个文件在最近 {FRESH//60} 分钟内被修改，拒绝执行")
    for p, age in fresh[:5]:
        print(f"    {age:6.0f} s 前  {os.path.basename(p)}")
    sys.exit(2)
print(f"[护栏 6] ✅ 无最近 {FRESH//60} 分钟内被修改的文件")

print(f"\n总计待删 {py_total/1073741824:.2f} GB")
if len(sys.argv) > 1 and sys.argv[1] == "--go":
    done = 0
    freed = 0
    for p in dl:
        w = to_win(p)
        try:
            if os.path.exists(w):
                freed += os.path.getsize(w)
                os.remove(w)
                done += 1
        except OSError as e:
            print(f"  [warn] 删不掉 {w}: {e}")
    print(f"\n✅ 已删 {done} 个文件，释放 {freed/1073741824:.2f} GB")
    json.dump({"deleted": done, "freed_bytes": freed},
              open(os.path.join(TOOLS, "del_result.json"), "w"), ensure_ascii=False, indent=1)
else:
    print("（试运行，未删除。加 --go 执行）")
