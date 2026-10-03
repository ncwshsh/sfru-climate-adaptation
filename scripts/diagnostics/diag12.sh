#!/bin/bash
# 严格过滤下重测: 深度>=20, MAPQ>=40, 主碱基一致度>=0.9
# 若 Ts/Tv 显著抬升 -> 宽松条件下确实混着错配假象; 若不动 -> Ts/Tv 低是该物种固有
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
  samtools mpileup -f "$REF" -r "$REG" -q 40 -Q 25 -d 5000 "$A" "$B" 2>/dev/null \
  | python3 -c '
import sys, re
LMIN=5; SMIN=20
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
lo=[0,0,0,0]   # n, A!=ref, ts, tv
st=[0,0,0,0]
for line in sys.stdin:
    f=line.rstrip("\n").split("\t")
    if len(f)<9: continue
    ref=f[2].upper()
    if ref not in ("A","C","G","T"): continue
    try: dA=int(f[3]); dB=int(f[6])
    except: continue
    if dA<LMIN or dB<LMIN: continue
    mA,cA=maj(f[4],ref); mB,cB=maj(f[7],ref)
    if mA is None or mB is None: continue
    lo[0]+=1
    if mA!=ref:
        lo[1]+=1
        lo[2 if (ref,mA) in TS else 3]+=1
    if dA>=SMIN and dB>=SMIN and cA>=0.9 and cB>=0.9:
        st[0]+=1
        if mA!=ref:
            st[1]+=1
            st[2 if (ref,mA) in TS else 3]+=1
def show(tag,t):
    n,r,ts,tv=t
    print(f"  {tag:<28} n={n:>7,}  A!=ref={100*r/n:6.4f}%  Ts/Tv={ts/tv if tv else 0:.3f}")
show("宽松(>=5读,MAPQ20)", lo)
show("严格(>=20读,MAPQ40,>=0.9)", st)
'
done
