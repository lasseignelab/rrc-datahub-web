"""
data_utils.py

Utility functions for preparing expression datasets for visualization and
downstream analysis.

Includes helpers for converting nf-core/rnaseq output tables into tidy
(long-format) dataframes suitable for plotting libraries such as Plotly and
Matplotlib, while preserving sample metadata annotations.
"""

from __future__ import annotations

import pandas as pd

# --------------------------------------------------------------------------
# TPM data preparation
# --------------------------------------------------------------------------


def melt_nfcore_tpm(
    tpm_wide: pd.DataFrame,
    sample_metadata: pd.DataFrame,
    id_col: str = "gene_name",
    sample_id_col: str = "sample",
    group_col: str = "group",
) -> pd.DataFrame:
    """
    Convert an nf-core/rnaseq merged TPM matrix (genes x samples, wide
    format) into a tidy long-format dataframe annotated with group
    membership.
    """
    sample_cols = [
        c for c in tpm_wide.columns if c in set(sample_metadata[sample_id_col])
    ]

    if not sample_cols:
        raise ValueError(
            "No overlap between tpm_wide columns and sample_metadata "
            f"'{sample_id_col}' values — check that sample names match."
        )

    long_df = tpm_wide.melt(
        id_vars=[id_col],
        value_vars=sample_cols,
        var_name=sample_id_col,
        value_name="TPM",
    )

    long_df = long_df.merge(
        sample_metadata[[sample_id_col, group_col]],
        on=sample_id_col,
        how="left",
    )

    missing = long_df[group_col].isna().sum()
    if missing > 0:
        print(f"Warning: {missing} sample rows had no matching group in metadata.")

    return long_df
