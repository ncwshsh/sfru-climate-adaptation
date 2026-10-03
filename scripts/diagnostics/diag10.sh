#!/bin/bash
# 干净版 v2: 只看 A、B 双方都有 >=5 条读段的位点, 比较共有碱基
# 关键修复: mpileup 用 '.'(正链) / ','(负链) 表示"与参考一致", 必须计入参考碱基
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin
set -u
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna

# 选最长染色体, 取中段 1 Mb (避开端粒/着丝粒重复区)
BEST=$(sort -k2,2nr "${REF}.fai" | head -1)
CHR=$(echo "$BEST" | cut -f1)
LEN=$(echo "$BEST" | cut -f2)
MID=$(( LEN/2 ))
START=$(( MID - 500000 ))
REG="${CHR}:${START}-$((START+1000000))"
echo "选取区段: $REG  (染色体长 $LEN bp)"

A=/home/hugo/data/03_align/SRR11528381.dedup.bam
B=/home/hugo/data/03_align/SRR12044628.dedup.bam

samtools mpileup -f "$REF" -r "$REG" -q 20 -Q 20 -d 3000 "$A" "$B" 2>/dev/null \
| python3 -c '
import sys, re
MIN=5
indel=re.compile(r"[+-][0-9]+[ACGTNacgtn]+")
notread=re.compile(r"\^.")
def maj(b, ref):
    s=indel.sub("", notread.sub("", b))
    cnt={"A":0,"C":0,"G":0,"T":0}; n=0
    for ch in s:
        if ch=="." or ch==",": cnt[ref]+=1; n+=1
        else:
            u=ch.upper()
            if u in cnt: cnt[u]+=1; n+=1
    if n==0: return None,0
    top=max(cnt,key=cnt.get)
    return top, cnt[top]/n

n_both=nA=nB=0
A_ne=B_ne=A_ne_B=0
A_hi=B_hi=0
row=[]
vs=[]
for line in sys.stdin:
    f=line.rstrip("\n").split("\t")
    if len(f)<9: continue
    ref=f[2].upper()
    if ref not in ("A","C","G","T"): continue
    try: dA=int(f[3]); dB=int(f[6])
    except: continue
    if dA<MIN or dB<MIN: continue
    mA,cA=maj(f[4],ref); mB,cB=maj(f[7],ref)
    if mA is None or mB is None: continue
    n_both+=1
    if cA>=0.8: A_hi+=1
    if cB>=0.8: B_hi+=1
    if mA!=ref: A_ne+=1; vs.append((ref,mA))
    if mB!=ref: B_ne+=1
    if mA!=mB:  A_ne_B+=1
TS={("A","G"),("G","A"),("C","T"),("T","C")}
print(f"双方均覆盖(>={MIN}读)的位点        n = {n_both:,}")
if n_both:
    print(f"A(SRR11528381,中国浙江) != 参考     {A_ne:>8,}  -> {100*A_ne/n_both:.4f}%")
    print(f"B(SRR12044628,美国)     != 参考     {B_ne:>8,}  -> {100*B_ne/n_both:.4f}%")
    print(f"A != B                              {A_ne_B:>8,}  -> {100*A_ne_B/n_both:.4f}%")
    print(f"主碱基一致度>=0.8 的位点: A={100*A_hi/n_both:.1f}%  B={100*B_hi/n_both:.1f}%")
    ts=sum(1 for p in vs if p in TS); tv=len(vs)-ts
    print(f"\n[A!=参考 位点的碱基替换谱]  Ts={ts:,}  Tv={tv:,}  Ts/Tv={ts/tv if tv else 0:.3f}")
    sub={}
    for a,b in vs: sub[a+b]=sub.get(a+b,0)+1
    top=sorted(sub.items(), key=lambda x:-x[1])[:8]
    print("  最常见替换: " + "  ".join(f"{k}:{v}" for k,v in top))
'
