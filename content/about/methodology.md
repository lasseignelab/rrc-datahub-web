The methods below describe the current release (v0.1.0, bulk RNA-seq).
Methods for additional data types will be added as they are released.

#### Dataset selection

Datasets were identified by searching NCBI's Gene Expression Omnibus (GEO)
and PubMed for bulk RNA-seq datasets from mouse kidney in the context of PKD.
All v0.1.0 datasets were sequenced on Illumina platforms.

#### Processing pipeline

Datasets were processed with the DataHub processing pipeline
([lasseignelab/rrc-datahub](https://github.com/lasseignelab/rrc-datahub)) on UAB's Cheaha high-performance
computing cluster. Raw FASTQ files were downloaded from the European
Nucleotide Archive (ENA), which mirrors the SRA, and verified against their
MD5 checksums. Reads were processed with
[nf-core/rnaseq](https://nf-co.re/rnaseq) v3.25.0: aligned with STAR to the
GRCm39 mouse reference genome (primary assembly) with GENCODE release M37
annotation, and quantified with Salmon. Gene-level transcripts per million
(TPM) values were taken from the merged Salmon output.

nf-core/rnaseq results are not fully reproducible between runs, so the
processed outputs for each release are archived on Zenodo (v0.1.0:
[doi:10.5281/zenodo.24325117](https://doi.org/10.5281/zenodo.24325117)).

#### Metadata curation

Sample metadata were retrieved from NCBI SRA run records and their linked
BioSample attributes, then harmonized into standard fields (organism, sample
type, sex, age, underlying variant, genotype, strain, tissue, and treatment):

- Genotype descriptions were consolidated into one field, and the
  PKD-related gene in each genotype was recorded as the underlying variant
  using an explicit lookup table. Samples without a PKD-related variant are
  labeled wild-type.
- Strain and tissue names were normalized to a controlled vocabulary.
- Ages were converted from free text to postnatal days and stored as ranges
  (single ages have equal lower and upper bounds), so datasets reported in
  different units can be filtered together.
- Sample type was derived from the sample source description, and treatment
  group (experimental, vehicle control, or untreated) from the treatment.
- Missing values are labeled "Not provided" (NP); values recorded as not
  applicable in the source are labeled "Not applicable" (NA). See
  [Missing values](#missing-values).
- Only RNA-seq runs were kept; for example, miRNA-seq runs in PRJNA342113
  were excluded.

#### Quality control

Quality-control (QC) metrics, including read counts and alignment rates, were
compiled for each dataset with MultiQC. No datasets or samples were excluded
based on QC; the metrics are compiled so users can apply their own filters.
QC metrics are not yet available in the DataHub interface (see Future
directions).

#### Statistics

Plots show log₁₀(TPM + 1). Optional group comparisons are chosen
automatically from the number of groups plotted: the two-sided Mann-Whitney U
test (2 groups) or the Kruskal-Wallis test (3 or more groups).
