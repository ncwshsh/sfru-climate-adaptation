import os, time, sys

src = r"C:\SF_data\01_raw"
dst = r"C:\SF_data\_trash_parts"
os.makedirs(dst, exist_ok=True)

fs = [f for f in os.listdir(src) if '.partial' in f and '.part' in f.split('.partial')[-1]]
print("待移动:", len(fs), flush=True)

t = time.time(); ok = err = 0
for i, f in enumerate(fs):
    try:
        os.replace(os.path.join(src, f), os.path.join(dst, f)); ok += 1
    except Exception as e:
        err += 1
        if err < 5:
            print("ERR", f, e, flush=True)
    if i % 1000 == 0:
        print(f"  {i}/{len(fs)}  {time.time()-t:.0f}s", flush=True)

print(f"完成: 移动{ok} 失败{err} 用时{time.time()-t:.0f}s", flush=True)

left = [f for f in os.listdir(src) if '.partial' in f and '.part' in f.split('.partial')[-1]]
bare = [f for f in os.listdir(src) if '.partial' in f and not '.part' in f.split('.partial')[-1]]
done = [f for f in os.listdir(src) if f.endswith('.fastq.gz')]
print("剩余分片段:", len(left), flush=True)
print("裸partial:", len(bare), flush=True)
print("已修复成品:", len(done), flush=True)
