#!/bin/bash
# 用与 diag10 相同的干净方法(多数碱基、双方>=5读)重测线粒体分歧
export PATH=/home/hugo/mamba/envs/sfru/bin:/usr/bin:/bin
set -u

MT=""
for c in /home/hugo/data/ref/NC_027836.1.fa /home/hugo/data/ref/NC_027836.1.fasta \
         /home/hugo/data/ref/mt.fa /tmp/NC_027836.1.fa /home/hugo/data/03_align/NC_027836.1.fna; do
  [ -f "$c" ] && MT="$c" && break
done
if [ -z "$MT" ]; then
  echo "本地无线粒体 fasta, 现下载..."
  mkdir -p /home/hugo/data/ref
  MT=/home/hugo/data/ref/NC_027836.1.fa
  curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=NC_027836.1&rettype=fasta&retmode=text" -o "$MT"
fi
echo "MT=$MT  大小=$(stat -c%s "$MT")"
samtools faidx "$MT"

A=/home/hugo/data/03_align/SRR11528381.dedup.bam
B=/home/hugo/data/03_align/SRR12044628.dedup.bam
CHR=$(cut -f1 "${MT}.fai" | head -1)
REG="${CHR}:1-$(cut -f2 "${MT}.fai" | head -1)"
echo "REG=$REG"

samtools mpileup -f "$MT" -r "$REG" -q 20 -Q 20 -d 3000 "$A" "$B" 2>/dev/null \
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
n=0; ane=bne=ab=0; vs=[]; ah=bh=0
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
    print(f"A != 线粒体参考   {ane:>6,}  -> {100*ane/n:.3f}%")
    print(f"B != 线粒体参考   {bne:>6,}  -> {100*bne/n:.3f}%")
    print(f"A != B            {ab:>6,}  -> {100*ab/n:.3f}%")
    print(f"一致度>=0.8: A={100*ah/n:.1f}%  B={100*bh/n:.1f}%")
    ts=sum(1 for p in vs if p in TS); tv=len(vs)-ts
    print(f"Ts={ts}  Tv={tv}  Ts/Tv={ts/tv if tv else 0:.3f}")
'
