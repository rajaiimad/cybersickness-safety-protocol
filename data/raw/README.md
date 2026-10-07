# Raw data

Files of the public UFFCSData repository (Porcino et al.), https://github.com/tmp1986/UFFCSData, commit
`b5128e681786b81501d269a73e860d57c495d0aa` (2020-05-01), redistributed unchanged under their licence (AGPL-3.0,
`UFFCSData_LICENSE`). The paper cites the repository as accessed on 3 December 2024; the files analysed are those of the
commit above, identified by the checksums below.

| File | Bytes | SHA-256 | Used by |
|---|---|---|---|
| dataset.csv | 1,040,939 | 2d3ab0a82962a11ef389ea02be4b51e6b7bad6004c53cd778db2b97f6665f740 | every step |
| DATABASE_SELECTED_DATA.zip | 532,272 | 206f27a7fb2ccd83fc2dbdb767ffd641371902ea185ff41d221bea36b316031a | step 02 only |
| RAW_DATABASE.zip | 891,353 | 7dc386b21922b7a5da1d746ce06c75669e230ea8be2fd26e84e4c0356d6327bc | step 02 only |

`python pipeline/00_get_data.py` verifies these checksums and downloads any missing file from the pinned commit.

dataset.csv has 9,390 rows and 22 columns and no participant or recording identifier. Recordings (35) and participant
groups (22) are recovered by `src/csp/data.py`; the result, one row per recording with its rows in dataset.csv, is
`outputs/tables/T_recovered_units.csv`.
