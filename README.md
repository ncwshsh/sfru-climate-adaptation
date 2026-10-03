# Climate adaptation genomics of the fall armyworm (*Spodoptera frugiperda*)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23124223.svg)](https://zenodo.org/records/23124223)

Analysis code and derived data for the manuscript *"Polygenic signals of climate adaptation in a globally invasive pest, the fall armyworm (Spodoptera frugiperda)"*.

All primary sequence data are **public** and were obtained from existing archives; no new organisms were collected for this study. This repository contains the **analysis code** and the **derived tables** needed to reproduce every number reported in the manuscript.

---

## What the study found, and where each number lives

| Manuscript result | Value | File |
|---|---|---|
| Analysed cohort | 214 individuals, 12 countries, 6 study accessions (P1–P6) | `data/tables/gea_input.tsv` |
| Per-panel QC (mapping rate, depth, coordinates) | Table 1 | `data/tables/qc_s2_bm2k15_P.tsv` |
| Host-strain counts (C/R/H) | Table 2 | `data/tables/gea_input.tsv` (`strain` column) |
| Variable sites retained | 16,230,602 | script `pipeline/angsd_gl.sh` |
| Sites entering the association test | 16,230,598 (4 monomorphic sites dropped) | `pipeline/gea_rda.py` |
| Partial-RDA variance explained | **R² = 2.30 %**, 999 permutations, *P* = 0.001 | `pipeline/gea_rda.py` |
| Genomic inflation factor | λ = 0.9485 | `pipeline/gea_rda.py` |
| Sites surviving strict BH control | **69** | `data/tables/gea_candidates_full_annotated.tsv` |
| Candidate sites at \|z\| > 4 | 4,421 | `data/tables/gea_candidates_full.tsv` |
| Module enrichment (HSP / oxidative stress / diapause) | 0.0010 / 0.0005 / 1.0000 | `pipeline/module_enrich.py`, Table 3 |
| Independent single-locus method (LFMM-type) | 47 sites at FDR < 0.05; *r* = +0.534 with \|z\| | Release asset `gea_lfmm_p.tsv` |
| Cross-panel shared candidates | 550 genes in ≥3 panels | `data/tables/crossregion_genes.tsv` |
| Gene-length bias in count-based enrichment | candidates 2.42× longer than background, *P* = 4.3 × 10⁻¹⁵⁴ | `pipeline/go_bias_check.py`, `pipeline/module_length_check.py` |
| Confounding diagnostics (mapping rate & depth vs latitude) | Fig. 7 | `pipeline/check_corr_scope.py` |

---

## Repository layout

```
scripts/
  pipeline/       44 scripts that constitute the analysis path, in execution order
  diagnostics/    209 auxiliary, QC, download and one-off diagnostic scripts
data/
  tables/         cohort metadata, candidate-site tables, gene sets, GO results
figures/          publication figures, vector (PDF) and 300-dpi PNG
environment/      software versions and environment specification
```

**Per-locus association statistics are not stored in the git history** (they total
171 MB and would make `git clone` impractical). They are provided as release assets:

```
https://github.com/ncwshsh/sfru-climate-adaptation/releases
```

| Asset | Size | Content |
|---|---|---|
| `gea_lfmm_p.tsv` | 36.9 MB | per-site *p* values of the LFMM-type single-locus test (1.01 M sites) |
| `crossregion_z_P1-C.tsv` … `P5-C.tsv` | 26.7 MB each | per-site RDA1 z-loadings for each corn-strain panel |

### The analysis path

| Step | Script | Produces |
|---|---|---|
| Cohort assembly | `select_cohort.py`, `final_cohort.py`, `cohort_xref.py` | `data/tables/host_sra.tsv` |
| Read mapping | `run_align_s2.sh` (bwa-mem2 2.2.1, `-k 15`) | BAM |
| Genotype likelihoods | `pipeline/angsd_gl.sh` (ANGSD, `-baq 0`, no `-C`) | beagle GL |
| Population structure | `pca_summarize.py` (PCAngsd v1.36.4) | PC1–PC6 |
| Strain assignment | `strain_classify.py` (*Tpi* / *Flightin*) | `strain` column |
| Association I (RDA) | `gea_rda.py`, `gea_rda_full.py`, `gea_fdr.py` | `gea_rda_z*.tsv` |
| Association II (single-locus) | `gea_lfmm.py` | `gea_lfmm_p.tsv` |
| Cross-panel | `gea_crossregion.py`, `crossregion_genes.py` | `crossregion_genes.tsv` |
| Module / GO enrichment | `module_enrich.py`, `go_enrich.py` | Table 3 |
| Bias controls | `go_bias_check.py`, `module_length_check.py` | Fig. S4 |
| Independent verification | `check_corr_scope.py`, `verify_crossregion.py` | reproduction of reported values |
| Sensitivity analysis | `run_sens_excl3.sh` | `*_excl3` tables |
| Figures | `paper_figs_pub_P.py`, `pub_style_p.py` | `figures/` |

---

## Reproducing the results

### Software

```
bwa-mem2   2.2.1 (avx2)
samtools   1.21+
ANGSD      (see environment/)
PCAngsd    1.36.4
Python     3.11 (analysis), plus pandas / numpy / scipy / matplotlib / rasterio
```

Exact environment specifications are in `environment/`.

### ⚠️ Paths in the scripts

The scripts were written for a fixed working layout and contain **absolute paths**
(`/home/hugo/...` inside WSL, `C:\SF_data\...` on the host). To re-run them you will
need to remap these to your own environment. The two conventions used are:

| Prefix | Meaning | Typical remap |
|---|---|---|
| `/mnt/c/SF_data/tools` | host directory holding all scripts and reports | your checkout root |
| `/home/hugo/data/angsd` | input data (genotype likelihoods, PCA scores, climate rasters) | your own data location |
| `C:\SF_data\tools\report` | host-side report directory | your checkout root |

The public accessions needed to rebuild the inputs are listed in
`data/tables/host_sra.tsv`; the PCA scores and the ANGSD genotype likelihoods used
here are the outputs of the scripts above and are not redistributed in this
repository (see *Data not included* below).

---

## Data not included here, and how to obtain it

| File | Size | Where it is / how to rebuild it |
|---|---|---|
| ANGSD genotype likelihoods (beagle) | **8.7 GB** | Regenerate from the public BAMs and the parameters in `pipeline/angsd_gl.sh`; too large for any code-hosting service |
| `gea_rda_z_full.tsv` (per-locus z, 16.2 M sites) | **428 MB** | Exceeds the 100 MB per-file limit of GitHub; regenerate with `pipeline/gea_rda_full.py`, or request a copy by mail |
| `crossregion_z_*_excl3.tsv` (sensitivity analysis) | 5 × 27 MB | Regenerate with `pipeline/run_sens_excl3.sh` |

The underlying primary sequence data remain publicly available from ENA/SRA under
the accessions in `data/tables/host_sra.tsv`.

---

## Data and panel codes

Panels are labelled **P1–P6** in descending order of analysed sample size. The codes
denote **public study accessions (BioProjects)**, not geographic labels; P3 and P4 are
multi-country survey panels (8 and 5 countries respectively, 2–3 individuals per
country). The full mapping, together with coordinate precision and country
composition, is in `data/tables/panel_map.tsv`. In-silico labels (US-C, BR-C, …) that
appear in the *derived* per-locus loading files are the original study codes and map
one-to-one onto P1–P6 as documented in the manuscript.

---

## Citation

If you use these scripts or derived tables, please cite the manuscript above. A
machine-readable citation record is provided in [`CITATION.cff`](CITATION.cff).

## Licence

- **Code** — MIT Licence (see [`LICENSE`](LICENSE))
- **Derived data tables** — CC BY 4.0 (see [`DATA_LICENSE`](DATA_LICENSE))

## Citation of dependencies

See `environment/`. Please cite ANGSD, PCAngsd, bwa-mem2 and the WorldClim and
USGS LANL GMTED datasets where applicable.
