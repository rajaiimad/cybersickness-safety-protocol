# Results map

Every table, figure and quoted number of the paper, with the step that produces it and the file it is read from.
All files are under `outputs/`. `pipeline/40_verify.py` checks every entry below against the printed paper.

## Main text

| Item | Content | Produced by | Read from |
|---|---|---|---|
| Table I | Evaluation designs of published studies | literature (no computation) | — |
| Table II | Dataset composition and recovered units | step 01 | `tables/T_dataset_facts.csv` |
| Table III | Primary comparison (fold, threshold free, pooled, all groups) | steps 20, 25 | `tables/T_primary.csv`, `tables/T_lpgo_atime.csv` |
| Table IV | Paired comparison with the clock and with elapsed time | steps 24, 25 | `tables/T_primary_stats.csv`, `tables/T_lpgo_atime.csv` |
| Table V | Severity errors under three levels of control | steps 20, 24 | `tables/T_severity.csv`, `tables/T_asev_paired.csv` |
| Table VI | Positive and negative controls | step 16 | `tables/T_controls.csv` (replicates: `tables/CTRL_LR.csv`) |
| Table VII | Reporting checklist | text (no computation) | — |
| Table VIII | Feature list (counts) | step 31 (counted from `csp.design`) | `paper_tables/Table_VIII.csv` |
| Fig. 1 | Evaluation protocol | step 30 | `figures/fig1_protocol.png` |
| Fig. 2 | Random window splitting against group disjoint evaluation | steps 20, 24, 30 | `tables/T_leakage.csv`, `tables/T_leakage_loro.csv` → `figures/fig2_leakage.png` |
| Fig. 3 | Primary comparison panel | steps 20, 25, 30 | `tables/T_primary.csv`, `tables/T_lpgo_atime.csv`, `predictions/P_primary*.csv` → `figures/fig3_primary.png` |
| Fig. 4 | Severity at controlled operating points | steps 20, 24, 30 | `tables/CURVE_s3_vs_alarm.csv`, `tables/T_asev_*.csv` → `figures/fig4_severity.png` |
| Fig. 5 | Smoothing window and nested feature analysis | steps 20, 30 | `tables/T_smoothing.csv`, `tables/T_ablation.csv`, `tables/T_original99.csv` → `figures/fig5_temporal.png` |
| Fig. 6 | Positive and negative controls | steps 16, 25, 30 | `tables/T_lpgo_atime.csv`, `tables/T_controls.csv` → `figures/fig6_controls.png` |

Figure numbers follow the order of the figures in the manuscript (protocol, leakage, primary, severity, temporal,
controls). See docs/AUDIT.md, item P1: the submitted manuscript labels two figures "Fig. 2".

## Supporting Information

| Item | Content | Produced by | Read from |
|---|---|---|---|
| Table S1 | 73 secondary tests with one BH adjustment | step 26 | `tables/T_secondary_tests.csv` |
| Table S2 | 99 features and LORO sensitivity | step 20 | `tables/T_original99.csv`, `tables/T_full99_mlp.csv`, `tables/T_loro.csv`, `tables/T_constants.csv` |
| Table S3 | PPV, NPV, false alarms, alarm onsets | step 20 | `tables/T_deploy.csv`, `tables/T_primary.csv` |
| Table S4 | Prior shift transfer after calibration | step 13 | `tables/T_prior_shift.csv` |
| Table S5 | Episodes with the shifted reference | steps 20, 21 | `tables/T_episodes.csv`, `tables/T_episode_random_reference.csv` |
| Table S6 | A_sev per group | steps 21, 24 | `tables/T_asev_by_group.csv`, `tables/T_s3_by_group.csv` |
| Table S7 | Control details | step 16 | `tables/T_controls.csv` |
| Note S1 | Closed form bootstrap | `src/csp/inference.py` (`ATime`) | equality with the resampling estimator asserted in step 24 |

## Numbers quoted in the text

`reference/paper_numbers.csv` lists 268 numbers quoted in the abstract and Sections III to VI, each with its
location and the expression that recomputes it from `outputs/tables`. The main sources:

| Section | Quantity | File |
|---|---|---|
| III-A | windows, prevalence, label changes, archive facts, 7.2 min, group spans, restarts | `T_dataset_facts.csv`, `T_archive_facts.csv` |
| III-B | zero IQR features per fold | `T_dataset_facts.csv` |
| V-A | leakage demonstration (0.995, 0.989, 1.000 against 0.670, 0.325, 0.730; LORO 0.307) | `T_leakage.csv`, `T_leakage_loro.csv` |
| V-A | fold MCC, paired tests, MDE, groups needed, seeds | `T_primary.csv`, `T_primary_stats.csv`, `T_sup_seeds.csv` |
| V-A | fold AUC, time matched AUC (LPGO and pooled) | `T_primary.csv`, `T_primary_stats.csv`, `T_lpgo_atime.csv` |
| V-A | 99 features, LORO, merged grouping, LORO by group type | `T_original99.csv`, `T_loro.csv`, `T_merged.csv`, `T_loro_by_grouptype.csv`, `T_constants.csv` |
| V-B | severity 3 misses, six recording group, A_sev | `T_severity.csv`, `T_s3_by_group.csv`, `T_s3_without_big_group.csv`, `T_asev_paired.csv`, `T_asev_by_group.csv` |
| V-C | persistence rules, smoothing sweep, nested w, episodes, nested features | `T_constants.csv`, `T_smoothing*.csv`, `T_nested_w*.csv`, `T_episodes.csv`, `T_episode_random_reference.csv`, `T_ablation.csv` |
| V-D | PPV at low prevalence, false alarms per 1,000, onsets, prior shift | `T_deploy.csv`, `T_primary.csv`, `T_prior_shift.csv` |
| V-E, VI-C | time only controls, detection rates, calibrated thresholds, half widths, null spread | `T_lpgo_atime.csv`, `T_controls.csv`, `CTRL_LR.csv` |
| V | 73 secondary tests, 2 unadjusted p < 0.05, none after BH | `T_secondary_tests.csv` |
