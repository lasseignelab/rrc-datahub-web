Sample metadata come from public records that depositors fill in
themselves, so some fields are blank or do not apply to every sample. The
DataHub uses two labels, kept separate throughout the site:

- **Not provided:** the information is missing. The depositor left the field
  blank, or no value was recorded for that sample. For example, a sample
  with no sex listed shows Not provided.
- **Not applicable:** the source record states that the field does not apply
  to that sample. For example, cell cultures do not record biological age.

How these labels affect what you see:

- **Filters:** on the [Charts](/charts) page, each "Include datasets with
  ... Not provided or Not applicable" checkbox covers both labels together.
  Uncheck it to leave those samples out.
- **Age:** ages are converted to days. Samples whose age is Not provided,
  Not applicable, or could not be converted to days are treated as unknown
  by the age filter. The original age text from the source record is shown
  when it is available.
- **Underlying variant:** samples labeled only "control" or "cystic" show
  Not provided, because those labels describe disease status rather than
  which gene is altered. Samples with no PKD-related variant are labeled
  wild-type rather than Not provided.
