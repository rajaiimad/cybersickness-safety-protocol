# Methods to code

Where each element of the methodology (manuscript Sections III and IV, Appendix B, Supporting Information Note S1) is
implemented. Line numbers refer to this release.

## Data, units and features (Section III-A, III-B)

| Paper | Code |
|---|---|
| Binary label y = 1 if s ≥ 1, eq. (1) | `src/csp/data.py`, `load_and_group` (`d["y"]`) |
| Recordings = maximal runs between TimeStamp resets (35) | `src/csp/data.py`, `load_and_group` (`d["session"]`), asserted |
| Participant groups = combinations of the seven descriptors (22) | `src/csp/data.py`, `load_and_group` (`d["participant"]`), asserted; no recording spans two groups, asserted |
| Recovered units written out | `pipeline/01_dataset_facts.py` → `outputs/tables/T_recovered_units.csv` |
| Dataset facts (Table II, Section III-A counts) | `pipeline/01_dataset_facts.py` → `T_dataset_facts.csv` |
| Archive linkage, start times, 7.2 min median gap, group spans, restarts | `pipeline/02_archive_linkage.py` → `T_archive_sessions.csv`, `T_raw_archive_sessions.csv`, `T_archive_facts.csv` |
| Trailing mean and SD over W ∈ {30, 120, 300}, eqs. (2) and (3), n_t = min(W, t), σ = 0 when n_t = 1 | `src/csp/data.py`, `make_features` (`rolling(w, min_periods=1)`, pandas SD with ddof 1, `fillna(0)`) |
| First difference, eq. (4), Δ₁ = 0 | `make_features` (`diff().fillna(0)`) |
| Two cumulative exposure features (expanding means) | `make_features` (`cum_rotation`, `cum_accel`) |
| Elapsed time feature | `make_features` (`elapsed_in_session` = TimeStamp) |
| 99 feature set; primary 76 = 99 minus 19 descriptor indicators minus 4 constant field of view features; TEL 68 | `src/csp/design.py`, `PRIMARY`, `TEL` (counts asserted: 19, 7, 4, 76, 68) |
| Robust scaling with training median and IQR, eq. (5); zero IQR → centred only | `RobustScaler` fitted on the training rows of every fold (`design.run`, steps 10, 13, 14, 15, 16) |
| Zero IQR counts (two of 76 features in 19 folds, three in 3) | `pipeline/01_dataset_facts.py` |
| Assertions: 22 groups, 35 recordings, no recording in two groups, no held out unit in training | `data.load_and_group`; `design.run`; `13_fit_nested.py` (validation and test groups); `15_fit_lpgo.py`; `16_controls.py` |

## Detectors (Section III-D, Appendix B)

| Paper | Code |
|---|---|
| RF: 300 trees, min leaf 2, balanced subsample, seed 42 | `design.rf` |
| GB: histogram gradient boosting, 300 iterations, lr 0.05, 31 leaves, L2 1.0, balanced, seed 42 | `design.gb` |
| RF+GB: mean of the RF and GB probabilities of the same fold | `design.run` (`"RF+GB"`) |
| LR: balanced class weights | `design.lr` |
| MLP (256, 128), Adam, epochs chosen on validation groups (patience 10, at most 150), refitted on all training groups | `design.GroupEarlyStopMLP` (see the implementation note in its docstring and docs/AUDIT.md, finding A1) |
| Clock: LR on elapsed time alone | `pipeline/11_fit_designs.py` (`*_clock` configurations) |
| Initial analysis detectors (99 features; MLP with scikit-learn early stopping) | `pipeline/10_fit_initial99.py` |

## Designs (Section IV-A)

| Paper | Code | Predictions |
|---|---|---|
| LOGO, 22 folds (primary) | `11_fit_designs.py` → `design.run(..., pid, ...)` | `P_primary.csv`, `P_primary_clock.csv` |
| LORO, 35 folds (26 with both classes) | `11_fit_designs.py` (`sess`) | `P_loro.csv`, `P_loro_clock.csv` |
| Merged grouping, 20 folds | `11_fit_designs.py` (`merged`, defined and asserted in `design.py`) | `P_merged.csv`, `P_merged_clock.csv` |
| Random 5 fold over windows (leakage demonstration, unsmoothed) | `11_fit_designs.py` (`KFold(5, shuffle=True, random_state=0)`) | `P_leak_random_primary.csv`, `P_leak_random_full99.csv` |
| 99 feature sensitivity | `10_fit_initial99.py`; MLP refit with group early stopping in `11_fit_designs.py` | `P_initial99.csv`, `P_full99.csv` |
| Nested feature analysis (time, TEL, TEL + time) | `11_fit_designs.py` (`ablation_*`) | `P_ablation_*.csv` |
| Seeds 1 and 2 | `12_fit_seeds.py` | `P_primary_seed1.csv`, `P_primary_seed2.csv` |
| Validation groups (3 of 21, refit on 18): nested w and calibration | `13_fit_nested.py` (validation groups = the next three groups in sorted order) | `P_nested_val.csv` |
| RF under LORO with 99 features | `14_fit_loro99.py` | `P_loro99_rf.csv` |
| LPGO: 216 pair models per detector, trained on the other 20 groups | `15_fit_lpgo.py` | `lpgo/pair_<g>_<h>.csv` |

## Operating rule and metrics (Sections III-C, III-E, III-F)

| Paper | Code |
|---|---|
| Trailing mean of the score, eq. (8); alarm if ≥ τ, eq. (9); w = 61, τ = 0.5 | `src/csp/metrics.py`, `W, TAU`, `trailing`, `decisions` |
| Recall, specificity, alarm rate, BA eq. (10), MCC eq. (11) (0 when the denominator is 0) | `src/csp/data.py`, `counts`, `rates` |
| Fold means over the 16 two class folds with 95% t half widths; pooled values over 22 folds | `metrics.summarise`, `data.ci95` |
| False alarm rate averaged over all 22 groups; alarm rate of the six never sick groups | `metrics.summarise` (`fa_all`, `never_sick_alarm`) |
| Fold AUC | `metrics.summarise`, `metrics_extra.fold_auc` |
| Time matched AUC, eq. (12): 30 s bins with ≥ 20 positive and ≥ 20 negative windows | `metrics.time_matched_auc` (resampling version); `inference.ATime.tables` (closed form) |
| LPGO time matched AUC, eq. (13) | `inference.ATime.tables_lpo`; `pipeline/25_lpgo_statistics.py` |
| Closed form group bootstrap (Note S1), 1,000 resamples, seed 0, shared by all detectors | `inference.boot_multiplicities`, `ATime.value`; equality with the resampling estimator asserted in step 24 |
| Severity misses at the primary rule and at matched alarm rate 0.44 | `metrics.summarise`, `metrics.matched_alarm` |
| A_sev, eq. (17), pair and equal weights, 4,000 group bootstrap resamples | `pipeline/24_primary_statistics.py` (Table V); `metrics.a_sev` (point estimate in `T_severity.csv`) |
| Episodes, eq. (7), latency, pre onset share | `metrics.episodes` |
| Circularly shifted alarm reference (500 shifts) | `metrics_extra.random_reference` |
| PPV, NPV, false alarms, eqs. (14) to (16) | `metrics.deploy` |
| Prior shift after isotonic calibration on validation groups | `13_fit_nested.py` (section 2) |

## Statistics

| Paper | Code |
|---|---|
| Paired t test on fold MCC (16 folds) | `24_primary_statistics.py` (`ttest_rel`) |
| Nadeau and Bengio correction, variance × (1/J + n_test/n_train), J = 16 | `24_primary_statistics.py` (`rho`, `t_nb`) |
| Wilcoxon signed rank (zeros dropped; fold AUC with zeros split) | `24_primary_statistics.py` (`zero_method="zsplit"` for fold AUC) |
| Benjamini–Hochberg over the five detectors | `inference.bh` |
| Minimum detectable difference at 80% power, two sided 5% (central t approximation); groups needed for 0.10 | `24_primary_statistics.py` (`mult`), `inference.n_needed` |
| Bonferroni intervals at 1 − 0.05/5 | `24_primary_statistics.py`, `25_lpgo_statistics.py` |
| 73 secondary tests with one BH adjustment (Table S1) | `26_secondary_tests.py` |

## Controls (Section IV-C, V-E)

| Paper | Code |
|---|---|
| State signal z_t = δ y_t + e_t; trait signal z_r = δ 1[recording ever sick] + e_r | `16_controls.py`, `synthetic` |
| Control detector: balanced LR on [elapsed time, z], LOGO and LPGO | `16_controls.py`, `logo_proba`, `lpo_scores` |
| 200 replicates per δ; seeds `[2026, kind, round(1000 δ), rep]` | `16_controls.py`, `one`, `run_grid` |
| Detection rules (paired t p < 0.05 with positive difference; lower 95% limit > 0) and calibrated threshold (97.5th percentile of the null) | `16_controls.py`, `summarise_controls` |
| Time only negative controls (clock, RF and GB on elapsed time) | `15_fit_lpgo.py` (`RF time only`, `GB time only`), `24`, `25` |
