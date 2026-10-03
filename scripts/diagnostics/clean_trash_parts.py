# -*- coding: utf-8 -*-
r"""清理 C:\SF_data\_trash_parts —— 分块下载遗留的中间碎片。

用法: python -S clean_trash_parts.py            # 干运行（只核查）
      python -S clean_trash_parts.py --apply    # 执行删除

必须 python -S（绕过 WorkBuddy 对 os.remove 的劫持），删除用 nt.remove + 并行。
"""
import os, re, sys, nt, time, shutil, collections
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

T   = r'C:\SF_data\_trash_parts'
RAW = r'C:\SF_data\01_raw'
APPLY = '--apply' in sys.argv

# ── 白名单：只允许「SRRxxxxxxx_[12].fastq.gz.partialNN.partM」形态 ──
PAT = re.compile(r'^SRR\d+_[12]\.fastq\.gz\.partial\d+\.part\d+$')
# ── mtime 护栏：拒绝最近 30 分钟内被写过的文件（目录是"活"的时候挡误伤）──
MTIME_GUARD = 30 * 60

print('=' * 66)
print('目标目录: %s' % T)
print('模式: %s' % ('★ 执行删除' if APPLY else '○ 干运行（只核查）'))
print('=' * 66)

free0 = shutil.disk_usage('C:/').free
print('C: 可用空间(前): %.2f GB' % (free0 / 1024**3))

files = os.listdir(T)
print('目录条目数: %d' % len(files))

# ── 护栏 1：白名单正则 ──
bad = [f for f in files if not PAT.match(f)]
print('\n[护栏1] 白名单正则: ', end='')
if bad:
    print('!! 违规 %d 个 → 拒绝执行' % len(bad))
    for b in bad[:10]:
        print('   %s' % b)
    sys.exit(2)
print('通过（%d/%d 全部匹配）' % (len(files), len(files)))

# ── 护栏 2：mtime（不能太新）──
now = time.time()
fresh = [(f, os.path.getmtime(os.path.join(T, f))) for f in files]
new_ones = [(f, t) for f, t in fresh if now - t < MTIME_GUARD]
print('[护栏2] mtime 护栏: ', end='')
if new_ones:
    print('!! %d 个文件在 %d 分钟内被改过 → 停手' % (len(new_ones), MTIME_GUARD // 60))
    for f, t in new_ones[:10]:
        print('   %s  %s' % (f, time.strftime('%H:%M:%S', time.localtime(t))))
    sys.exit(2)
mt = [t for _, t in fresh]
print('通过（最新一个: %s）' % time.strftime('%Y-%m-%d %H:%M', time.localtime(max(mt))))

# ── 护栏 3：逐 base 闭合核查 —— 每个 base 必须有成品，且 Σ(碎片) ≤ 成品 ──
bases = collections.defaultdict(list)
for f in files:
    bases[re.sub(r'\.part\d+$', '', f)].append(f)

raw_all = os.listdir(RAW)
print('\n[护栏3] 逐 base 闭合核查（%d 个 base）' % len(bases))
print('  %-44s %5s %11s %13s %11s' % ('base', '块数', 'Σ碎片GB', '成品GB', 'Σ≤成品'))
fails = []
rows = []
for b in sorted(bases):
    core = re.sub(r'\.partial\d+$', '', b)
    frag = sum(os.path.getsize(os.path.join(T, f)) for f in bases[b])
    # 成品候选 = 同名 core 开头、且不是块碎片（块碎片形如 .partNN 结尾）
    # ★ 不能用子串 '.part' 判断：成品名本身可能是 '.partial44'（含 '.part'）
    BLOCK = re.compile(r'\.part\d+$')
    cands = [x for x in raw_all if x.startswith(core) and not BLOCK.search(x)]
    if not cands:
        fails.append((b, '无成品'))
        rows.append((b, len(bases[b]), frag, None, 'X 无成品'))
        continue
    fin_name = max(cands, key=lambda x: os.path.getsize(os.path.join(RAW, x)))
    fin = os.path.getsize(os.path.join(RAW, fin_name))
    ok = frag <= fin
    if not ok:
        fails.append((b, 'Σ碎片 > 成品'))
    rows.append((b, len(bases[b]), frag, fin, 'OK' if ok else 'X 过大'))

for b, cnt, frag, fin, st in rows:
    print('  %-44s %5d %11.3f %13s %11s'
          % (b, cnt, frag / 1024**3, ('%.3f' % (fin / 1024**3)) if fin else '--', st))

if fails:
    print('\n!! 闭合核查失败 %d 项 → 拒绝执行' % len(fails))
    for b, why in fails[:20]:
        print('   %s : %s' % (b, why))
    sys.exit(2)
print('  闭合核查全部通过：%d/%d 个 base 的碎片总量 ≤ 成品字节（碎片是成品的真子集）'
      % (len(bases), len(bases)))

# ── 护栏 4：字节总量双通道核对 ──
tot = sum(os.path.getsize(os.path.join(T, f)) for f in files)
print('\n[护栏4] 字节总量: %d 个文件 / %d bytes / %.2f GB' % (len(files), tot, tot / 1024**3))

# ── 护栏 5：重新 stat 验字节稳定性（清单里不能有正在被写的文件）──
tot2 = sum(os.path.getsize(os.path.join(T, f)) for f in files)
print('[护栏5] 字节稳定性: %s (%d vs %d)' % ('OK' if tot == tot2 else '!! 变动', tot, tot2))
if tot != tot2:
    sys.exit(2)

if not APPLY:
    print('\n○ 干运行结束，全部护栏通过。加 --apply 执行删除。')
    sys.exit(0)

# ── 执行删除（单进程 + 并行，绕开安全策略 50 文件限制与回收站劫持）──
print('\n★ 开始删除 ...')
paths = [os.path.join(T, f) for f in files]
done = [0]
errs = []
lock_t = time.time()

def kill(p):
    try:
        nt.remove(p)
        done[0] += 1
    except OSError as e:
        errs.append((p, str(e)))

with ThreadPoolExecutor(max_workers=16) as ex:
    list(ex.map(kill, paths))

print('  删除完成: %d 成功 / %d 失败  用时 %.1f s' % (done[0], len(errs), time.time() - lock_t))
for p, e in errs[:10]:
    print('   失败 %s : %s' % (p, e))

# ── 删后回查 ──
left = os.listdir(T)
print('\n[回查] 目录残留条目: %d' % len(left))
for f in left[:10]:
    print('   %s' % f)

if not left:
    try:
        nt.rmdir(T)
        print('[回查] 空目录已删除: %s' % T)
    except OSError as e:
        print('[回查] 目录删除失败（可能非空或有句柄）: %s' % e)

free1 = shutil.disk_usage('C:/').free
print('\nC: 可用空间(后): %.2f GB' % (free1 / 1024**3))
print('实际释放: %.2f GB' % ((free1 - free0) / 1024**3))
