#### 1. Find a gene

Type a gene symbol (for example, *Pkd1*) into the search box on the
[Home](/) page and press **Search Datahub**. Close misspellings are matched
automatically, and you are taken to the [Charts](/charts) page with that gene
preselected.

#### 2. Choose a dataset

On the Charts page, use the **Dataset Filter** panel to narrow the list by
scientific name, sex, age range, underlying variant, and sample type. For
**Age range**, enter a minimum and maximum and choose a unit (days, weeks,
months, or years). By default, datasets where a characteristic is "not provided" or "not
applicable" are included; uncheck those boxes to exclude them. Tick **Only
include datasets with matching controls** to keep only datasets that include
wild-type samples.

Matching datasets appear in the **Found Dataset(s)** table. Select one with
the button in the first column.

#### 3. Set plot parameters

Under **Edit Plot Parameters**, choose the gene, the experimental groups to
compare, and optionally restrict by sample type, sex, or age. Select a
statistical test if you want one:

- **Mann-Whitney** for comparing exactly 2 groups
- **Kruskal-Wallis** for 3 or more groups

#### 4. Read and export results

The violin plot shows log₁₀(TPM + 1) expression for each group. Use
**Show table** to switch to a table of summary statistics (minimum, first
quartile (Q1), median, third quartile (Q3), maximum) for screen readers or copying. **Download plot as PNG**
and **Download table as CSV** save the current view.
