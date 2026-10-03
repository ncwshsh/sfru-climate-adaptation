#!/bin/bash
# 多区段稳健化: 取 4 条最长染色体的中段各 500 kb, 汇总估计全基因组口径的样本-参考分歧
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin
set -u
REF=/home/hugo/data/ref/ref_GCF_023101765.2.fna
A=/home/hugo/data/03_align/SRR11528381.dedup.bam
B=/home/hugo/data/03_align/SRR12044628.dedup.bam

REGS=""
while read -r chr len _; do
  mid=$(( len/2 )); st=$(( mid-250000 ))
  REGS="$REGS ${chr}:${st}-$((st+500000))"
done < <(sort -k2,2nr "${REF}.fai" | head -4)

for REG in $REGS; do
  echo "### $REG"
  samtools mpileup -f "$REF" -r "$REG" -q 20 -Q 20 -d 3000 "$A" "$B" 2>/dev/null \
  | python3 -c '
import sys, re
MIN=5
indel=re.compile(r"[+-][0-9]+[ACGTNacgtn]+"); notread=re.compile(r"\^.")
def maj(b, ref):
    s=indel.sub("", notread.sub("", b)); c={"A":0,"C":0,"G":0,"T":0}; n=0
    for ch in s:
        if ch in ".,": c[ref]+=1; n+=1
        else:
            u=ch.upper()
            if u in c: c[u]+=1; n+=1
    return (max(c,key=c.get), max(c.values())/n) if n else (None,0)
TS={("A","G"),("G","A"),("C","T"),("T","C")}
n=ane=bne=ab=ts=tv=0
for line in sys.stdin:
    f=line.rstrip("\n").split("\t")
    if len(f)<9: continue
    ref=f[2].upper()
    if ref not in ("A","C","G","T"): continue
    try: dA=int(f[3]); dB=int(f[6])
    except: continue
    if dA<MIN or dB<MIN: continue
    mA,_=maj(f[4],ref); mB,_=maj(f[7],ref)
    if mA is None or mB is None: continue
    n+=1
    if mA!=ref:
        ane+=1
        if (ref,mA) in TS: ts+=1
        else: tv+=1
    if mB!=ref: bne+=1
    if mA!=mB: ab+=1
print(f"  可用位点 n={n:,}   A!=参考 {100*ane/n:.4f}%   B!=参考 {100*bne/n:.4f}%   A!=B {100*ab/n:.4f}%   Ts/Tv={ts/tv if tv else 0:.3f}")
'
done
