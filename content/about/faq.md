#### Frequently asked questions

**Can I compare results across datasets?**
Not yet. In v0.1.0 each plot shows one dataset at a time.

**Why can't I find my gene?**
Gene names use symbols from the GENCODE mouse annotation (release M37).
Try the official symbol (for example, *Pkd2* rather than *polycystin-2*).

**Can I download the full processed datasets?**
Yes. The processed data for each release are archived on Zenodo
(v0.1.0: [doi:10.5281/zenodo.24325117](https://doi.org/10.5281/zenodo.24325117); see also Code and data availability).
You can also download the data behind any plot as CSV from the Charts page.

#### Glossary

- **TPM (transcripts per million):** expression normalized for gene length
  and sequencing depth, so values within a sample are comparable across genes.
- **log₁₀(TPM + 1):** the scale used in plots. Adding 1 keeps unexpressed
  genes (TPM = 0) on the plot at 0.
- **BioProject:** the NCBI accession grouping all samples from one study.
- **Group:** the experimental condition (genotype, treatment, or both) that
  samples are plotted by.
- **Underlying variant:** the PKD-related gene variant modeled in a dataset.
- **Violin plot:** a plot that shows the full distribution of values in each
  group. Wider sections mean more samples at that expression level.
