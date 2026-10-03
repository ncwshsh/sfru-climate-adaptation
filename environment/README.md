# Environment

## Verified software versions

| Component | Version | Notes |
|---|---|---|
| bwa-mem2 | 2.2.1 (avx2) | `-k 15` used cohort-wide on purpose (see manuscript §2.2) |
| PCAngsd | 1.36.4 | structure estimation from genotype likelihoods |
| ANGSD | see below | run with `-baq 0` and **no** `-C` (see manuscript §2.3) |
| Python | 3.11 | analysis; requires numpy, pandas, scipy, matplotlib, rasterio |

## Record the exact ANGSD version used

```
angsd -v            # or: angsd 2>&1 | head -2
samtools --version
bwa-mem2 -h | head -1
```

The ANGSD version string is the one item not recoverable from this repository;
append it here when finalising the archive.

## External data sources

- Reference assembly: `GCF_023101765.2` (AGI-APGP_CSIRO_Sfru_2.0), NCBI
- Climate: WorldClim v2.1 at 10 arc-min
- Primary sequence: ENA/SRA, accessions in `../data/tables/host_sra.tsv`
