#!/bin/bash
# 线粒体重测 v3: 取样 -> 比对到线粒体 -> 多数碱基比较
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin
set -u
MT=/home/hugo/data/ref/NC_027836.1.fa
[ -f "$MT" ] || curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_027836.1&rettype=fasta&retmode=text" -o "$MT"
samtools faidx "$MT"
mkdir -p /tmp/mt
CHR=$(cut -f1 "${MT}.fai" | head -1)
LEN=$(cut -f2 "${MT}.fai" | head -1)
echo "线粒体 $CHR  $LEN bp"

for S in SRR11528381 SRR12044628; do
  R1=/home/hugo/data/01_raw/${S}_1.fastq.gz
  R2=/home/hugo/data/01_raw/${S}_2.fastq.gz
  echo "--- $S 取样 200 万对读段 ---"
  pigz -dc "$R1" 2>/dev/null | head -8000000 > /tmp/mt/${S}_1.fq
  pigz -dc "$R2" 2>/dev/null | head -8000000 > /tmp/mt/${S}_2.fq
  minimap2 -ax sr -t 8 --secondary=no "$MT" /tmp/mt/${S}_1.fq /tmp/mt/${S}_2.fq 2>/dev/null \
    | samtools sort -@ 2 -o /tmp/mt/${S}.bam -
  samtools index /tmp/mt/${S}.bam
  echo "  比对到线粒体的读段 = $(samtools view -c /tmp/mt/${S}.bam)"
done

samtools mpileup -f "$MT" -r "${CHR}:1-${LEN}" -q 20 -Q 20 -d 5000 \
  /tmp/mt/SRR11528381.bam /tmp/mt/SRR12044628.bam 2>/dev/null \
| python3 -c '
import sys, re
MIN=5
indel=re.compile(r"[+-][0-9]+[ACGTNacgtn]+"); notread=re.compile(r"\^.")
def maj(b, ref):
    s=indel.sub("", notread.sub("", b)); cnt={"A":0,"C":0,"G":0,"T":0}; n=0
    for ch in s:
        if ch in ".,": cnt[ref]+=1; n+=1
        else:
            u=ch.upper()
            if u in cnt: cnt[u]+=1; n+=1
    return (max(cnt,key=cnt.get), max(cnt.values())/n) if n else (None,0)
TS={("A","G"),("G","A"),("C","T"),("T","C")}
n=ane=bne=ab=0; vs=[]; ah=bh=0
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
    n+=1
    if cA>=0.8: ah+=1
    if cB>=0.8: bh+=1
    if mA!=ref: ane+=1; vs.append((ref,mA))
    if mB!=ref: bne+=1
    if mA!=mB: ab+=1
print(f"\n线粒体 双方均覆盖(>={MIN}读)位点  n = {n:,}")
if n:
    print(f"A(中国浙江) != 线粒体参考   {ane:>6,}  -> {100*ane/n:.3f}%")
    print(f"B(美国)     != 线粒体参考   {bne:>6,}  -> {100*bne/n:.3f}%")
    print(f"A != B                      {ab:>6,}  -> {100*ab/n:.3f}%")
    print(f"一致度>=0.8: A={100*ah/n:.1f}%  B={100*bh/n:.1f}%")
    ts=sum(1 for p in vs if p in TS); tv=len(vs)-ts
    print(f"Ts={ts}  Tv={tv}  Ts/Tv={ts/tv if tv else 0:.3f}")
'
