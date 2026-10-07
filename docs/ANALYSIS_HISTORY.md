# Analysis history and provenance

This repository is a clean restructuring of the analysis code that produced the submitted paper. The scientific code
was copied verbatim from the original scripts; the only changes are file layout, file names, import statements (the
original scripts executed one another's source), output paths, and added assertions and documentation. Nothing that
affects a number was changed. Running the tables of this release on the original predictions reproduces every
original table exactly (maximum absolute difference 0), see docs/AUDIT.md.

The original scripts are kept in the authors' archive and are available from the corresponding author on request.

## Where each original script went

| Original script | This release |
|---|---|
| `src/preprocessing/pipeline.py` (`load_and_group`), `pipeline_v3.py` (`make_features_v3`) | `src/csp/data.py` |
| `src/analysis/pipeline_final.py` (initial analysis, 99 features) | `pipeline/10_fit_initial99.py` |
| `src/analysis/revision_v6_runs.py` | `src/csp/design.py` (top) and `pipeline/11_fit_designs.py` (runs) |
| `src/analysis/revision_v6_tables.py` | `src/csp/metrics.py` (functions) and `pipeline/20_tables.py` (tables) |
| `src/analysis/revision_v7_seeds.py` | `pipeline/12_fit_seeds.py` |
| `src/analysis/revision_v7_nested.py` | `pipeline/13_fit_nested.py` |
| `src/analysis/reviewer_sensitivity.py` (RF, LORO, 99 features) | `pipeline/14_fit_loro99.py` |
| `src/analysis/revision_v8_lpo.py` | `pipeline/15_fit_lpgo.py` |
| `src/analysis/revision_v8_controls.py` | `pipeline/16_controls.py` |
| `src/analysis/revision_v7_extra.py` | `src/csp/metrics_extra.py` and `pipeline/21_tables_extra.py` |
| `src/analysis/revision_v7_loro_diag.py` | `pipeline/22_loro_diagnostic.py` |
| `src/analysis/revision_v7_constants.py` | `pipeline/23_constants.py` |
| `src/analysis/revision_v8_core.py` | `src/csp/inference.py` and `pipeline/24_primary_statistics.py` |
| `src/analysis/revision_v8_lpo_stats.py` | `pipeline/25_lpgo_statistics.py` |
| `src/analysis/revision_v8_secondary.py` | `pipeline/26_secondary_tests.py` |
| `src/analysis/data_structure_check.py` | `pipeline/01_dataset_facts.py` (extended to every Table II and Section III count) |
| `src/analysis/archive_check.py`, `revision_v8_archive_dates.py` | `pipeline/02_archive_linkage.py` |
| `src/figures/make_figs_cavw_v9.py` | `pipeline/30_figures.py` (plus the leakage figure, Fig. 2) |
| table code of the manuscript build | `pipeline/31_paper_tables.py` |

Output names: `results/tables/v6/*` and `results/tables/v8/T8_*` became `outputs/tables/T_*`
(`T8_lpo_atime` → `T_lpgo_atime`); `v6/P_*` → `outputs/predictions/P_*`; `final_supervised_proba.csv` →
`P_initial99.csv`; the RF rows of `reviewer_loro_supervised_proba.csv` → `P_loro99_rf.csv`; `v8/lpo/` →
`outputs/predictions/lpgo/`.

## What is not in this release, and why

* Reinforcement learning detectors (E-DDQN, standard DQN) and every table that used them: they belong to the
  authors' companion manuscript and are not reported in this paper.
* The second matched alarm rate analysis of the initial analysis (rate of the reinforcement learning detector), the
  τ = 1/6 tables and the RF class weight diagnostic: not reported in this paper (the manuscript says the second matched
  analysis was removed, Section IV-B).
* The resampling version of the time matched bootstrap of revision v7 is kept as `csp.metrics.time_matched_auc`; the
  reported intervals use the closed form of `csp.inference.ATime`, and step 24 asserts that both agree to 1e-9.
* Scripts of the initial analysis that produced only superseded tables (`audit.py`, `complete_tables.py`,
  `matched_*.py`, `severity_*.py`, and others).

## How the analysis plan evolved (as stated in Section IV-B of the paper)

1. Initial analysis: 99 features (with the participant descriptor indicators), seven detectors.
2. Revision: descriptor indicators removed from the primary representation (76 features); the elapsed time clock
   adopted as the primary reference; the 99 feature set kept as a sensitivity analysis.
3. Negative controls showed that pooled LOGO scores bias the time matched AUC against models fitted to elapsed time;
   the primary time matched comparison was rescored with leave pair of groups out models; the pooled values are kept
   for comparison.
4. Calibrated control thresholds and paired comparisons under recording holdout were added last.
