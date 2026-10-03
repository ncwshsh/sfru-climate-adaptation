# -*- coding: utf-8 -*-
r"""修复"末块被截断"的 BGZF 文件（bgzip / htslib 输出）。

【症状】`gzip -t` 报错、`zcat` 报 "unexpected end of file"，但文件大部分是好的。
【成因】写入进程被中断/磁盘满 → 最后一个 BGZF 块没写完；BGZF 的 28 字节 EOF marker 也缺失。
【原理】BGZF = 一串独立的 gzip 成员，每块自带 CRC32+ISIZE 校验。
        ⇒ 把残缺的**最后一块**丢掉，再补上标准 28 字节 EOF marker，文件即恢复合法。
【代价】丢失 ≤ 1 个块（≤65,280 字节未压缩），对 beagle 约十几行。

用法:
  python -S repair_bgzf.py <源文件> [目标文件]
不加目标文件则输出到 <源文件>.repaired.gz
"""
import os, sys, zlib, time

sys.stdout.reconfigure(encoding='utf-8')

BGZF_EOF = bytes.fromhex(
    '1f8b08040000000000ff0600424302001b0003000000000000000000')  # 标准 28 字节 EOF marker


def scan(path, verbose=True):
    """逐块扫描，返回 (完整块数, 末块边界偏移, 解压字节, 行数, 状态)"""
    sz = os.path.getsize(path)
    nblk = tot = nl = off = 0
    status = 'OK'
    with open(path, 'rb') as f:
        while off < sz:
            f.seek(off)
            hdr = f.read(12)
            if len(hdr) < 12:
                status = 'SHORT_HEADER'; break
            if hdr[0] != 0x1f or hdr[1] != 0x8b or hdr[2] != 8:
                status = 'BAD_MAGIC'; break
            xlen = int.from_bytes(hdr[10:12], 'little')
            extra = f.read(xlen)
            if len(extra) < xlen:
                status = 'SHORT_EXTRA'; break
            bsize = None
            i = 0
            while i + 4 <= len(extra):
                if extra[i] == 66 and extra[i + 1] == 67:
                    sl = int.from_bytes(extra[i + 2:i + 4], 'little')
                    if sl >= 2:
                        bsize = int.from_bytes(extra[i + 4:i + 4 + sl], 'little') + 1
                i += 4 + int.from_bytes(extra[i + 2:i + 4], 'little')
            if bsize is None:
                status = 'NO_BC'; break
            remain = bsize - 12 - xlen
            rest = f.read(remain)
            if len(rest) < remain:
                status = 'TRUNCATED_BLOCK(声明 %d，实读 %d，缺 %d)' % (
                    bsize, 12 + xlen + len(rest), remain - len(rest))
                break
            try:
                out = zlib.decompress(rest[:-8], -15)
            except zlib.error as e:
                status = 'DEFLATE_ERROR(%s)' % e; break
            nblk += 1; tot += len(out); nl += out.count(b'\n')
            off += bsize
            if verbose and nblk % 300000 == 0:
                print('    ... %d 块 / %.2f GB' % (nblk, tot / 1024**3))
    return nblk, off, tot, nl, status


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if not src:
        print(__doc__); sys.exit(1)
    dst = sys.argv[2] if len(sys.argv) > 2 else src + '.repaired.gz'

    sz = os.path.getsize(src)
    print('源  : %s  (%.3f GB)' % (src, sz / 1024**3))
    print('目标: %s' % dst)

    print('\n[1/3] 扫描源文件，定位最后一个完整块')
    t0 = time.time()
    nblk, good, tot, nl, status = scan(src)
    print('  完整块 %d / 解压 %.3f GB / %d 行 / %.0fs' % (nblk, tot / 1024**3, nl, time.time() - t0))
    print('  状态: %s' % status)

    if status == 'OK':
        print('  ⇒ 全部块完好（可能只是缺 EOF marker）')

    print('\n[2/3] 截取前 %d 字节 + 追加 BGZF EOF marker' % good)
    with open(src, 'rb') as fi, open(dst, 'wb') as fo:
        left = good
        while left:
            b = fi.read(min(8 << 20, left))
            if not b:
                break
            fo.write(b); left -= len(b)
        fo.write(BGZF_EOF)
    print('  写出 %d 字节 (%.3f GB)' % (os.path.getsize(dst), os.path.getsize(dst) / 1024**3))

    print('\n[3/3] 校验修复结果')
    n2, good2, tot2, nl2, st2 = scan(dst)
    print('  完整块 %d / 解压 %.3f GB / %d 行' % (n2, tot2 / 1024**3, nl2))
    print('  状态: %s' % st2)
    with open(dst, 'rb') as f:
        f.seek(-28, 2); mk = f.read()
    print('  EOF marker: %s' % ('存在 ✓' if mk == BGZF_EOF else '缺失 ✗'))
    print('  数据保留率: %.6f%%  (丢 %d 行, 原 %d 行)' % (
        100.0 * nl2 / nl if nl else 0, (nl - nl2) if nl else 0, nl))


if __name__ == '__main__':
    main()
