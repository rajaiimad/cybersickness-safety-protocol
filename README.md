# A Safety Oriented Evaluation Protocol for Cybersickness Detection in Virtual Reality

Code, predictions and results for the paper *"A Safety Oriented Evaluation Protocol for Cybersickness Detection in
Virtual Reality: Group Disjoint Evaluation, Temporal Baselines and Severity Aware Comparison"* (R. Darabee,
M. Muniandy, W. K. Cheng, E. H. Sumiea, O. Shindi).

The paper proposes an evaluation protocol, not a new detector. On the public UFFCSData gameplay dataset (9,390
windows, 35 recordings, 22 reconstructed participant groups) it compares five supervised detectors (RF, GB, RF+GB,
LR, MLP) with an elapsed time reference (the clock) under group disjoint cross validation, scores a time matched AUC
with leave pair of groups out (LPGO) models, compares severity errors at controlled operating points, and checks what
the protocol can detect with synthetic positive and negative controls.

Everything in the paper can be checked at two levels:

* **Fast path, about 6 minutes on 2 CPUs.** Recompute every result table, the tables as printed in the paper, the six figures,
  and 268 numbers quoted in the text from the shipped window level predictions, then compare them with the paper.
* **Full path, about 3.5 hours on 2 CPUs.** Refit every model from the raw data (including the 216 LPGO pair models
  per detector and the 2,400 control replicates), then run the same tables and checks.

## Quick start

```bash
git clone https://github.com/rajaiimad/cybersickness-safety-protocol.git
cd cybersickness-safety-protocol
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt                            # Python 3.11

python run_all.py                                          # fast path (about 6 min): tables, paper tables, figures, checks
```

The run ends with `ALL CHECKS PASSED` when every table, every printed table cell and every listed number matches the
paper.

Full reproduction from the raw data, written to a separate folder so that the shipped outputs stay available for
comparison:

```bash
CSP_OUTPUTS=/tmp/csp_refit python run_all.py --full       # Windows: set CSP_OUTPUTS=C:\temp\csp_refit
```

`--full` is restartable: a step skips every model fit whose prediction file already exists. In the reported
environment it reproduces the shipped predictions to within 6e-16 and passes every check at the default tolerance;
with other library versions or hardware, pass `--tol` (for example `--tol 1e-3`) and read the per table differences.
See [Reproducing from the raw data](#reproducing-from-the-raw-data).

## Repository layout

```
cybersickness-safety-protocol/
├── README.md               this file
├── run_all.py              runs the pipeline in order (fast or --full)
├── requirements.txt        pinned versions of the reported run (environment.yml for conda)
├── LICENSE  CITATION.cff
├── data/raw/               UFFCSData files (dataset.csv and the two archives), their licence and checksums
├── src/csp/                library: paths, data and unit recovery, features, designs and detectors, metrics, statistics
│   ├── paths.py            all paths; CSP_OUTPUTS redirects the outputs
│   ├── data.py             recordings and participant groups recovered from dataset.csv (asserted), 99 features
│   ├── design.py           76 / 99 / 68 feature sets (asserted), detectors, LOGO / LORO / merged designs, fitting loop
│   ├── metrics.py          decision rule (w = 61, τ = 0.5), fold and pooled metrics, time matched AUC, A_sev, episodes
│   ├── metrics_extra.py    fold AUC, shifted alarm reference, per group severity
│   └── inference.py        closed form group bootstrap (Note S1), BH, groups needed, fold MCC
├── pipeline/               numbered steps, each a script with a docstring stating inputs, method and outputs
│   ├── 00_get_data.py            download at a pinned commit and verify SHA-256
│   ├── 01_dataset_facts.py       Table II and Section III counts; recovered units
│   ├── 02_archive_linkage.py     archive linkage and start times (Section III-A)
│   ├── 10_fit_initial99.py       initial analysis, 99 features (sensitivity)
│   ├── 11_fit_designs.py         primary LOGO, LORO, merged, random split, 99 feature MLP, nested features, clocks
│   ├── 12_fit_seeds.py           seeds 1 and 2
│   ├── 13_fit_nested.py          w chosen on validation groups; prior shift after calibration
│   ├── 14_fit_loro99.py          RF under LORO with 99 features
│   ├── 15_fit_lpgo.py            216 LPGO pair models per detector
│   ├── 16_controls.py            positive and negative controls (200 replicates per δ)
│   ├── 20_tables.py ... 26_secondary_tests.py   result tables and statistics, from saved predictions only
│   ├── 30_figures.py             Figs. 1 to 6
│   ├── 31_paper_tables.py        Tables II to VI, VIII and S1 to S7 formatted as printed
│   └── 40_verify.py              comparison with the paper (tables, printed tables, quoted numbers)
├── outputs/
│   ├── predictions/        window level held out probabilities of every model fit (lpgo/: one file per pair)
│   ├── tables/             every result table (CSV)
│   ├── paper_tables/       the paper's tables as printed (CSV and PAPER_TABLES.md)
│   └── figures/            the six figures
├── reference/
│   ├── tables/             frozen copy of the result tables of the reported run
│   ├── paper_tables/       the tables as printed in the submitted manuscript and Supporting Information
│   ├── paper_numbers.csv   268 quoted numbers with their location and the expression that recomputes them
│   └── predictions_sha256.txt   checksums of the shipped prediction files
├── docs/
│   ├── METHODS_TO_CODE.md  where each element of the method is implemented
│   ├── RESULTS_MAP.md      which step and file produce each table, figure and quoted number
│   ├── AUDIT.md            code audit, reproduction results and the inconsistencies found
│   └── ANALYSIS_HISTORY.md provenance from the original scripts and how the analysis plan evolved
└── tools/extract_paper_tables.py   used once to freeze the printed tables into reference/paper_tables
```

## Dataset

The analysis uses `dataset.csv` of UFFCSData (Porcino et al.), https://github.com/tmp1986/UFFCSData, at commit
`b5128e6`. It is included in `data/raw/` unchanged, with its AGPL-3.0 licence and SHA-256 checksums
(`data/raw/README.md`); `python pipeline/00_get_data.py` verifies the files and downloads any missing one. The two
archives (`DATABASE_SELECTED_DATA.zip`, `RAW_DATABASE.zip`) are used only by step 02 to link recordings to their start
times.

The file has no participant or recording identifier. Recordings are the maximal runs between resets of `TimeStamp`
(35) and participant groups are the combinations of the seven participant descriptors (22); `src/csp/data.py`
asserts both every time the data are loaded, and `outputs/tables/T_recovered_units.csv` lists the recording, group,
merged group and dataset rows of every recording. A participant group is a descriptor profile, not a verified person
(paper, Section III-A).

## Pipeline

| Step | What it does | Main outputs | Time (2 CPUs) |
|---|---|---|---|
| 00 | download and checksum the raw files | `data/raw/*` | seconds |
| 01 | dataset facts, recovered units | `T_dataset_facts.csv`, `T_recovered_units.csv` | seconds |
| 02 | archive linkage, start times | `T_archive_sessions.csv`, `T_raw_archive_sessions.csv`, `T_archive_facts.csv` | seconds |
| 10 | initial analysis, 99 features, five detectors, LOGO | `P_initial99.csv` | 8 min |
| 11 | every design of the paper (see docstring) | `P_primary*.csv`, `P_loro*.csv`, `P_merged*.csv`, `P_leak_*.csv`, `P_full99.csv`, `P_ablation_*.csv` | 30 min |
| 12 | seeds 1 and 2; scoring of all seeds | `P_primary_seed*.csv`, `T_sup_seeds.csv` | 6 min |
| 13 | validation group fits; nested w; prior shift | `P_nested_val.csv`, `T_nested_w*.csv`, `T_prior_shift.csv` | 5 min |
| 14 | RF under LORO, 99 features | `P_loro99_rf.csv` | 3 min |
| 15 | LPGO pair models | `predictions/lpgo/pair_*.csv` | 60 min |
| 16 | controls (`lr` runs the replicates, `summary` only summarises) | `CTRL_LR.csv`, `T_controls.csv` | 75 min |
| 20 to 26 | tables and statistics from saved predictions | `T_*.csv` | 5 min |
| 30, 31 | figures and formatted paper tables | `figures/`, `paper_tables/` | 1 min |
| 40 | verification against the paper | printed report | 1 min |

Steps 12, 13 and 16 both fit and score; on the fast path they find their prediction files and only score.

Every step can be run on its own from the repository root, for example `python pipeline/24_primary_statistics.py`.
`run_all.py --from 20` starts at a step and `run_all.py --only 30` runs one.

## Where the results come from

* Tables and figures: [docs/RESULTS_MAP.md](docs/RESULTS_MAP.md).
* Method to code: [docs/METHODS_TO_CODE.md](docs/METHODS_TO_CODE.md).
* Leakage control: whole participant groups are held out in every fold; features use current and past windows of
  the same recording only; scaling is fitted on training rows only; participant descriptors are excluded from the
  primary features; assertions check the units and that no held out unit has a row in training. The random 5 fold
  split in step 11 leaks on purpose: it is the leakage demonstration of Section V-A.

## Verification

`python pipeline/40_verify.py` prints one PASS or FAIL line per check:

1. every result table against `reference/tables` (default tolerance 1e-9);
2. every regenerated paper table against the table as printed in the submitted manuscript and Supporting
   Information, cell by cell;
3. 268 numbers quoted in the abstract and text, recomputed and formatted as printed.

When `CSP_OUTPUTS` points to a separate run, it also reports the largest difference between the new and the shipped
window level predictions of every file.

## Reproducing from the raw data

The reported predictions were produced on CPU with Python 3.11, scikit-learn 1.8.0, numpy 2.4.4, pandas 3.0.2 and
scipy 1.17.1, with 2 threads and fixed seeds (42 for the detectors, 1 and 2 for the seed analysis, 0 for the bootstrap
and the random split, `[2026, kind, round(1000 δ), replicate]` for the controls). The one exception to 2 threads is
the LPGO step, which was resumed with 1 thread after its first 14 pairs; step 15 reproduces that setting. `run_all.py`
pins `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` to 2 (override with `CSP_THREADS`) because the
logistic regression on the 76 features reaches a slightly different optimum with another number of BLAS threads (no
reported value changes at the printed precision except one interval limit, by 0.001). A full refit
in this environment reproduced the shipped predictions to within 1e-15 and every table and quoted number of the paper;
see [docs/AUDIT.md](docs/AUDIT.md), section 3, which also reports how much a different thread count changes. The
statistics and tables are computed by deterministic code from the predictions.

## Known issues in the submitted manuscript

The audit found no wrong number, but a few text and layout problems (two captions labelled Fig. 2, a search and
replace artefact in Table I, missing spaces) and some implementation details that the methods could state more
precisely (for example how the MLP's Adam optimiser is restarted each epoch). They are listed with suggested fixes in
[docs/AUDIT.md](docs/AUDIT.md), sections 4 and 5. None of them changes a result.

## Citation and licence

Please cite the paper and this repository (`CITATION.cff`). Code: MIT licence (`LICENSE`). Data: UFFCSData,
AGPL-3.0 (`data/raw/UFFCSData_LICENSE`).
