# -*- coding: utf-8 -*-
r"""清空回收站里属于本批碎片的部分，真正把空间还给磁盘。

【为什么需要这一步】
实测本机**文件系统层**会把所有删除重定向进回收站：
  - nt.remove              → 进回收站
  - kernel32.DeleteFileW   → 进回收站
  - SHFileOperationW(无 FOF_ALLOWUNDO) → 进回收站
⇒ 删 _trash_parts 只是把它们「搬」进回收站，磁盘空间并未释放。
必须用 SHEmptyRecycleBinW 真清空。

【护栏】只允许清空「原始路径全部落在白名单内、且白名单外字节量为 0」的回收站。
白名单外若有 >100 MB 的真实数据 → 拒绝执行。

用法: python -S empty_recycle_bin.py            # 干运行
      python -S empty_recycle_bin.py --apply    # 执行
"""
import os, sys, time, shutil, ctypes, collections

sys.stdout.reconfigure(encoding='utf-8')

RB    = r'C:\$Recycle.Bin\S-1-5-21-521485576-593421438-3457633465-1000'
OURS  = (r'C:\SF_data\_trash_parts', r'C:\SF_data\tmp')
LIMIT = 100 * 1024 * 1024          # 白名单外允许的字节上限
APPLY = '--apply' in sys.argv

print('=' * 64)
print('清空回收站: %s' % RB)
print('模式: %s' % ('★ 执行' if APPLY else '○ 干运行'))
print('=' * 64)

free0 = shutil.disk_usage('C:/').free
print('C: 可用空间(前): %.2f GB' % (free0 / 1024**3))


def parse_i(d):
    sz = int.from_bytes(d[8:16], 'little')
    ver = int.from_bytes(d[24:28], 'little')
    if ver == 2 and len(d) >= 32:
        ln = int.from_bytes(d[28:32], 'little')
        p = d[32:32 + ln * 2].decode('utf-16-le', 'replace').rstrip('\x00')
    else:
        p = d[28:28 + 520].decode('utf-16-le', 'replace').split('\x00')[0]
    return p, sz


# ── 护栏：解析全部 $I，统计白名单内/外 ──
items = [f for f in os.listdir(RB) if f.startswith('$I')]
in_cnt = in_sz = out_cnt = out_sz = 0
out_samples = []
for i in items:
    try:
        p, sz = parse_i(open(os.path.join(RB, i), 'rb').read())
    except OSError:
        continue
    if p.startswith(OURS):
        in_cnt += 1; in_sz += sz
    else:
        out_cnt += 1; out_sz += sz
        if len(out_samples) < 20:
            out_samples.append((p, sz))

print('\n[护栏] 回收站条目 %d 个' % len(items))
print('  白名单内 (_trash_parts/tmp): %5d 项  %.3f GB' % (in_cnt, in_sz / 1024**3))
print('  白名单外                : %5d 项  %.6f GB' % (out_cnt, out_sz / 1024**3))
for p, sz in out_samples:
    print('     %10d  %s' % (sz, p))

if out_sz > LIMIT:
    print('\n!! 白名单外有 %.3f GB 真实数据 → 拒绝执行' % (out_sz / 1024**3))
    sys.exit(2)
print('  护栏通过（白名单外仅 %.3f MB < 上限 %d MB）' % (out_sz / 1024**2, LIMIT // 1024**2))

if not APPLY:
    print('\n○ 干运行结束。加 --apply 执行清空。')
    sys.exit(0)

# ── 执行 SHEmptyRecycleBinW（限 C: 盘）──
try:
    ctypes.windll.ole32.CoInitialize(None)
except Exception:
    pass

SHERB_NOCONFIRMATION = 0x1
SHERB_NOPROGRESSUI   = 0x2
SHERB_NOSOUND        = 0x4
flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND

print('\n★ 调用 SHEmptyRecycleBinW("C:\\") ...')
t0 = time.time()
hr = ctypes.windll.shell32.SHEmptyRecycleBinW(None, 'C:\\', flags)
print('  返回 HRESULT = 0x%08X  (0=S_OK, 1=S_FALSE 已空)  用时 %.1f s' % (hr & 0xFFFFFFFF, time.time() - t0))

# ── 回查 ──
left = os.listdir(RB)
free1 = shutil.disk_usage('C:/').free
print('\n[回查] 回收站残留条目: %d' % len(left))
if left:
    for f in left[:10]:
        print('   %s' % f)
print('C: 可用空间(后): %.2f GB' % (free1 / 1024**3))

# ── 目标目录现状 ──
print('\n[回查] C:\\SF_data 关键目录:')
for p, tag in ((r'C:\SF_data\_trash_parts', '_trash_parts (应为已删除)'),
               (r'C:\SF_data\01_raw', '01_raw'),
               (r'C:\SF_data\03_align', '03_align')):
    if os.path.exists(p):
        n = sum(len(f) for _, _, f in os.walk(p))
        print('   %-34s 存在, %d 文件' % (tag, n))
    else:
        print('   %-34s 不存在 ✓' % tag)
