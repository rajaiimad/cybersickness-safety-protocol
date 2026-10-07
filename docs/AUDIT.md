# Code audit and reproduction report

Scope: this repository against the submitted manuscript (IEEE format) and its Supporting Information. The audit was
done while building this release, in two passes: one while porting every script, and a second, independent pass
that read the methods and the code line by line. No finding changed a reported number. The
scientific method was not changed anywhere.

## 1. Reproduction

| Check | Result |
|---|---|
| Tables of this release recomputed from the original predictions, against the original result tables | identical, maximum absolute difference 0, in all 36 tables that the original run produced (for `T_original99` and `T_severity`, on the rows and columns kept; the removed ones concern the reinforcement learning detectors). The other 3 tables (`T_dataset_facts`, `T_archive_facts`, `T_recovered_units`) are new in this release and are frozen in `reference/tables` |
| Tables as printed in the manuscript (II to VI, VIII) and Supporting Information (S1 to S7), cell by cell | all 13 tables match |
| Numbers quoted in the abstract and text (`reference/paper_numbers.csv`) | 268 of 268 reproduce |
| Figures 1 and 3 to 6 against the images in the manuscript | byte for byte identical |
| Figure 2 (leakage) | drawn separately for the manuscript; every plotted value equals `T_leakage.csv` / `T_leakage_loro.csv`; step 30 redraws it |
| Full refit from the raw data (`run_all.py --full`) | see section 3 |

## 2. Leakage audit

Checked and found correct, in every design (LOGO, LORO, merged, nested validation, LPGO, controls):

* Features use the current and past windows of the same recording only (trailing rolling windows with
  `min_periods=1`, expanding means, first difference within the recording); no feature crosses recordings or looks ahead.
* The four constant field of view features and the descriptor indicators are removed by a rule that uses no labels.
* `RobustScaler` is fitted on the training rows of each fold only.
* Hyperparameters are fixed in advance; MLP early stopping uses validation groups drawn from the training groups only.
* The nested analysis (step 13) asserts that validation and test groups are disjoint from the training groups; the
  smoothing window and the isotonic calibration map are chosen on validation groups only.
* LPGO models are trained on the 20 groups outside each pair (asserted).
* The matched alarm threshold (rate 0.44) is set on pooled held out scores without labels and is reported as
  descriptive.
* The random 5 fold split leaks by design (it is the leakage demonstration).

Assertions added in this release (they do not change any result and make the statement of Section III-B literally
true): in every design built by `design.run`, no held out unit has a row in training and, under LOGO, no recording is
on both sides of a fold; the same for the LPGO pairs (step 15) and the control folds and pairs (step 16); the two
merged restart pairs have different descriptors; the MLP validation split raises an error instead of continuing if no
split with both classes exists (it never happens on these data).

## 3. Full refit from the raw data

Run: `CSP_OUTPUTS=<fresh folder> python run_all.py --full` in the reported environment (Python 3.11.15,
scikit-learn 1.8.0, numpy 2.4.4, pandas 3.0.2, scipy 1.17.1, 2 CPUs).

Every model was refitted from `data/raw/dataset.csv` into an empty output folder and compared with the shipped
predictions (`40_verify.py` prints this comparison for every file).

| Step | Fits | Largest difference from the shipped predictions |
|---|---|---|
| 10 | initial analysis, 99 features | 2.2e-16 |
| 11 | primary LOGO, LORO, merged, random split, 99 feature MLP, nested features, clocks (13 files) | 4.4e-16 |
| 12 | seeds 1 and 2 | 2.2e-16 |
| 13 | validation group fits | 2.2e-16 |
| 14 | RF, LORO, 99 features | 2.2e-16 |
| 15 | 216 LPGO pairs × 8 models (with the reported thread setting, see R1) | 5.6e-16 |
| 16 | 2,400 control replicates (every column of `CTRL_LR.csv`) | 0 |

The differences of order 1e-16 come from the random forest (the order in which the probabilities of the 300 trees
are summed across parallel workers); GB, LR, the MLP and the clock are bit for bit identical. After the refit, every
result table equals the reported one to within 1.1e-16, all 13 printed tables match cell by cell, and all quoted
numbers reproduce (`ALL CHECKS PASSED`); the six figures and the 13 formatted paper tables are byte for byte the
shipped ones. Runtime on 2 CPUs: about 3.5 hours (LPGO 57 min, controls about 75 min,
step 11 about 30 min).

**Thread count (finding R1).** Only one model depends on the number of BLAS threads: the logistic regression on the
76 features, whose lbfgs solution moves slightly with the thread count (up to 0.065 in a predicted probability for one
LPGO pair, up to 0.017 under LOGO). Comparing the shipped LPGO files with refits at 1 and at 2 threads shows that the
reported LPGO run fitted its first 14 pairs with 2 threads and was then resumed with `OMP_NUM_THREADS=1` for the other
202 pairs; every one of the 216 files matches exactly one of the two settings. Step 15 now reproduces this mix
(`REPORTED_2THREAD_PAIRS`), and `run_all.py` pins every other step to the 2 threads of the reported run. Effect on the
reported results: with 2 threads for all pairs, the lower 95% limit of the LR's LPGO time matched AUC in Table III
becomes 0.433 instead of 0.432 (largest change in any table 2.8e-4); with 1 thread for all pairs the largest change is
1.1e-5; under LOGO with 1 thread the LR's fold mean MCC is unchanged (0.1974). No conclusion depends on it. The
paper's statement that seeds are fixed is correct, but it could add: "all fits used 2 CPU threads (the LR solution
depends slightly on the BLAS thread count)".

## 4. Implementation details the paper should state more precisely

None of these changes a result; each is a description gap that a reader reimplementing the method from the paper
would hit. Suggested wording is given so the text can be aligned with the code.

| # | Code | Paper now | Suggested text |
|---|---|---|---|
| A1 | The MLP is trained one epoch per call of `MLPClassifier.fit(max_iter=1, warm_start=True)`; scikit-learn recreates the Adam optimiser state at each call and uses the same minibatch order every epoch. Other settings are scikit-learn defaults (ReLU, L2 penalty 1e-4, batch size 200, learning rate 1e-3), no class weights, improvement threshold 1e-4 on validation log loss. | "trained with Adam"; "patience 10 on validation log loss" (Appendix B) | Appendix B: "Each epoch is one call of scikit-learn's MLPClassifier with warm start, so the Adam moment estimates restart at every epoch; ReLU activations, L2 penalty 1e-4, batch size 200, learning rate 0.001, no class weights; an epoch counts as an improvement when the validation log loss falls by more than 1e-4." |
| A2 | `GroupShuffleSplit(test_size=0.15)` selects 4 of the 21 training groups (rounded up; 3 of 20 in the LPGO models, 3 of 18 in the nested fits); the first seed from 42 that gives both classes is used. | "approximately 15% of the training groups" (Section IV-A, Appendix B) | "four of the 21 training groups (a 15% group split rounded up), drawn at random with both classes required" |
| A3 | The MLP's scaler is fitted on all training groups including its inner validation groups; under the merged grouping and LORO the inner validation split is by reconstructed group. Nothing reaches the held out unit. | not stated | Section IV-A, one clause: "the inner validation split uses the reconstructed groups of the training partition" |
| A4 | Step 13 uses as validation groups the next three groups in sorted order after the held out group. | "three of the 21 training groups" | "the three groups that follow the held out group in index order" |
| A5 | The matched alarm rate is the constant 0.44; the prevalence is 0.4416. | "a pooled alarm rate of 0.44, the label prevalence" | "0.44, the label prevalence rounded to two decimals" |
| A6 | Alarm onsets are divided by the number of recordings (25 to 303 windows long). | "alarm onsets per five minute recording" (Section V-D, Table S3 note) | "alarm onsets per recording (most recordings last about five minutes)" |
| A7 | "Mean bootstrap standard error 0.060" is the mean of the 95% percentile half widths divided by 1.96. | "a mean bootstrap standard error of 0.060" (Section VI-C) | "a mean bootstrap standard error, estimated as the 95% half width divided by 1.96, of 0.060" |
| A8 | The 7.2 minute median is the median of the gaps rounded to 0.1 min; the unrounded median is 7.25 min. | "a median of 7.2 minutes" | correct as rounded; optionally "7.25 minutes" |
| A9 | The minimum detectable difference uses the central t approximation, (t₀.₉₇₅,₁₅ + t₀.₈₀,₁₅) × SD / √16. | "minimum detectable difference at 80% power" | add "(central t approximation)" |
| A10 | `T_severity.csv` contains A_sev intervals from an older bootstrap draw (`csp.metrics.a_sev`); Table V uses the 4,000 shared resamples of step 24 (`T_asev_paired.csv`). The older intervals are not printed anywhere. | — | none (documentation only) |
| A11 | Short recording means fewer than 120 windows (step 02). | "five restarts following a short recording" | optionally "a recording shorter than two minutes" |

## 5. Inconsistencies in the submitted manuscript

Found by comparing the manuscript with the code outputs and with the version generated from them. Numbers: none
wrong. Text and layout:

| # | Where | Problem | Fix |
|---|---|---|---|
| P1 | Figure captions and references | Two captions are labelled "Fig. 2" (leakage figure and primary comparison). The text calls the primary comparison "Fig. 3" once (Section V-A, first paragraph after the leakage figure) and "Fig. 2(a)", "Fig. 2(b)" later; severity, temporal and control figures are still "Fig. 3", "Fig. 4", "Fig. 5". | Renumber: leakage Fig. 2, primary Fig. 3, severity Fig. 4, temporal Fig. 5, controls Fig. 6, and update every reference: "Fig. 2(a)" → "Fig. 3(a)", "Fig. 2(b)" → "Fig. 3(b)", "Fig. 3(a)/(b)" → "Fig. 4(a)/(b)", "Fig. 4(a)/(b)" → "Fig. 5(a)/(b)", "Fig. 5(a)", "Fig. 5(b, c)" → "Fig. 6(a)", "Fig. 6(b, c)". This repository already uses 1 to 6. |
| P2 | Table I, last row | "reconstructed group terminology, 22 folds" (a search and replace artefact) | "Leave one reconstructed group out, 22 folds; recording holdout as sensitivity" |
| P3 | Table II, second row | "Recordings / reconstructed descriptor derived groups." ends with a full stop | remove the full stop |
| P4 | Section V, second paragraph; Section IV-B; leakage figure caption | missing spaces: "(Section V-A).No detector", "w=61and", "w=61corresponds", "for the RF.(a)" | insert spaces (check the inline equations in Section IV-B after typesetting) |
| P5 | Code availability | the manuscript cites `https://github.com/rajaiimad/cybersickness-safety`; the repository is now `https://github.com/rajaiimad/cybersickness-safety-protocol` and must be public at submission | update the link in the Code availability statement, make the repository public, and archive it (Zenodo) for a DOI |
| P6 | Conclusion and Section VI | "nearly doubled" and "doubled" for the same quantity (LR alarm rate on never sick groups, 0.342 → 0.677, ratio 1.98) | use one wording |
