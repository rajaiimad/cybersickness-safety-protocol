# Reference copies used by `pipeline/40_verify.py`

| Path | What it is | Origin |
|---|---|---|
| `tables/` | every result table of the reported run | the original analysis outputs, renamed (docs/ANALYSIS_HISTORY.md); `T_dataset_facts`, `T_archive_facts` and `T_recovered_units` are new in this release and were computed from `data/raw` |
| `paper_tables/Table_II.csv` … `Table_VIII.csv` | data rows of the main text tables as printed | extracted with `tools/extract_paper_tables.py` from the submitted manuscript (.docx) |
| `paper_tables/Table_S1.csv` … `Table_S7.csv` | data rows of the Supporting Information tables as printed | extracted from the Supporting Information source (.docx); every number in it was checked to be identical to the submitted Supporting Information PDF (733 of 733 numeric tokens) |
| `paper_numbers.csv` | 268 numbers quoted in the abstract and text: id, location, printed value, expression that recomputes it from `outputs/tables` | written by hand from the submitted manuscript; each expression is evaluated by step 40 |
| `predictions_sha256.txt` | SHA-256 of every shipped prediction file in `outputs/predictions` | computed on the shipped files |

To check the shipped predictions: `cd outputs/predictions && sha256sum -c ../../reference/predictions_sha256.txt`.
