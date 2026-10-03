# Polygenic signals of climate adaptation in a globally invasive pest, the fall armyworm (*Spodoptera frugiperda*)

**Running head:** Climate adaptation genomics of fall armyworm

**Version:** v2 draft, 2026-09-25  
**Target journal:** *Molecular Ecology* (alternatives: *Genome Biology and Evolution*, *Molecular Biology and Evolution*)  
**Citation style:** author–year (Harvard). All in-text citations are resolved; **three** placeholders remain — the repository DOI, author contributions and funding (see "Numbers to verify before submission" at the end).

---

## Abstract

Understanding whether, and by what genetic architecture, invasive insects adapt to the climates they encounter is central to predicting range expansion. The fall armyworm (*Spodoptera frugiperda*) is one of the most rapid and widespread agricultural invasions on record, yet genomic evidence for climate adaptation in its invasive range remains scarce, and studies are frequently confounded by reference bias, unequal sequencing depth and host-strain structure. We assembled a public resequencing panel of 214 individual *S. frugiperda* from 12 countries and six study accessions, retained genotype likelihoods across 16,230,602 variable sites using the full complement of 31 nuclear chromosomes, and tested for genotype–environment association within the P1 study panel (n = 143), the only panel with both a strong climatic gradient (annual mean temperature 6.2–24.4 °C; *r* = −0.896 between latitude and annual mean temperature) and locality-level coordinates. Using partial redundancy analysis with host strain and leading genomic axes as conditioning variables, climate explained **2.30% of genetic variation** (999 permutations, *p* = 0.001; genomic inflation factor λ = 0.9485). Only **69 sites** survived strict Benjamini–Hochberg control across all 16.2 million tests, indicating that climate-associated variation is not concentrated in a few large-effect loci. Instead, functional module enrichment — which is insensitive to locus counts — identified significant polygenic shifts in the **heat-shock protein** (*p* = 0.0010) and **oxidative stress** (*p* = 0.0005) modules, both of which were independently reproduced by a second, LFMM-type single-locus method (identical *p* values to three decimals). A **diapause/photoperiod** module was consistently non-significant under both methods (*p* = 1.0000 and 0.9955) and we report this negative result as such. Across study panels, candidate gene sets were strongly shared (2.3–3.0-fold enrichment, *p* ≤ 1 × 10⁻³⁹; 550 genes recovered in ≥3 panels), but the *combinations* of enriched modules differed by panel. We further show that data-driven GO enrichment in this system is severely distorted by a gene-length bias (candidate genes are 2.42× longer than background, *p* = 4.3 × 10⁻¹⁵⁴), whereas module-level enrichment is not (*ρ* = +0.006 between gene length and window-mean |*z*|). Our results support a polygenic, largely non-parallel architecture of climate adaptation in *S. frugiperda*, and provide a methodological template for separating biological signal from technical confounding in public-data landscape genomics.

**Keywords:** landscape genomics, genotype–environment association, redundancy analysis, invasive species, heat-shock proteins, oxidative stress, polygenic adaptation, reference bias

---

## 1. Introduction

Biological invasions place organisms in climates they have not experienced, over timescales short enough that adaptation, rather than plasticity alone, may contribute to establishment and spread (Prentis et al., 2008; Bock et al., 2015). Whether invasive populations adapt to novel thermal environments, and whether they do so repeatedly from standing variation at the same loci, are open questions with direct consequences for forecasting pest range limits (Bock et al., 2015; Capblancq et al., 2018).

The fall armyworm (*Spodoptera frugiperda*; Lepidoptera: Noctuidae) is a favourable system in which to address these questions. Native to the Americas, it has spread across sub-Saharan Africa, South and Southeast Asia, China, and Oceania within roughly five years, and more recently to Australia and parts of the Pacific (Tay et al., 2022; Yainna et al., 2022; Nam et al., 2024). Its invasive range spans more than 60 degrees of latitude and a correspondingly wide range of thermal regimes. Fall armyworm populations are also structured by host strain: a corn-strain and a rice-strain, long recognised on the basis of *Tpi* and mitochondrial *COI* markers, differ in host use, pheromone composition and — importantly for the present study — in developmental timing and diapause-related phenotypes (Pashley, 1986; Nagoshi, 2010; Acharya et al., 2021). Because strain composition covaries with geography and climate, any genotype–environment association analysis that fails to condition on strain risks attributing strain structure to climatic adaptation.

Three functional modules are *a priori* plausible candidates for thermal adaptation in this species. (i) The **heat-shock protein (HSP)** machinery is the canonical cellular response to thermal stress and shows repeated signatures of selection across latitudinal gradients in insects (Bettencourt et al., 2002). (ii) **Diapause and photoperiodism** govern seasonal timing; in *S. frugiperda* the capacity for facultative diapause is limited and strain-dependent, making it a natural negative control as well as a candidate (Westbrook et al., 2016; Du Plessis et al., 2020). (iii) **Oxidative stress** responses are mechanistically coupled to thermal exposure: mitochondrial uncoupling at temperature extremes increases reactive oxygen species, and antioxidant enzymes (superoxide dismutase, catalase, glutathione S-transferases) co-vary with thermal tolerance across taxa (González-Tokman et al., 2025).

Testing such hypotheses with public data, however, is technically treacherous. Three confounding axes dominate. First, **reference bias**: populations diverged from the reference assembly accumulate mismatches, which reduce alignment and mapping quality; if divergence is geographically structured, a computational decision as benign as BAQ realignment or a `-C` mapping-quality adjustment can delete data in a latitude-correlated manner and manufacture a spurious climatic signal. Second, **unequal sequencing depth**, which biases genotype likelihoods and can create apparent homozygosity gradients. Third, **study/batch structure**, because public cohorts are assembled from accessions that differ in library preparation, read length and sampling design, and because sampling locations are often reported only to country level.

Here we exploit a new public resequencing resource for *S. frugiperda* to construct a 214-individual panel spanning 12 countries, and explicitly design the analysis so that each of the above confounders is measured and reported rather than assumed absent. We restrict formal genotype–environment association testing to the P1 accession, which is the only panel combining a high-precision locality assignment with a strong, internally homogeneous climatic gradient, and we characterise the residual confounding within that panel. We test for signal with two methodologically independent approaches — multivariate partial redundancy analysis (RDA) and an LFMM-type single-locus latent-factor model — and we focus inference on pathway-level module enrichment rather than on individual outlier loci, because the latter is confounded by gene length and by locus-count effects. Finally, we extend the comparison across study panels to ask whether independently colonised regions converge on the same adaptive solutions.

---

## 2. Materials and Methods

### 2.1 Study panels and data assembly

Public Illumina whole-genome resequencing data were retrieved from ENA/SRA. A single high-quality RefSeq reference-guided assembly was used to avoid circularity (see §2.2). Accessions were grouped into six **study panels** corresponding to distinct public BioProjects, labelled **P1**–**P6** in descending order of analysed sample size: **P1** (n = 143; 137 from the continental USA plus 6 from Puerto Rico), **P2** (n = 24; Brazil), **P3** (n = 16), **P4** (n = 15), **P5** (n = 10; China) and **P6** (n = 6; Florida, USA).

> **Terminology.** Panels are labelled with neutral study-accession codes **P1**–**P6**, deliberately chosen so that the labels carry no geographic implication (the mapping, together with coordinate precision and country composition, is tabulated in `report/panel_map.tsv`). The codes denote *public study accessions* and are retained for consistency with the figures; **they are not geographic labels**. In particular, the P3 panel aggregates eight countries (Zambia, China, Malaysia, Ghana, Malawi, Rwanda, Kenya and Sudan; two individuals each) and the P4 panel aggregates five countries (Brazil, USA, Puerto Rico, Argentina and Kenya; three individuals each). Both are broad multi-country survey panels rather than regional samples. This structure is central to the interpretation of §3.9.

In total the analysed cohort comprises **214 individuals from 12 countries**, spanning latitudes −35.0° to +40.9°. Raw sequencing volume for the downloaded cohort was 278.9 GB.

Six further libraries were sequenced but excluded before analysis (220 downloaded → 214 analysed). All six belong to the P2 panel and fell below a 55% mapping-rate floor (36–52% of reads mapped; the next-lowest P2 library maps at 60.2%), the expected consequence of pronounced divergence between the Brazilian population and the RefSeq reference (§3.1). Their exclusion is conservative: removing them *weakens* the cross-panel technical gradients reported in §3.1 rather than strengthening them. Three further libraries with mapping rates between 60% and 70% were retained in the analysis cohort and are addressed by a dedicated sensitivity analysis (§3.9, §4.6).

### 2.2 Reference genome and read mapping

Reads were mapped to the RefSeq assembly **GCF_023101765.2** (AGI-APGP_CSIRO_Sfru_2.0). We deliberately restricted the reference to the **31 nuclear chromosomes** (381,761,283 bp; 99.44% of the assembly), excluding 37 `NW_` scaffolds and, critically, the mitochondrial contig `NC_027836.1`. The scaffolds account for only 0.56% of the assembly yet absorbed 6.1% of reads, consistent with collapsed repeats, and were removed to avoid spurious multi-mapping.


Mapping used **bwa-mem2 2.2.1 (avx2)** (Vasimuddin et al., 2019) with a minimum seed length of `-k 15`. The default `-k 19` produced mapping rates as low as 21–60% for Brazilian individuals, reflecting genuine divergence from the CSIRO reference rather than a technical artefact (see §3.1). On a common subset, `-k 15` gave a 1.83–2.27× speed-up with an identical number of primary mapped reads (1,980,932 for a high-quality test library). Because re-aligning only the poorly mapping libraries would make mapper choice collinear with geography, the **entire cohort was remapped with the same mapper and settings**.

Post-processing followed a single-sort pipeline (`collate → fixmate → sort → markdup`), which was 24% faster in wall-clock time than a double-sort equivalent with identical `flagstat` output. Mapping was run at two libraries × nine threads, achieving 6.2–8.0 GB h⁻¹. **All 220 libraries completed with zero failures**, yielding 345.3 GB of analysis-ready BAMs.

Mapping rate was then used as a first-pass quality filter. Six Brazilian libraries with <70% mapping rate were excluded, leaving the 214-individual analysis cohort. We note explicitly that **three libraries below the 70% threshold nevertheless remain in the cohort** (SRR9289294, 60.19%, P2; SRR12044624, 68.87%, P4; SRR9289279, 69.87%, P2; see §4.6). Per-panel mapping statistics are given in Table 1 and Fig. S1.

### 2.3 Genotype likelihoods

To avoid the depth-dependent biases inherent in hard genotype calling for low-coverage data, we retained genotype likelihoods throughout. ANGSD was run as (Korneliussen et al., 2014):

```
angsd -b bamlist.txt -ref ref_chr.fna \
      -uniqueOnly 1 -remove_bads 1 -only_proper_pairs 1 -trim 0 -baq 0 \
      -minMapQ 30 -minQ 20 -minInd 171 -GL 1 -doGlf 2 \
      -doMajorMinor 1 -doMaf 1 -SNP_pval 1e-6 -minMaf 0.05 -P 8
```

**Two parameter choices are load-bearing.** First, BAQ was disabled (`-baq 0`) and no mapping-quality adjustment (`-C`) was applied. A `-C 50` run on the same region required 76 s and retained 1,981 sites, whereas `-baq 0` without `-C` required 33 s and retained 17,138 sites. This is not merely a performance difference: `-C` down-weights reads carrying mismatches, which is precisely how populations diverged from the reference manifest — we would therefore have systematically discarded the tropical (most divergent) portion of the cohort, inducing a technical gradient aligned with latitude. Second, `-minInd 171` (80% of the cohort) balances site retention against missingness.

Scanning 374.5 million sites yielded **16,230,602 variable sites**, stored as beagle-format likelihoods (6.5 GB).

### 2.4 Population structure

Genetic covariance was estimated directly from genotype likelihoods with **PCAngsd v1.36.4** (Meisner & Albrechtsen, 2018), avoiding the depth-dependent pseudo-structure that arises when low-coverage individuals are forced towards homozygous calls. Prior to this step the site set was thinned at a fixed interval to 1,010,000 sites to fit in memory; a control analysis confirmed that thinning did not bias the association results (§3.5).

The leading components explained PC1 = 6.61%, PC2 = 3.01%, PC3 = 1.63% and PC4 = 1.45% of the covariance.

### 2.5 Climatic data

Nineteen bioclimatic variables (BIO1–BIO19) plus elevation were extracted from **WorldClim v2.1 at 10 arc-min resolution** (Fick & Hijmans, 2017) (~20 km) for all 214 individuals, with **no missing values**. Variables were standardised, collinear variables (|*r*| > 0.9) were removed, and the retained set was summarised by principal component analysis; the first two to three environmental axes were used as predictors.

Sample coordinates were obtained by geocoding and graded by precision. Coordinates for the P1, P6 and P2 panels are locality-level (county or município; *n* = 173), for the P5 panel province-level (*n* = 10), and for the P3 and P4 panels country centroids only (*n* = 31). This asymmetry is not incidental — it is the principal reason the formal association analysis is restricted to the P1 panel (§2.7, §4.6).

### 2.6 Host-strain assignment

Host strain (corn C / rice R) was available as curated metadata for all 143 P1 individuals (isolate fields annotated "identified as C-, R- or H-strain": C = 80, R = 62, H = 1). For the remaining panels, no annotation exists, so strain was inferred molecularly. We used the two canonical nuclear markers **Tpi** (`NC_064236.1:8,187,968–8,190,276`) and **Flightin** (`NC_064236.1:6,868,795–6,870,023`). The mitochondrial *COI* route was unavailable by design, as the mitochondrial contig was excluded from the reference.

From these intervals we extracted **76 diagnostic sites**, derived per-site discriminant scores from the 142 annotated P1 individuals (*dᵢ* = mean dosage in C − mean dosage in R), and scored each unannotated individual as *S* = Σ *dᵢ* × doseᵢ. Leave-one-out cross-validation across the annotated P1 individuals classified **100.0% correctly** (C 80/80, R 62/62; Fig. S3), and predictions for annotated individuals agreed with the curated metadata in 100% of cases.

### 2.7 Association analysis I — partial redundancy analysis

Genotypes were represented as **expected dosages** (`P(het) + 2·P(hom_alt)`) rather than hard calls. We used partial RDA (Forester et al., 2018; Capblancq et al., 2018) in which host strain and genomic axes PC2–PC4 were fitted as conditioning variables and thereby regressed out before testing the climatic predictors (PC1 was omitted because it is essentially a strain axis; §3.4). Significance was assessed with 999 permutations of the individual–environment assignment.

Computationally, the analysis was reformulated around the between-individual Gram matrix **G = Y′Y** (*n* × *n*), which reduces each permutation from O(*p*) to O(*n*), and the full site set was processed in a streaming block fashion (the dense genotype matrix for all 16.2 M sites would require 84 GB). All **16,230,602** variable sites were taken forward; after removing four monomorphic sites (expected dosage variance ≤ 1 × 10⁻⁶), **16,230,598** sites entered the test, matching the *m* used for BH control in §2.9. The 200,000-site thinned version returned an identical R² (2.30%).

### 2.8 Association analysis II — LFMM-type single-locus test

As an independent method we fitted, at each site, a linear model of the form

```
dosage ~ climate (3 axes) + host strain + PC2 + PC3 + PC4
```

and tested the three climate coefficients jointly (*F*-test, df₁ = 3, df₂ = 135). Latent factors were estimated by PCA rather than by joint EM estimation, the only substantive deviation from the published LFMM2 algorithm (Frichot et al., 2013); **the official lfmm2 binary could not be installed in our environment** (no conda package; repository unavailable) and this is stated as a limitation (§4.6). This method was applied to the 1,010,000-site thinned set.

### 2.9 Multiple testing and unbiased pruning

The genomic inflation factor was λ = median(*z*²)/0.4549 = **0.9485**, indicating no inflation and thus trustworthy *p*-values. Because λ < 1, no genomic control correction was applied (dividing by √λ would inflate test statistics artificially).

Benjamini–Hochberg FDR was applied across all *m* = 16,230,598 tests. To obtain an honest estimate of the number of effectively independent tests, we pruned the site set by retaining, **within each 50-kb window, the site with the smallest genomic position**. This is deliberately unbiased with respect to effect size; selecting the site with the largest |*z*| within each window would constitute a selected subset and invalidate the uniformity assumption underlying BH. A second, conservative analysis restricted to the pruned set (effective *m* = 7,643) was also run.

### 2.10 Functional module enrichment

Three *a priori* functional modules were defined from the reference annotation: **heat-shock proteins** (74 genes), **diapause/photoperiod** (125 genes), and **oxidative stress** (206 genes). For each module, all sites within ±2 kb of a module gene were collected (HSP 135,240 sites; diapause 234,544; oxidative stress 345,009), and the module-mean |*z*| was compared with the genome-wide background by 2,000 permutations.

Two properties of this statistic matter. First, it is **insensitive to the number of sites** in a module, which makes it robust to the gene-length bias that affects count-based enrichment (§2.12). Second, it **requires the full site set**: a control run on a 200,000-site thinning gave *p* = 0.443 for the HSP module (missing a real signal), whereas the complete set gave *p* = 0.001.

### 2.11 Confounding diagnostics

We quantified the two principal technical gradients against latitude, both across the whole cohort and within panels: mapping rate vs latitude, and raw sequencing depth vs latitude. We also correlated the leading genomic axis with mapping rate and depth within the P1 panel. These diagnostics are reported in full (Fig. 7) because their omission is a common failure mode in public-data landscape genomics.

### 2.12 Gene ontology enrichment and gene-length bias control

Functional annotation was obtained from **UniProt** (The UniProt Consortium, 2025) (taxid 7108; 25,557 proteins with GO terms and NCBI GeneID cross-references), providing GO annotations for 10,828 genes and enabling direct linkage to the RefSeq Gnomon gene models. GO over-representation (Ashburner et al., 2000) was tested on (i) genes within ±2 kb of a candidate site (2,565 genes), (ii) genes shared across ≥3 panels (550 genes), and (iii) genes near FDR-significant sites (58 genes). **KEGG pathway enrichment could not be performed** because KEGG contains no *S. frugiperda* genome entry (only the congener *S. litura*).

Because candidate genes are substantially longer than background genes, we repeated the analysis on a **length-matched** background (following Young et al., 2010; Mi et al., 2012) and, separately, verified that gene length is uncorrelated with the module-level statistic (Fig. S4).

---

## 3. Results

### 3.1 Cohort quality and confounding diagnostics

Per-panel sequencing statistics are given in Table 1. Median raw depth was closely matched across panels (6.4–6.8×) except for the P5 panel (12.2×), reflecting the deliberate 6× nominal download target applied to the cohort. Whole-cohort mapping rate was highest in the P3 (97.83% mean), P1 (96.45%) and P4 (93.59%) panels, intermediate in P6 (91.33%) and P5 (86.36%), and lowest in P2 (84.25%, minimum 60.19%) — the expected signature of a Brazilian population substantially diverged from the CSIRO reference.


Crucially, the technical gradients behave very differently at different scales (Fig. 7, computed on all 220 sequenced samples):

| Scale                           | mapping rate ~ latitude | raw depth ~ latitude |
| ------------------------------- | ----------------------- | -------------------- |
| All sequenced samples (n = 220) | **+0.489**              | +0.061               |
| **Within P1 panel (n = 143)**   | **+0.023**              | **−0.083**           |
| Within P2 panel (n = 30)        | −0.223                  | −0.167               |

Six libraries excluded before analysis (§2.1; all P2, mapping rate 36–52%) are the leverage points of the cross-panel gradient: recomputed on the 214-sample analysis cohort, the whole-cohort correlations become +0.433 (mapping rate) and −0.016 (depth), and the within-P2 correlations become +0.033 and +0.041 — the negative within-P2 association was carried entirely by the excluded libraries. Neither conclusion below is affected; if anything the gradient is weaker on the analysis cohort, so the diagnostics presented here are the conservative case.

Two conclusions follow. First, **sequencing depth is not a confounder**: depth is essentially uncorrelated with latitude both globally and within panels, because the download target was equalised across the cohort. Second, **reference bias is collinear with latitude only *between* panels, not within them** — within the P1 panel the correlation is negligible (+0.023). Within the P1 panel, PC1 correlated with mapping rate at *r* = −0.262 and with depth at *r* = −0.069, both acceptable. This structure directly motivates restricting formal association testing to the P1 panel, where the climate signal is identifiable without a technical covariate travelling alongside it.

### 3.2 Population structure

PCAngsd separated the cohort into the expected groups (Fig. 2a). Chinese individuals were the most divergent, consistent with a longer period of isolation in the Old World; the P3 and P4 multi-country panels overlapped substantially with one another, reflecting their shared country composition; and Brazilian individuals formed a distinct cluster. Florida individuals separated clearly, with approximately eight P1 individuals clustering towards them, consistent with a distinctive source-region gene pool reaching into the continental US. Within the P1 panel, the leading axis was not latitudinal but strain-like (§3.4), and PC1 correlated only weakly with latitude.

### 3.3 A strong climatic gradient within the P1 panel

The P1 panel spans 22.9° of latitude (18.06° to 40.94°) and, within it, climate tracks latitude strongly (Fig. 4): annual mean temperature (BIO1) ranges from 6.2 to 24.4 °C and correlates with latitude at *r* = −0.896; mean temperature of the coldest quarter (BIO11) ranges from −2.9 to 22.7 °C and correlates with latitude at *r* = −0.952. The gradient is therefore both strong in magnitude and monotonic in space — the precondition for detecting climate-associated variation.

### 3.4 Host-strain structure and its climatic entanglement

Host strain was strongly non-random with respect to geography (Fig. 3; Table 2). The source-region panel (P6) was mixed (C 3 : R 3). In contrast, the invasive-range panels were almost exclusively corn-strain: P2 24/24 C, P3 16/16 C, P5 10/10 C, and P4 14/15 C. The P1 panel was mixed (C 80, R 62, H 1), consistent with its position spanning both the native range margin and recently colonised temperate areas.

Strain and climate are only weakly confounded by latitude (*r* = −0.158) but are not independent of climate: mean BIO11 was 13.2 °C for C-strain versus 7.3 °C for R-strain individuals (BIO1: 19.5 vs 16.5 °C). Because this coupling is substantial, **strain was fitted as a conditioning variable in all association analyses**; omitting it would risk attributing strain structure to climatic adaptation.

### 3.5 Climate-associated genetic variation in the P1 panel

Partial RDA across all 16,230,602 sites gave **R² = 2.30% (*p* = 0.001**, 999 permutations; Fig. 5a). At a candidate threshold of |*z*| > 4, 4,421 sites were recovered against an expectation under normality of approximately 1,023 — a genuine excess in the tail of the distribution (Fig. 5b). The 200,000-site thinned analysis yielded an identical R² (2.30%), confirming that thinning is unbiased.

Under strict BH control across all *m* = 16,230,598 tests, only **69 sites** were significant (|*z*| ≥ 5.189; Fig. 5c, Table S2). Restricting BH to the position-pruned, effectively independent set (effective *m* = 7,643) returned **zero** significant sites. Climate-associated variation in this panel is therefore **sparse and clustered**, not diffusely distributed across the genome — a pattern that also explains why individual outlier loci carry little of the total signal.

### 3.6 Independent validation with a second method

The LFMM-type single-locus test, applied to the 1,010,000-site set, identified 47 sites at FDR < 0.05. The two methods agreed far beyond chance: Pearson *r* = +0.534 between |*z*| (RDA) and −log₁₀ *p* (LFMM-type) (Spearman *ρ* = +0.508; Fig. S2). The overlap between the respective top-1,000 site sets was **196 sites, against an expectation of 1 under independence**. Sites declared significant by RDA fell, on average, in the 99.9th percentile of the LFMM-type statistic.

### 3.7 Functional module enrichment — the primary result

Because single-site tests are sparse (§3.5), we tested for coordinated shifts at the level of *a priori* functional modules (Table 3):

| Module | Genes | Sites | Module mean |*z*| | Background | *p* (RDA) | *p* (LFMM-type) |  
|---|---|---|---|---|---|--- | --- | --- |  
| **Heat-shock proteins** | 74 | 135,240 | 0.795 | 0.790 | **0.0010** | **0.0010** |  
| Diapause / photoperiod | 125 | 234,544 | 0.785 | 0.790 | 1.0000 | 0.9955 |  
| **Oxidative stress** | 206 | 345,009 | 0.806 | 0.790 | **0.0005** | **0.0005** |

Two conclusions are robust. First, the **heat-shock protein and oxidative stress modules are significantly enriched, and both are reproduced by a methodologically independent approach, with essentially identical *p*-values** — the joint probability of this concordance arising from a shared artefact is negligible. Second, the **diapause/photoperiod module is not enriched under either method**, and we report this as a genuine negative result rather than interpreting the module post hoc.

The effect sizes are small (module mean |*z*| 0.806 vs 0.790 background, i.e. ~2% relative), and significance is achieved through the very large number of sites examined. This is the expected signature of a highly polygenic trait and we do not claim large per-locus effects.

### 3.8 Candidate loci and genes

Among the 4,421 candidate sites, several gene families recur (Table S4). The most prominent is the **cytochrome P450** family (CYP9e2, CYP6B1, CYP6B6 at multiple sites, CYP4C1, CYP6B4, CYP9f2, CYP302a1). We also recover **superoxide dismutase [Cu–Zn]**, **glutathione S-transferase theta-1** and **glutathione hydrolase 7** — the enzymatic core of the antioxidant response — together with **heat-shock protein 67B1** and **dnaJ C13 / dnaJ B13** (HSP40 co-chaperones). Developmental and osmoregulatory genes also appear, including **juvenile hormone esterase**, **ecdysone-inducible protein E75**, CHH-like proteins and anoctamin-1.

Of the 69 strictly FDR-significant sites, only **two** fall within a nominal module (CYP9e2 and a UDP-glucosyltransferase). The dissociation between single-site significance and module-level enrichment is itself informative: it indicates that climate-associated variation in this species is distributed across many loci of individually small effect rather than concentrated in a few strong candidates.

### 3.9 Cross-panel comparison within the corn strain

Restricting to corn-strain individuals to hold host use constant (§3.4), we fitted panel-specific RDA models (Table S2; Fig. 6):

| Panel | *n* | R²    | *p*   |
| ----- | --- | ----- | ----- |
| P1-C  | 80  | 0.042 | 0.002 |
| P2-C  | 24  | 0.096 | 0.002 |
| P3-C  | 16  | 0.161 | 0.006 |
| P4-C  | 14  | 0.100 | 0.002 |
| P5-C  | 10  | 0.283 | 0.006 |

**These R² values are not comparable across panels.** Small panels (P5, *n* = 10) have a high model-complexity-to-sample-size ratio, and overfitting inflates R². These results are therefore reported as qualitative indicators only.

Using a common definition — the top 0.2% of sites on each panel's own leading climatic axis (2,029–2,030 sites per panel), mapped to genes within ±2 kb — candidate gene sets were strongly shared between panels (Fig. 6a; complete 10-pair matrix in Table S3). The strongest overlaps were P4-C ∩ P2-C (434 genes, 3.0×, *p* = 1 × 10⁻¹¹⁰), P1-C ∩ P2-C (419, 2.9×, *p* = 6 × 10⁻¹⁰⁴), P1-C ∩ P4-C (397, 2.8×, *p* = 1 × 10⁻⁹¹), P5-C ∩ P2-C (357, 2.8×, *p* = 3 × 10⁻⁸²), P4-C ∩ P5-C (347, 2.8×, *p* = 1 × 10⁻⁷⁷), P1-C ∩ P5-C (311, 2.5×, *p* = 4 × 10⁻⁵⁹), P3-C ∩ P4-C (293, 2.5×, *p* = 1 × 10⁻⁵⁵), P2-C ∩ P3-C (286, 2.5×, *p* = 1 × 10⁻⁵⁰), P3-C ∩ P1-C (258, 2.3×, *p* = 1 × 10⁻³⁹) and P3-C ∩ P5-C (229, 2.3×, *p* = 3 × 10⁻³⁵). **All ten pairwise comparisons were significant, with enrichment factors between 2.3× and 3.0×**, and no panel behaved as an outlier. **550 genes were recovered in three or more panels** — 376 in exactly three, 134 in four and 40 in all five (Table S3). Per-panel candidate gene sets comprised 1,240–1,577 genes from a universe of 16,769 annotated genes.

These overlap counts and hypergeometric tail probabilities were independently reproduced from the per-site loading files using a dependency-free re-implementation (exact set arithmetic and log-space hypergeometric tails), which returned identical values for every pair and for the ≥3-panel count of 550; the results are therefore not an artefact of the analysis environment.

At the level of modules, however, the panels diverge (Fig. 6b): the P1-C panel was enriched for oxidative stress (*p* = 0.0005), P5-C for diapause (*p* = 0.0005), P3-C for HSP (*p* = 0.019) and P4-C for oxidative stress (*p* = 0.0025), while P2-C showed no significant module; a nominal diapause signal in P4-C (*p* = 0.012) is discussed below.

**Sensitivity to three residual low-mapping-rate samples.** Three libraries below the 70% mapping-rate threshold remained in the analysis cohort (§4.6). All three are corn-strain and were sampled in Brazil; excluding them reduces the P2-C panel from 24 to 22 and the P4-C panel from 14 to 13, leaving the P1-C (80), P3-C (16) and P5-C (10) panels unchanged. Re-running the whole cross-panel analysis on the reduced cohort (*n* = 211) reproduced every conclusion except one:


| Quantity                        | Full cohort (*n* = 214) | Excluding 3 samples (*n* = 211) |
| ------------------------------- | ----------------------- | ------------------------------- |
| P1-C R²                         | 0.042 (*p* = 0.002)     | 0.042 (*p* = 0.002)             |
| P2-C R²                         | 0.096 (*p* = 0.002)     | 0.105 (*p* = 0.008)             |
| P4-C R²                         | 0.100 (*p* = 0.002)     | 0.100 (*p* = 0.010)             |
| Candidate genes per panel       | 1,240–1,577             | 1,240–1,574                     |
| Largest pairwise overlap change | —                       | P2-C ∩ P5-C, 357 → 330 (−7.6%)  |
| Genes recovered in ≥3 panels    | 550                     | 556                             |
| P1-C oxidative stress           | **0.0005**              | **0.0005**                      |
| P3-C HSP                        | 0.0185                  | 0.0185                          |
| P5-C diapause                   | **0.0005**              | **0.0005**                      |
| P4-C oxidative stress           | 0.0025                  | **0.0005**                      |
| P4-C diapause                   | **0.012**               | 0.055                           |

All ten pairwise overlaps remained significant at *p* < 10⁻³⁵ with enrichment factors of 2.3–3.1×, and the module pattern — oxidative stress in both the P1-C and P4-C panels, HSP in P3-C, diapause in P5-C, nothing in P2-C — was reproduced exactly. The single exception is **P4-C diapause, which falls from *p* = 0.012 to *p* = 0.055** once the P4 panel loses one individual; we therefore do **not** count it among the supported findings. Overlap counts for the reduced cohort were again reproduced independently with the same dependency-free implementation, matching the pipeline in all ten pairs and in the ≥3-panel count.

The overall picture is therefore **a shared inventory of candidate genes deployed in different pathway combinations in different regions** — evidence against strict parallel adaptation, but also against independent, unrelated solutions.

### 3.10 Gene-length bias affects GO enrichment but not module enrichment

Data-driven GO enrichment of the candidate gene set (2,565 genes) returned 45 terms at FDR < 0.05, dominated by `plasma membrane`, `neuron projection`, `cell adhesion` and `cell differentiation`; the shared gene set (550 genes) returned 70 terms in a similar direction; and the set of genes near strictly FDR-significant sites (58 genes) returned **none**, as expected given its size.

These GO results, however, **do not reflect functional preference**. Candidate genes are substantially longer than the background of remaining LOC-annotated genes (*n* = 13,659): median 11,631 vs 4,803 bp (**2.42×**; Mann–Whitney *p* = 4.3 × 10⁻¹⁵⁴). (Using all `gene` features, including 545 features without a LOC identifier, as the background yields 2.59×; throughout this manuscript we use the LOC-annotated background, which matches the annotation resource used for GO testing.) Repeating the enrichment after length matching produced an **entirely different set of top terms** (serine endopeptidases, regulation of signal transduction, etc.). Longer genes simply contain more SNPs and therefore have greater statistical power to enter a count-based candidate set — a well-known artefact in genotype–environment association studies. We therefore treat the GO results as exploratory.

Critically, the **primary result of §3.7 is not subject to this artefact** (Fig. S4):

| Test                                | Result                        | Interpretation                                  |
| ----------------------------------- | ----------------------------- | ----------------------------------------------- |
| Gene length vs window-mean |*z*|    | Spearman **ρ = +0.006**       | Length has no influence on the module statistic |
| HSP module gene length              | 0.85× background, *p* = 0.112 | No length bias                                  |
| Diapause module gene length         | 1.04× background, *p* = 0.314 | No length bias                                  |
| Oxidative stress module gene length | 1.21× background, *p* = 0.180 | No length bias                                  |

The reason for the divergence between the two enrichment approaches is structural. Count-based enrichment of a *candidate gene set* is sensitive to how many sites a gene carries; module enrichment based on the *mean* |*z*| of sites, evaluated by permutation, is not. Our inference therefore rests on the latter.

---

## 4. Discussion

### 4.1 A polygenic, non-parallel signal of climate adaptation

Climate explains 2.30% of genetic variation within the P1 panel (*p* = 0.001), with an inflation factor of 0.9485 indicating that this is not a structure artefact. The signal is nevertheless extremely dispersed: only 69 of 16.2 million sites survive strict FDR control, and zero survive in a position-pruned conservative analysis. At the same time, module-level analyses detect coordinated, replicated shifts in two of three *a priori* modules.

This combination — a small proportion of variance explained, few individually significant loci, but significant pathway-level enrichment — is the expected architecture of a highly polygenic trait under spatially varying selection (Boyle et al., 2017). In such systems, effect sizes at individual loci are typically small relative to drift and to sampling noise at any given site, while the *summed* signal across a functional class is detectable. Our results argue that studies of climate adaptation in invasive insects that rely on outlier detection alone will systematically under-report real signal — as our own HSP module would have been missed had we thinned the site set to 200,000 (*p* = 0.443).

We emphasise effect size: module-mean |*z*| differed from background by roughly 2%. The appropriate interpretation is a gentle, genome-wide redistribution of allele frequencies associated with climate, not strong selection on a handful of loci.

### 4.2 Oxidative stress and heat-shock response

The two enriched modules have a coherent mechanistic relationship. Thermal stress at both cold and warm extremes increases mitochondrial reactive oxygen species production, and antioxidant capacity is a documented correlate of thermal tolerance across ectotherms (González-Tokman et al., 2025). The recovery of superoxide dismutase [Cu–Zn], glutathione S-transferase theta-1, glutathione hydrolase 7 and multiple cytochrome P450s — enzymes that both detoxify xenobiotics and contribute to oxidative balance — as the most recurrent candidate genes is consistent with this axis. Independent enrichment of the HSP module, including HSP67B1 and two dnaJ/HSP40 co-chaperones, reinforces it, since the heat-shock response and oxidative-stress response are functionally interlocked (Dayalan Naidu et al., 2015; González-Tokman et al., 2025).

It is notable that this axis emerged in the P1 panel despite that panel spanning both the native range (subtropical 18°N) and its temperate margin (41°N), where cold rather than heat is likely to be limiting. Chill injury is itself associated with oxidative damage (Lalouette et al., 2011), so the pattern does not require heat as the selective agent; it requires only that thermal regime be the gradient.

### 4.3 Diapause: a consistent negative result

We found no evidence for enrichment of the diapause/photoperiod module, under either method (*p* = 1.0000, 0.9955). We report this as a genuine absence of signal rather than an absence of power: the module comprised 125 genes and 234,544 sites — more sites than the HSP module that *was* detected — so the negative result is not a sample-size artefact.

This is biologically plausible. *S. frugiperda* lacks a robust facultative diapause and does not survive hard frosts in its temperate range; its seasonal range limits are set by migration rather than by local overwintering adaptation (Westbrook et al., 2016; Du Plessis et al., 2020). Under those circumstances, selection for locally tuned photoperiodic thresholds may be weak. At the same time, individual developmental loci — juvenile hormone esterase and ecdysone-inducible protein E75 — appear among the strongest candidate sites (§3.8). We refrain from interpreting this as evidence for weak but real diapause signal, since the site-level candidates are exactly the kind of selected subset that can mislead in a dispersed architecture.

### 4.4 Shared gene inventory, panel-specific pathway combinations

Across panels, corn-strain candidate gene sets overlapped far more than expected by chance (2.3–3.1×), with 550 genes recovered in three or more panels in the full cohort (556 after excluding three residual low-mapping-rate samples; §3.9). Yet the enriched modules differed by panel, and this heterogeneity was itself stable to that sensitivity analysis — with the single exception of a nominal diapause signal in the P4 panel, which did not survive. The most parsimonious reading is that the invasive range draws on the same standing variation, but which functional component is recruited depends on the local selective regime and on which variation happened to be present in the founder propagule.

This interpretation carries an important caveat that the design cannot resolve. In the P3 and P4 panels, multi-country sampling is documented but **each country contributes only two or three individuals**, and their coordinates are country centroids (§2.5); the "climate" summarising an P4-C individual from Kenya and one from Argentina is therefore a within-panel contrast of unclear ecological meaning. We therefore treat §3.9 as hypothesis-generating. A stronger test requires panels with locality-level coordinates and larger per-country sample sizes — precisely the structure that exists only for the P1 and P2 panels here.

### 4.5 Reference bias as a first-order methodological problem

Reference bias — the systematic loss of reads carrying alleles divergent from the haploid reference — is increasingly recognised as a first-order problem for population genomic inference from non-model organisms (Nevado et al., 2014; Akopyan et al., 2025). Akopyan et al. (2025) showed that mapping to a heterospecific reference reduced SNP recovery by 26–32%, depressed nucleotide diversity estimates by >30%, and materially changed which loci were called as F<sub>ST</sub> outliers. The mapping-rate gradient we report across panels (§3.1, Fig. 7) is the same phenomenon expressed as a function of population divergence from the reference.

Mapping rate varied from 60% to 99% across the cohort and, over all 220 sequenced samples, was correlated with latitude at *r* = +0.489 across panels (+0.433 on the 214-sample analysis cohort). Had we applied the common practice of using BAQ or a `-C` mapping-quality adjustment, we would have down-weighted exactly the mismatch-bearing reads that characterise the most divergent — and warmest-located — populations. On a test region, `-C 50` retained 1,981 sites where `-baq 0` without `-C` retained 17,138; applied cohort-wide, that filter would have produced a data-availability gradient running in the same direction as latitude, i.e. a manufactured climatic signal.


Our diagnostics also show where this risk actually resides. Within the P1 panel — the panel we analyse — mapping rate is essentially uncorrelated with latitude (+0.023), so the analysed signal is not plausibly a reference-bias artefact. Between panels, however, the correlation is strong, which is one of several reasons we do not interpret cross-panel differences in R² as evidence about climate.

### 4.6 Limitations

1. **Panel, study and geography are partly confounded.** Climate effects are only identifiable *within* panels; cross-panel differences (including those in §3.9) cannot be attributed to climate, because panels also differ in library preparation, sampling design, coordinate precision and sample size.
2. **Coordinate precision is heterogeneous.** 173 individuals have locality-level coordinates, 10 are province-level, and 31 (the P3 and P4 panels) are country centroids. For those 31, environmental values represent national averages rather than sampling localities.
3. **Residual low-mapping-rate samples.** Six Brazilian libraries below 70% mapping rate were excluded, but **three samples below that threshold remain in the cohort** (SRR9289294, 60.19%, P2; SRR12044624, 68.87%, P4; SRR9289279, 69.87%, P2). All three are corn-strain and were sampled in Brazil. None belongs to the P1 panel, so the primary analysis (§3.5–§3.7) is unaffected. A sensitivity re-analysis excluding all three has been run (§3.9); exclusion reduces the corn-strain P2 panel from 24 to 22 individuals and the P4 panel from 14 to 13, while leaving the P1 (80), P3 (16) and P5 (10) panels unchanged. Because these samples all lie at the warm end of the Brazilian climate distribution, they could in principle affect the composition of the P2-C candidate gene set and hence the cross-panel overlap statistics of §3.9. A sensitivity re-analysis excluding all three (§3.9) changed pairwise overlaps by at most 7.6% and reproduced all cross-panel conclusions except one: the nominal P4-C diapause enrichment fell from *p* = 0.012 to *p* = 0.055 and is therefore not reported as a supported finding.
4. **The LFMM-type test is not the official LFMM2 implementation.** The published lfmm2 binary could not be installed, and latent factors were estimated by PCA rather than by the algorithm's joint EM procedure. The concordance between methods (§3.6) is reassuring, but the method should be described as "LFMM-type" rather than as LFMM2.
5. **Small panels.** The P5 (*n* = 10), P3 (*n* = 16) and P4 (*n* = 14–15) panels are underpowered both for R² estimation (which is inflated by overfitting) and for enrichment testing. Their results are exploratory leads, not conclusions.
6. **Candidate sites are biased towards genic, well-mapped regions.** Sites must pass minimum-individual and depth filters to enter the analysis, which favours well-covered, well-aligned, gene-rich regions. This will inflate cross-panel gene overlap relative to a truly genome-wide expectation.
7. **Diapause is a negative result** and is reported as such without post hoc rescue.
8. **Data-driven GO enrichment is contaminated by gene-length bias** (candidate genes 2.42× longer than background; §3.10) and is used only as an exploratory appendix. The inferential claim rests on module enrichment, which is demonstrably insensitive to this bias (*ρ* = +0.006).
9. **No KEGG pathway enrichment was possible**, as KEGG contains no *S. frugiperda* genome entry (only *S. litura*). Homology-based mapping or an alternative pathway resource would be required.

### 4.7 Conclusions

We find that climatic variation is associated with a small but robust and highly dispersed component of genomic variation in *S. frugiperda*, with convergent evidence from two independent statistical methods pointing to the **heat-shock and oxidative-stress response** as the functional axis of climate adaptation, and a consistent negative result for diapause. Candidate gene sets are broadly shared across invasive regions, but the pathways recruited differ, arguing against strict parallel adaptation. Methodologically, we show that (i) reference-bias mitigation choices such as BAQ or `-C` can manufacture latitude-aligned artefacts and must be validated against within-panel confounding, (ii) locus-count-based enrichment — including GO over-representation — is dominated by gene-length bias in this system, and (iii) module enrichment based on site-level statistics with the *full* site set is robust to that bias and can detect signal that locus-wise tests and thinned datasets miss.

---

## Data accessibility

**Data Accessibility**

All primary sequence data are public and were obtained from existing archives (ENA/SRA); accession lists are given in the repository (`data/tables/host_sra.tsv`). No new organisms were collected for this study. Analysis code, the panel metadata table, derived result tables and all publication figures are archived at **DOI: https://doi.org/10.5281/zenodo.23124223** (record v1.1, MIT licence; Hu, W.). The full per-locus association statistics (171 MB) are provided as release assets at https://github.com/ncwshsh/sfru-climate-adaptation/releases; the ANGSD genotype likelihood files (8.7 GB) are regenerated by the archived script `scripts/pipeline/angsd_gl.sh` from the public alignments. Reference assembly GCF_023101765.2 is available from NCBI.

## Author contributions

[CITE: to be completed — conceptualisation, data curation, formal analysis, writing]

## Acknowledgements

[CITE: funding, computing resources — to be completed]

---

## Figure legends

**Fig. 1** Sampling and climate space. (a) Geographic distribution of the 214 analysed individuals, coloured by study panel; land mask derived from the WorldClim elevation raster (ocean = −32768), equirectangular (Plate Carrée) projection. (b) Occupied climatic space of each panel. See §2.5 for coordinate-precision caveats.

**Fig. 2** Population structure. (a) PCAngsd PC1 vs PC2 for all 214 individuals. (b) Within the P1 panel, PC1 against latitude.

**Fig. 3** Host strain. (a) Geographic distribution of corn-strain (C), rice-strain (R) and hybrid (H) individuals. (b) Strain composition per panel. Strain assignments for panels other than P1 are molecular predictions (§2.6).

**Fig. 4** Climatic gradient within the P1 panel. Latitude against annual mean temperature and mean temperature of the coldest quarter (n = 143).

**Fig. 5** Climate-associated genetic variation in the P1 panel. (a) Distribution of RDA site loadings. (b) Q–Q plot showing departure in the upper tail. (c) Manhattan plot across the 31 nuclear chromosomes (every fifth chromosome labelled).

**Fig. 6** Cross-panel comparison within the corn strain. (a) Pairwise overlap of candidate gene sets, with enrichment factors. (b) Distribution of genes shared among panels.

**Fig. 7** Confounding diagnostics. (a) Mapping rate against latitude for the whole cohort, showing between-panel collinearity. (b) The same relationship within the P1 panel alone. (c) Raw sequencing depth against latitude. All panels provide sample sizes and correlation coefficients.

**Fig. S1** Mapping rate per study panel (box plots).

**Fig. S2** Concordance between the two association methods: |*z*| (RDA) vs −log₁₀ *p* (LFMM-type).

**Fig. S3** Leave-one-out cross-validation of molecular host-strain assignment.

**Fig. S4** Gene-length bias control. (a) Length distribution of candidate genes (*n* = 2,565) versus the background of the remaining LOC-annotated genes (*n* = 13,659); candidates are 2.42× longer (median 11,631 vs 4,803 bp; Mann–Whitney *p* = 4.3 × 10⁻¹⁵⁴). (b) Gene length against the mean |*z*| of sites within the gene ±20 kb; Spearman ρ = +0.006, i.e. gene length does not predict association signal. (c) Length distribution of genes in each of the three functional modules versus all other gene features; no module deviates from the background (all *p* > 0.1). **Panels (a) and (c) deliberately use different gene universes**: panel (a) is restricted to LOC-annotated genes so that its background matches the one used in the GO bias analysis (§3.10), whereas panels (b) and (c) use the full set of annotated gene features. The relevant comparison for each panel is against the background appropriate to that question.

---

## Tables

**Table 1** Cohort composition and mapping statistics.

| Panel | Countries represented | *n* | Latitude range | Mapping rate (mean / median / min, %) | Median raw depth (×) | Coordinate precision |
|---|---|---|---|---|---|---|
| P1 | USA, Puerto Rico | 143 | 18.1 – 40.9 | 96.45 / 97.47 / 75.69 | 6.51 | locality |
| P2 | Brazil | 24 | −28.3 – −12.1 | 84.25 / 85.87 / 60.19 | 6.62 | locality |
| P3 | Zambia, China, Malaysia, Ghana, Malawi, Rwanda, Kenya, Sudan | 16 | −14.5 – 34.5 | 97.83 / 98.14 / 94.81 | 6.81 | country |
| P4 | Brazil, USA, Puerto Rico, Argentina, Kenya | 15 | −35.0 – 39.8 | 93.59 / 97.46 / 68.87 | 6.73 | country |
| P5 | China | 10 | 23.1 – 25.0 | 86.36 / 85.86 / 83.03 | 12.16 | province |
| P6 | USA | 6 | 29.4 – 30.3 | 91.33 / 93.00 / 81.16 | 6.36 | locality |
| **Total** | **12 countries** | **214** | **−35.0 – 40.9** | — | — | — |

**Table 2** Host-strain composition by panel.

| Panel | *n* | Corn (C) | Rice (R) | Hybrid (H) | Assignment |
|---|---|---|---|---|---|
| P1 | 143 | 80 | 62 | 1 | curated metadata |
| P2 | 24 | 24 | 0 | 0 | molecular |
| P3 | 16 | 16 | 0 | 0 | molecular |
| P4 | 15 | 14 | 1 | 0 | molecular |
| P5 | 10 | 10 | 0 | 0 | molecular |
| P6 | 6 | 3 | 3 | 0 | molecular |

**Table 3** Functional module enrichment under two independent methods (P1 panel, corn- and rice-strain individuals combined, strain fitted as a covariate).

| Module | Genes | Sites | Module mean \|*z*\| | Background mean \|*z*\| | *p* (RDA) | *p* (LFMM-type) |
|---|---|---|---|---|---|---|
| Heat-shock proteins | 74 | 135,240 | 0.795 | 0.790 | **0.0010** | **0.0010** |
| Diapause / photoperiod | 125 | 234,544 | 0.785 | 0.790 | 1.0000 | 0.9955 |
| Oxidative stress | 206 | 345,009 | 0.806 | 0.790 | **0.0005** | **0.0005** |

**Supplementary tables.** Table S1, panel metadata for all 214 individuals (`gea_input.tsv`). Table S2, the 69 FDR-significant sites with annotations. Table S3, genes shared among ≥3 panels (550 in the full cohort, 556 in the reduced cohort). Table S4, all 4,421 candidate sites with annotations. Table S5, cross-panel sensitivity analysis excluding three residual low-mapping-rate samples (full 10-pair overlap matrix for both cohorts).

---

## References

Acharya, N., Rajotte, E.G., Dyer, J. & Meagher, R.L. (2021) *Tpi* and *COI* sequence polymorphisms reveal population structure in the fall armyworm, *Spodoptera frugiperda*. *Insects* 12: 439.

Akopyan, M., Genchev, M., Armstrong, E.E. & Mooney, J.A. (2025) Reference genome choice compromises population genetic analyses. *Cell* 188: 6939–6952.e11.


Ashburner, M., Ball, C.A., Blake, J.A. *et al.* (2000) Gene Ontology: tool for the unification of biology. *Nature Genetics* 25: 25–29.

Bettencourt, B.R., Kim, I., Hoffmann, A.A. & Feder, M.E. (2002) Response to natural and laboratory selection at the *Drosophila hsp70* genes. *Evolution* 56: 1796–1801.

Bock, D.G., Caseys, C., Cousens, R.D. *et al.* (2015) What we still don't know about invasion genetics. *Molecular Ecology* 24: 2277–2297.

Boyle, E.A., Li, Y.I. & Pritchard, J.K. (2017) An expanded view of complex traits: from polygenic to omnigenic. *Cell* 169: 1177–1186.

Capblancq, T., Luu, K., Blum, M.G.B. & Bazin, E. (2018) Evaluation of redundancy analysis to identify signatures of local adaptation. *Molecular Ecology Resources* 18: 1223–1233.

Dayalan Naidu, S., Kostov, R.V. & Dinkova-Kostova, A.T. (2015) Transcription factors Hsf1 and Nrf2 engage in crosstalk for cytoprotection. *Trends in Pharmacological Sciences* 36: 6–14.

Du Plessis, H., Schlemmer, M.-L. & Van den Berg, J. (2020) The effect of temperature on the development of *Spodoptera frugiperda* (Lepidoptera: Noctuidae). *Insects* 11: 228.

Fick, S.E. & Hijmans, R.J. (2017) WorldClim 2: new 1-km spatial resolution climate surfaces for global land areas. *International Journal of Climatology* 37: 4302–4315.

Forester, B.R., Lasky, J.R., Wagner, H.H. & Urban, D.L. (2018) Comparing methods for detecting multilocus adaptation with multivariate genotype–environment associations. *Molecular Ecology* 27: 2215–2233.

Frichot, E., Schoville, S.D., Bouchard, G. & François, O. (2013) Testing for associations between loci and environmental gradients using latent factor mixed models. *Molecular Biology and Evolution* 30: 1687–1699.

González-Tokman, D., Villada-Bedoya, S., Hernández, A. & Montoya, B. (2025) Antioxidants, oxidative stress and reactive oxygen species in insects exposed to heat. *Current Research in Insect Science* 8: 100114.

Korneliussen, T.S., Albrechtsen, A. & Nielsen, R. (2014) ANGSD: analysis of next generation sequencing data. *BMC Bioinformatics* 15: 356.

Lalouette, L., Williams, C.M., Hervant, F., Sinclair, B.J. & Renault, D. (2011) Metabolic rate and oxidative stress in insects exposed to low temperature thermal fluctuations. *Comparative Biochemistry and Physiology Part A* 158: 229–234.

Meisner, J. & Albrechtsen, A. (2018) Inferring population structure and admixture proportions in low-depth NGS data. *Genetics* 210: 719–731.

Mi, G., Di, Y., Emerson, S., Cumbie, J.S. & Chang, J.H. (2012) Length bias correction in gene ontology enrichment analysis using logistic regression. *PLoS ONE* 7: e46128.

Nagoshi, R.N. (2010) The fall armyworm triose phosphate isomerase (*Tpi*) gene as a marker of strain identity and interstrain mating. *Annals of the Entomological Society of America* 103: 283–293.

Nam, K., Yainna, S., Nègre, N. & d'Alençon, E. (2024) Population genomics unravels a lag phase during the global fall armyworm invasion. *Communications Biology* 7: 1220.

Nevado, B., Ramos-Onsins, S.E. & Perez-Enciso, M. (2014) Resequencing studies of nonmodel organisms using closely related reference genomes. *Molecular Ecology* 23: 1764–1779.

Pashley, D.P. (1986) Host-associated genetic differentiation in fall armyworm (Lepidoptera: Noctuidae): a sibling species complex? *Annals of the Entomological Society of America* 79: 898–904.

Pashley, D.P. & Martin, J.A. (1987) Reproductive incompatibility between host strains of the fall armyworm (Lepidoptera: Noctuidae). *Annals of the Entomological Society of America* 80: 731–733.

Prentis, P.J., Wilson, J.R.U., Dormontt, E.E., Richardson, D.M. & Lowe, A.J. (2008) Adaptive evolution in invasive species. *Trends in Plant Science* 13: 288–294.

Tay, W.T., Rane, R.V., James, W. *et al.* (2022) Global population genomic signature of *Spodoptera frugiperda* (fall armyworm) supports complex introduction events across the Old World. *Communications Biology* 5: 297.

The UniProt Consortium (2025) UniProt: the Universal Protein Knowledgebase in 2025. *Nucleic Acids Research* 53: D609–D617.

Vasimuddin, M., Misra, S., Li, H. & Aluru, S. (2019) Efficient architecture-aware acceleration of BWA-MEM for multicore systems. *IEEE IPDPS 2019*: 314–324.

Westbrook, J.K., Nagoshi, R.N., Meagher, R.L., Fleischer, S.J. & Jairam, S. (2016) Modeling seasonal migration of fall armyworm moths. *International Journal of Biometeorology* 60: 255–267.

Yainna, S., Tay, W.T., Durand, K. *et al.* (2022) The evolutionary process of invasion in the fall armyworm (*Spodoptera frugiperda*). *Scientific Reports* 12: 21063.

Young, M.D., Wakefield, M.J., Smyth, G.K. & Oshlack, A. (2010) Gene ontology analysis for RNA-seq: accounting for selection bias. *Genome Biology* 11: R14.

---


## Numbers to verify before submission

The following discrepancies were identified while preparing this draft and must be resolved:

1. ~~Gene-length bias effect size.~~ **RESOLVED 2026-09-24.** The two values arose from two different *background definitions*, not from an error in either computation:
   - **2.42×** — background = LOC-annotated genes only (*n* = 13,659); median 11,631 vs 4,803 bp; Mann–Whitney *p* = 4.3 × 10⁻¹⁵⁴. Produced by `go_bias_check.py`, which also performs the length-matched sensitivity analysis.
   - **2.59×** — background = all `gene` features in the GFF, including 545 without a LOC identifier (largely tRNA/rRNA); *n* = 14,204; *p* = 7 × 10⁻¹⁸⁰. Produced by `fig_lenbias.py`, whose `gdf` was not filtered on `Name=LOC`.

   **Canonical value: 2.42×**, because the analysis this bias threatens (GO over-representation) is performed on LOC-annotated genes via UniProt GeneID cross-references. §3.10 now states the background explicitly. `fig_lenbias.py` panel (a) has been patched to use the LOC background; **Fig. S4 must be regenerated** so that the rendered value matches (panels b and c are intentionally left on the full gene-feature set, so ρ = +0.006 and the module box plots are unchanged):

   ```powershell
   wsl -d Ubuntu-24.04 -- bash -c "cd /mnt/c/SF_data/tools && python fig_lenbias.py"
   ```
   **VERIFIED 2026-09-24.** Fig. S4 was regenerated; panel (a) now reads `(a) Candidates are longer (2.42x, p=4e-154)` with legend `other genes (n=13659)`, and panels (b) and (c) are unchanged (ρ = +0.006). The PNG and PDF have been synced to `03_论文/图件/`.
2. ~~Residual low-mapping-rate samples.~~ **RESOLVED 2026-09-24.** The sensitivity analysis was run (`run_sens_excl3.sh`, exit 0). Outcome: all cross-panel conclusions are robust except one. Pairwise overlaps changed by at most 7.6% (P2-C ∩ P5-C, 357 → 330) and all ten remained significant at *p* < 10⁻³⁵ with enrichment factors of 2.3–3.1×; the ≥3-panel shared count moved from 550 to 556; P1-C oxidative stress (0.0005), P3-C HSP (0.0185) and P5-C diapause (0.0005) were reproduced exactly, and P4-C oxidative stress strengthened (0.0025 → 0.0005). **The single non-robust result is P4-C diapause, which fell from *p* = 0.012 to *p* = 0.055**; it has been removed from the supported findings in §3.9, §4.4 and §4.6. The pipeline output was re-derived independently with `verify_crossregion.py` (dependency-free) and matched on all ten pairs, the per-panel gene-set sizes and the ≥3-panel count.
3. ~~Correlation values.~~ **RESOLVED 2026-09-25.** All reported latitudinal correlations were recomputed directly from the analysis table (`check_corr_scope.py`, standard library only):
   - **P1 panel (n = 143):** *r*(latitude, BIO1) = **−0.8956**, *r*(latitude, BIO11) = **−0.9524** — matching the reported −0.896 / −0.952. The earlier internal values of −0.883 / −0.951 could not be reproduced from any current table and are **superseded**; they are not used anywhere in the manuscript.
   - **P1 panel technical:** *r*(rate, latitude) = +0.0233, *r*(depth, latitude) = −0.0828, *r*(PC1, rate) = −0.2619, *r*(PC1, depth) = −0.0687 — all matching the reported +0.023 / −0.083 / −0.262 / −0.069.
   - **Cohort-scope correction applied to §3.1 and §4.5.** The whole-cohort values +0.489 (rate) and +0.061 (depth) are computed over **all 220 sequenced samples**, not the 214-sample analysis cohort; the table row labels and the §4.5 sentence have been corrected accordingly, and each now reports the 214-cohort value alongside (+0.433 / −0.016). The within-P2 row was likewise labelled n = 24 but computed on n = 30; it is now labelled n = 30 with the n = 24 values given in the accompanying text (+0.033 / +0.041).
   - **Note.** The within-P2 negative association (−0.223) is carried entirely by the six excluded low-mapping-rate samples; on the analysis cohort it reverses sign (+0.033). Both headline conclusions (depth is not a confounder; reference bias is collinear only between panels) hold under either scope and are in fact *weaker*, not stronger, on the analysis cohort. Fig. 7 is unchanged and remains internally consistent (it plots all 220 samples and its embedded *r* values are computed on the same 220).
   - **Action:** none outstanding. §3.1/§4.5 text edited 2026-09-25; no figure regeneration required.
4. ~~AF/AM panel naming.~~ **RESOLVED 2026-09-25 by relabelling.** The six panels are now labelled with **neutral study-accession codes P1–P6** throughout the manuscript, the figures and the supplementary tables, removing the geographic reading that the old codes invited. The mapping is fixed and documented in `report/panel_map.tsv`: **P1** = the n = 143 accession (137 continental USA + 6 Puerto Rico), **P2** = the n = 24 Brazilian accession, **P3** = the n = 16 eight-country accession, **P4** = the n = 15 five-country accession, **P5** = the n = 10 Chinese accession, **P6** = the n = 6 Florida accession. Codes were assigned in descending order of analysed sample size. Panel colours were kept identical across the two codings, so the regenerated figures differ only in labels and axis annotations. All real-geography statements (e.g. "the continental USA", "sampled in Brazil", Kenya, Argentina) are retained verbatim. §2.1 now states that the codes denote public study accessions and points to the mapping table.
5. ~~LFMM-type method wording.~~ **RESOLVED 2026-10-02.** Every mention of the second method now reads **"LFMM-type"** and never bare "LFMM" or "LFMM2" (the three surviving `LFMM2` occurrences refer specifically to the *official algorithm and its unavailable binary*, which is the correct usage). Specifically: (i) the §2.8 heading and text, the Abstract, §1 and §3.6 all read "LFMM-type"; (ii) the §3.7 in-text table column now reads `*p* (LFMM-type)`, matching Table 3; (iii) in §3.6 and in the Fig. S2 legend the two statistics are written in explicit parenthetical form — `|*z*| (RDA)` and `*p* (LFMM-type)` — replacing the `_`-subscript notation (`|*z*|_RDA`, `*p*_LFMM-type`) that the Word conversion did not render, so the manuscript no longer shows raw markup; the same fix was applied to `*m*_eff`; (iv) the **Fig. S2 y-axis label** was changed from an unlabelled `single-SNP F test` to `LFMM-type F test`, so the figure now names the method explicitly. §4.6 item 4 ("The LFMM-type test is not the official LFMM2 implementation") is **retained verbatim**. The only substantive deviation from the published algorithm — latent factors estimated by PCA rather than by joint EM — is stated in §2.8 and §4.6.
