#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fill_citations.py — replace [CITE: ...] placeholders in the FAW manuscript with verified
Harvard-style in-text citations, and append a reference list.

Design decisions (per author instruction, 2026-09-24/25):
  * #1..#13 in-text markers  -> filled with real, verified references.
  * repository DOI / author contributions / funding  -> LEFT UNTOUCHED (author-specific).
  * No reference is invented. Every entry exists in references_verified_2026-09-25.md
    and was retrieved from a publisher/PubMed/DOI record this session.

Usage:
    python fill_citations.py <in.md> <out.md>
"""
import io, re, sys

# ---------------------------------------------------------------- in-text markers
# Exact placeholder text -> replacement (Harvard author-year, multiple refs separated by '; ')
INLINE = {
    "[CITE: rapid evolution during invasion; contemporary evolution]":
        "(Prentis et al., 2008; Bock et al., 2015)",
    "[CITE: invasion genomics / range forecasting]":
        "(Bock et al., 2015; Capblancq et al., 2018)",
    "[CITE: FAW global invasion]":
        "(Tay et al., 2022; Yainna et al., 2022; Nam et al., 2024)",
    "[CITE: host strain divergence; Nagoshi]":
        "(Pashley, 1986; Nagoshi, 2010; Acharya et al., 2021)",
    "[CITE: HSP selection in insects]":
        "(Bettencourt et al., 2002)",
    "[CITE: FAW diapause / overwintering limits]":
        "(Westbrook et al., 2016; Du Plessis et al., 2020)",
    "[CITE: oxidative stress thermal tolerance; SOD/catalase thermal]":
        "(González-Tokman et al., 2025)",
    "[CITE: polygenic adaptation / omnigenic]":
        "(Boyle et al., 2017)",
    "[CITE: oxidative stress thermal tolerance]":
        "(González-Tokman et al., 2025)",
    "[CITE: HSP-ROS crosstalk]":
        "(Dayalan Naidu et al., 2015; González-Tokman et al., 2025)",
    "[CITE: chill injury oxidative]":
        "(Lalouette et al., 2011)",
    "[CITE: FAW diapause / overwintering]":
        "(Westbrook et al., 2016; Du Plessis et al., 2020)",
}

# Method-section citations: inserted by anchoring on a unique sentence fragment.
# (anchor, replacement) — the anchor itself is preserved.
METHOD_ANCHORS = [
    ("retained genotype likelihoods throughout. ANGSD was run as:",
     "retained genotype likelihoods throughout. ANGSD was run as:", [  # citation appended after the code block headline
     ]),
]

# ---------------------------------------------------------------- reference list
REFS = [
 "Acharya, N., Rajotte, E.G., Dyer, J. & Meagher, R.L. (2021) *Tpi* and *COI* sequence polymorphisms reveal population structure in the fall armyworm, *Spodoptera frugiperda*. *Insects* 12: 439.",
 "Akopyan, M., Genchev, M., Armstrong, E.E. & Mooney, J.A. (2025) Reference genome choice compromises population genetic analyses. *Cell* 188: 6939\u20136952.e11.",
 "Ashburner, M., Ball, C.A., Blake, J.A. *et al.* (2000) Gene Ontology: tool for the unification of biology. *Nature Genetics* 25: 25\u201329.",
 "Bettencourt, B.R., Kim, I., Hoffmann, A.A. & Feder, M.E. (2002) Response to natural and laboratory selection at the *Drosophila hsp70* genes. *Evolution* 56: 1796\u20131801.",
 "Bock, D.G., Caseys, C., Cousens, R.D. *et al.* (2015) What we still don't know about invasion genetics. *Molecular Ecology* 24: 2277\u20132297.",
 "Boyle, E.A., Li, Y.I. & Pritchard, J.K. (2017) An expanded view of complex traits: from polygenic to omnigenic. *Cell* 169: 1177\u20131186.",
 "Capblancq, T., Luu, K., Blum, M.G.B. & Bazin, E. (2018) Evaluation of redundancy analysis to identify signatures of local adaptation. *Molecular Ecology Resources* 18: 1223\u20131233.",
 "Dayalan Naidu, S., Kostov, R.V. & Dinkova-Kostova, A.T. (2015) Transcription factors Hsf1 and Nrf2 engage in crosstalk for cytoprotection. *Trends in Pharmacological Sciences* 36: 6\u201314.",
 "Du Plessis, H., Schlemmer, M.-L. & Van den Berg, J. (2020) The effect of temperature on the development of *Spodoptera frugiperda* (Lepidoptera: Noctuidae). *Insects* 11: 228.",
 "Fick, S.E. & Hijmans, R.J. (2017) WorldClim 2: new 1-km spatial resolution climate surfaces for global land areas. *International Journal of Climatology* 37: 4302\u20134315.",
 "Forester, B.R., Lasky, J.R., Wagner, H.H. & Urban, D.L. (2018) Comparing methods for detecting multilocus adaptation with multivariate genotype\u2013environment associations. *Molecular Ecology* 27: 2215\u20132233.",
 "Frichot, E., Schoville, S.D., Bouchard, G. & Fran\u00e7ois, O. (2013) Testing for associations between loci and environmental gradients using latent factor mixed models. *Molecular Biology and Evolution* 30: 1687\u20131699.",
 "Gonz\u00e1lez-Tokman, D., Villada-Bedoya, S., Hern\u00e1ndez, A. & Montoya, B. (2025) Antioxidants, oxidative stress and reactive oxygen species in insects exposed to heat. *Current Research in Insect Science* 8: 100114.",
 "Korneliussen, T.S., Albrechtsen, A. & Nielsen, R. (2014) ANGSD: analysis of next generation sequencing data. *BMC Bioinformatics* 15: 356.",
 "Lalouette, L., Williams, C.M., Hervant, F., Sinclair, B.J. & Renault, D. (2011) Metabolic rate and oxidative stress in insects exposed to low temperature thermal fluctuations. *Comparative Biochemistry and Physiology Part A* 158: 229\u2013234.",
 "Meisner, J. & Albrechtsen, A. (2018) Inferring population structure and admixture proportions in low-depth NGS data. *Genetics* 210: 719\u2013731.",
 "Mi, G., Di, Y., Emerson, S., Cumbie, J.S. & Chang, J.H. (2012) Length bias correction in gene ontology enrichment analysis using logistic regression. *PLoS ONE* 7: e46128.",
 "Nagoshi, R.N. (2010) The fall armyworm triose phosphate isomerase (*Tpi*) gene as a marker of strain identity and interstrain mating. *Annals of the Entomological Society of America* 103: 283\u2013293.",
 "Nam, K., Yainna, S., N\u00e8gre, N. & d'Alen\u00e7on, E. (2024) Population genomics unravels a lag phase during the global fall armyworm invasion. *Communications Biology* 7: 1220.",
 "Nevado, B., Ramos-Onsins, S.E. & Perez-Enciso, M. (2014) Resequencing studies of nonmodel organisms using closely related reference genomes. *Molecular Ecology* 23: 1764\u20131779.",
 "Pashley, D.P. (1986) Host-associated genetic differentiation in fall armyworm (Lepidoptera: Noctuidae): a sibling species complex? *Annals of the Entomological Society of America* 79: 898\u2013904.",
 "Pashley, D.P. & Martin, J.A. (1987) Reproductive incompatibility between host strains of the fall armyworm (Lepidoptera: Noctuidae). *Annals of the Entomological Society of America* 80: 731\u2013733.",
 "Prentis, P.J., Wilson, J.R.U., Dormontt, E.E., Richardson, D.M. & Lowe, A.J. (2008) Adaptive evolution in invasive species. *Trends in Plant Science* 13: 288\u2013294.",
 "Tay, W.T., Rane, R.V., James, W. *et al.* (2022) Global population genomic signature of *Spodoptera frugiperda* (fall armyworm) supports complex introduction events across the Old World. *Communications Biology* 5: 297.",
 "The UniProt Consortium (2025) UniProt: the Universal Protein Knowledgebase in 2025. *Nucleic Acids Research* 53: D609\u2013D617.",
 "Vasimuddin, M., Misra, S., Li, H. & Aluru, S. (2019) Efficient architecture-aware acceleration of BWA-MEM for multicore systems. *IEEE IPDPS 2019*: 314\u2013324.",
 "Westbrook, J.K., Nagoshi, R.N., Meagher, R.L., Fleischer, S.J. & Jairam, S. (2016) Modeling seasonal migration of fall armyworm moths. *International Journal of Biometeorology* 60: 255\u2013267.",
 "Yainna, S., Tay, W.T., Durand, K. *et al.* (2022) The evolutionary process of invasion in the fall armyworm (*Spodoptera frugiperda*). *Scientific Reports* 12: 21063.",
 "Young, M.D., Wakefield, M.J., Smyth, G.K. & Oshlack, A. (2010) Gene ontology analysis for RNA-seq: accounting for selection bias. *Genome Biology* 11: R14.",
]


def main(src, dst):
    s = io.open(src, encoding="utf-8").read()
    n = 0

    # 1) exact placeholder replacements
    for k, v in INLINE.items():
        if k in s:
            s = s.replace(k, v)
            n += 1

    # 2) method-section citations, anchored on sentences already in the text
    method_subs = [
        ("ANGSD was run as:", "ANGSD was run as (Korneliussen et al., 2014):", "Korneliussen et al., 2014"),
        ("with **PCAngsd v1.36.4**, avoiding",
         "with **PCAngsd v1.36.4** (Meisner & Albrechtsen, 2018), avoiding", "Meisner & Albrechtsen, 2018"),
        ("from **WorldClim v2.1 at 10 arc-min resolution**",
         "from **WorldClim v2.1 at 10 arc-min resolution** (Fick & Hijmans, 2017)", "Fick & Hijmans, 2017"),
        ("We used partial RDA in which host strain",
         "We used partial RDA (Forester et al., 2018; Capblancq et al., 2018) in which host strain",
         "Forester et al., 2018; Capblancq et al., 2018"),
        ("the only substantive deviation from the published LFMM2 algorithm",
         "the only substantive deviation from the published LFMM2 algorithm (Frichot et al., 2013)",
         "Frichot et al., 2013"),
        ("Functional annotation was obtained from **UniProt**",
         "Functional annotation was obtained from **UniProt** (The UniProt Consortium, 2025)",
         "The UniProt Consortium, 2025"),
        ("GO over-representation was tested on",
         "GO over-representation (Ashburner et al., 2000) was tested on", "Ashburner et al., 2000"),
        ("we repeated the analysis on a **length-matched** background",
         "we repeated the analysis on a **length-matched** background (following Young et al., 2010; Mi et al., 2012)",
         "Young et al., 2010; Mi et al., 2012"),
    ]
    for old, new, tag in method_subs:
        if old in s and tag not in s:
            s = s.replace(old, new, 1)
            n += 1

    # bwa-mem2 citation, in section 2.2
    anchor = "Mapping used **bwa-mem2 2.2.1 (avx2)**"
    if anchor in s and "Vasimuddin et al., 2019" not in s:
        s = s.replace(anchor, anchor + " (Vasimuddin et al., 2019)", 1)
        n += 1

    # 3) reference-bias citation, section 4.5
    rb = re.search(r"(^### 4\.5 Reference bias as a first-order methodological problem\s*\n)", s, re.M)
    if rb and "Akopyan et al., 2025" not in s:
        insert = ("\nReference bias \u2014 the systematic loss of reads carrying alleles divergent from the "
                  "haploid reference \u2014 is increasingly recognised as a first-order problem for population "
                  "genomic inference from non-model organisms (Nevado et al., 2014; Akopyan et al., 2025). "
                  "Akopyan et al. (2025) showed that mapping to a heterospecific reference reduced SNP "
                  "recovery by 26\u201332%, depressed nucleotide diversity estimates by >30%, and materially "
                  "changed which loci were called as F<sub>ST</sub> outliers. The mapping-rate gradient we "
                  "report across panels (\u00a73.1, Fig. 7) is the same phenomenon expressed as a function of "
                  "population divergence from the reference.\n\n")
        s = s[:rb.end()] + insert + s[rb.end():]
        n += 1

    # 4) drop the scaffolding section, append the reference list
    idx = s.find("## Reference scaffolding")
    if idx != -1:
        end = s.find("## Numbers to verify before submission")
        if end == -1:
            end = len(s)
        scaff = s[idx:end]
        repl = ("## References\n\n" + "\n\n".join(REFS) + "\n\n---\n\n")
        s = s[:idx] + repl + s[end:]
        n += 1

    io.open(dst, "w", encoding="utf-8", newline="\n").write(s)
    left = re.findall(r"\[CITE:[^\]]*\]", s)
    print("replacements applied:", n)
    print("remaining [CITE: ...] markers:", len(left))
    for x in left:
        print("   ", x)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
