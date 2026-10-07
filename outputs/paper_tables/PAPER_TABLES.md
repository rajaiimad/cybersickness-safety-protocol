# Tables of the paper, regenerated from outputs/tables


## Table II

| Property | Value |
|---|---|
| Windows | 9,390 |
| Recordings / reconstructed descriptor derived groups | 35 / 22 |
| Groups with no positive window | 6 |
| Groups containing both classes | 16 of 22 |
| Negative windows (st = 0) | 5,243 |
| Positive windows (st ≥ 1); prevalence | 4,147; 0.44 |
| Severity 1 / 2 / 3 windows | 2,656 / 670 / 821 |
| Groups with any severity 3 window | 7 |
| Positive episodes | 31 |
| Features, primary / full (Appendix A) | 76 / 99 |

## Table III

| Detector | Fold MCC ± 95% half width | Fold recall | Fold specificity | Fold alarm rate | Atime LPGO [95% CI] | Fold AUC ± 95% | Pooled MCC | Pooled alarm rate | False alarm rate, all 22 groups | Alarm, no sickness groups |
|---|---|---|---|---|---|---|---|---|---|---|
| RF | 0.448 ± 0.183 | 0.613 | 0.882 | 0.403 | 0.653 [0.513, 0.792] | 0.897 ± 0.091 | 0.316 | 0.338 | 0.141 | 0.248 |
| GB | 0.461 ± 0.182 | 0.624 | 0.893 | 0.398 | 0.621 [0.481, 0.765] | 0.872 ± 0.097 | 0.326 | 0.324 | 0.144 | 0.298 |
| RF+GB | 0.462 ± 0.185 | 0.622 | 0.895 | 0.395 | 0.640 [0.495, 0.788] | 0.891 ± 0.095 | 0.325 | 0.323 | 0.141 | 0.292 |
| LR | 0.197 ± 0.137 | 0.417 | 0.839 | 0.339 | 0.535 [0.432, 0.650] | 0.818 ± 0.102 | 0.148 | 0.375 | 0.189 | 0.342 |
| MLP | 0.288 ± 0.157 | 0.465 | 0.850 | 0.351 | 0.585 [0.484, 0.708] | 0.829 ± 0.109 | 0.221 | 0.318 | 0.152 | 0.152 |
| Clock (reference) | 0.365 ± 0.171 | 0.552 | 0.869 | 0.400 | 0.530 [0.521, 0.544] | 0.866 ± 0.103 | 0.268 | 0.386 | 0.165 | 0.338 |

## Table IV

| Detector | MCC | ΔMCC | t test p | Corrected p | Wilcoxon p | BH p | ΔAtime LPGO [95% CI] | Bonferroni CI | ΔAtime pooled [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| RF | 0.448 | +0.083 | 0.244 | 0.394 | 0.464 | 0.464 | +0.123 [−0.014, 0.260] | [−0.050, 0.284] | +0.110 [−0.035, 0.239] |
| GB | 0.461 | +0.097 | 0.204 | 0.353 | 0.464 | 0.464 | +0.091 [−0.046, 0.228] | [−0.089, 0.261] | +0.088 [−0.052, 0.220] |
| RF+GB | 0.462 | +0.097 | 0.204 | 0.352 | 0.464 | 0.464 | +0.110 [−0.030, 0.251] | [−0.071, 0.282] | +0.105 [−0.046, 0.236] |
| LR | 0.197 | −0.167 | 0.093 | 0.214 | 0.093 | 0.464 | +0.005 [−0.099, 0.117] | [−0.139, 0.149] | −0.013 [−0.134, 0.105] |
| MLP | 0.288 | −0.076 | 0.100 | 0.225 | 0.193 | 0.464 | +0.056 [−0.041, 0.172] | [−0.094, 0.212] | +0.008 [−0.088, 0.123] |

## Table V

| Detector | Primary rule alarm rate | Primary rule S3 missed | Matched 0.44 S3 missed | Matched 0.44 recall | Matched 0.44 specificity | Asev | Δ vs clock [95% CI] | Δ equal weights [95% CI] | Groups above clock |
|---|---|---|---|---|---|---|---|---|---|
| RF | 0.338 | 413 | 279 | 0.604 | 0.690 | 0.779 | +0.078 [−0.112, 0.311] | −0.084 [−0.291, 0.121] | 1 of 6 |
| GB | 0.324 | 420 | 330 | 0.609 | 0.694 | 0.813 | +0.112 [−0.098, 0.515] | +0.033 [−0.146, 0.267] | 2 of 6 |
| RF+GB | 0.323 | 421 | 305 | 0.619 | 0.702 | 0.800 | +0.099 [−0.057, 0.380] | −0.045 [−0.267, 0.185] | 1 of 6 |
| LR | 0.375 | 253 | 124 | 0.544 | 0.642 | 0.852 | +0.151 [−0.031, 0.472] | +0.062 [−0.104, 0.268] | 3 of 6 |
| MLP | 0.318 | 450 | 265 | 0.553 | 0.650 | 0.864 | +0.162 [−0.084, 0.516] | −0.012 [−0.217, 0.235] | 2 of 6 |
| Clock | 0.386 | 328 | 267 | 0.603 | 0.689 | 0.702 | — | — | — |

## Table VI

| Signal | δ | Fold MCC mean Δ | Fold MCC detected | Atime pooled mean Δ | Atime pooled detected | Atime pooled declared worse | Atime LPGO mean Δ | Atime LPGO detected | Atime LPGO detected, calibrated |
|---|---|---|---|---|---|---|---|---|---|
| state | 0 | −0.000 | 0.5% | −0.086 | 0% | 100% | −0.001 | 0% | 2.5% |
|  | 0.05 | +0.000 | 3.5% | −0.079 | 0% | 100% | +0.005 | 16% | 54% |
|  | 0.1 | +0.002 | 16% | −0.060 | 0% | 95% | +0.024 | 78% | 99% |
|  | 0.15 | +0.004 | 36% | −0.028 | 0% | 32% | +0.055 | 99% | 100% |
|  | 0.2 | +0.007 | 57% | +0.013 | 11% | 1.0% | +0.093 | 100% | 100% |
|  | 0.3 | +0.016 | 89% | +0.122 | 100% | 0% | +0.188 | 100% | 100% |
| trait | 0 | −0.011 | 0% | −0.078 | 1.5% | 36% | −0.019 | 5.0% | 2.5% |
|  | 0.5 | −0.010 | 0% | −0.049 | 4.5% | 28% | +0.007 | 7.0% | 4.0% |
|  | 1 | −0.004 | 0.5% | +0.013 | 8.5% | 15% | +0.061 | 15% | 11% |
|  | 1.5 | +0.005 | 1.0% | +0.090 | 24% | 3.0% | +0.128 | 38% | 33% |
|  | 2 | +0.007 | 0.5% | +0.131 | 43% | 0.5% | +0.162 | 56% | 49% |
|  | 3 | +0.022 | 0% | +0.154 | 47% | 0% | +0.178 | 60% | 58% |

## Table VIII

| Group | Primary | Full |
|---|---|---|
| Trailing mean | 30 | 30 |
| Trailing standard deviation | 27 | 30 |
| First difference | 9 | 10 |
| Cumulative exposure | 2 | 2 |
| Elapsed time | 1 | 1 |
| Condition indicators | 7 | 7 |
| Descriptor indicators | 0 | 19 |
| Total | 76 | 99 |

## Table S1

| Family | Detector | Contrast | Estimate | Test | p | BH p (all) |
|---|---|---|---|---|---|---|
| Fold AUC (smoothed score) | RF | fold AUC minus clock | +0.031 | Wilcoxon | 0.753 | 0.820 |
| Fold AUC (smoothed score) | GB | fold AUC minus clock | +0.006 | Wilcoxon | 0.312 | 0.820 |
| Fold AUC (smoothed score) | RF+GB | fold AUC minus clock | +0.025 | Wilcoxon | 0.753 | 0.820 |
| Fold AUC (smoothed score) | LR | fold AUC minus clock | −0.048 | Wilcoxon | 0.392 | 0.820 |
| Fold AUC (smoothed score) | MLP | fold AUC minus clock | −0.036 | Wilcoxon | 0.676 | 0.820 |
| Smoothing window w = 1 | RF | fold MCC minus clock | +0.033 | Wilcoxon | 0.860 | 0.884 |
| Smoothing window w = 1 | GB | fold MCC minus clock | +0.026 | Wilcoxon | 0.597 | 0.820 |
| Smoothing window w = 1 | RF+GB | fold MCC minus clock | +0.030 | Wilcoxon | 0.597 | 0.820 |
| Smoothing window w = 1 | LR | fold MCC minus clock | −0.140 | Wilcoxon | 0.175 | 0.820 |
| Smoothing window w = 1 | MLP | fold MCC minus clock | −0.084 | Wilcoxon | 0.051 | 0.820 |
| Smoothing window w = 15 | RF | fold MCC minus clock | +0.047 | Wilcoxon | 0.632 | 0.820 |
| Smoothing window w = 15 | GB | fold MCC minus clock | +0.056 | Wilcoxon | 0.528 | 0.820 |
| Smoothing window w = 15 | RF+GB | fold MCC minus clock | +0.056 | Wilcoxon | 0.528 | 0.820 |
| Smoothing window w = 15 | LR | fold MCC minus clock | −0.161 | Wilcoxon | 0.130 | 0.820 |
| Smoothing window w = 15 | MLP | fold MCC minus clock | −0.067 | Wilcoxon | 0.175 | 0.820 |
| Smoothing window w = 31 | RF | fold MCC minus clock | +0.069 | Wilcoxon | 0.528 | 0.820 |
| Smoothing window w = 31 | GB | fold MCC minus clock | +0.076 | Wilcoxon | 0.464 | 0.820 |
| Smoothing window w = 31 | RF+GB | fold MCC minus clock | +0.072 | Wilcoxon | 0.495 | 0.820 |
| Smoothing window w = 31 | LR | fold MCC minus clock | −0.163 | Wilcoxon | 0.159 | 0.820 |
| Smoothing window w = 31 | MLP | fold MCC minus clock | −0.052 | Wilcoxon | 0.323 | 0.820 |
| Smoothing window w = 121 | RF | fold MCC minus clock | +0.033 | Wilcoxon | 0.860 | 0.884 |
| Smoothing window w = 121 | GB | fold MCC minus clock | +0.077 | Wilcoxon | 0.562 | 0.820 |
| Smoothing window w = 121 | RF+GB | fold MCC minus clock | +0.065 | Wilcoxon | 0.632 | 0.820 |
| Smoothing window w = 121 | LR | fold MCC minus clock | −0.120 | Wilcoxon | 0.375 | 0.820 |
| Smoothing window w = 121 | MLP | fold MCC minus clock | −0.048 | Wilcoxon | 0.256 | 0.820 |
| Smoothing window w = 201 | RF | fold MCC minus clock | +0.018 | Wilcoxon | 0.860 | 0.884 |
| Smoothing window w = 201 | GB | fold MCC minus clock | +0.087 | Wilcoxon | 0.274 | 0.820 |
| Smoothing window w = 201 | RF+GB | fold MCC minus clock | +0.056 | Wilcoxon | 0.669 | 0.820 |
| Smoothing window w = 201 | LR | fold MCC minus clock | −0.075 | Wilcoxon | 0.562 | 0.820 |
| Smoothing window w = 201 | MLP | fold MCC minus clock | −0.053 | Wilcoxon | 0.632 | 0.820 |
| w chosen on validation groups | RF | fold MCC minus clock | +0.006 | Wilcoxon | 0.900 | 0.900 |
| w chosen on validation groups | GB | fold MCC minus clock | +0.041 | Wilcoxon | 0.900 | 0.900 |
| w chosen on validation groups | RF+GB | fold MCC minus clock | +0.023 | Wilcoxon | 0.860 | 0.884 |
| w chosen on validation groups | LR | fold MCC minus clock | −0.163 | Wilcoxon | 0.044 | 0.820 |
| w chosen on validation groups | MLP | fold MCC minus clock | −0.035 | Wilcoxon | 0.433 | 0.820 |
| Training seed 1 | RF | fold MCC minus clock | +0.069 | Wilcoxon | 0.464 | 0.820 |
| Training seed 1 | RF+GB | fold MCC minus clock | +0.093 | Wilcoxon | 0.433 | 0.820 |
| Training seed 1 | MLP | fold MCC minus clock | +0.005 | Wilcoxon | 0.669 | 0.820 |
| Training seed 2 | RF | fold MCC minus clock | +0.078 | Wilcoxon | 0.375 | 0.820 |
| Training seed 2 | RF+GB | fold MCC minus clock | +0.092 | Wilcoxon | 0.464 | 0.820 |
| Training seed 2 | MLP | fold MCC minus clock | −0.061 | Wilcoxon | 0.105 | 0.820 |
| 99 features (descriptors included) | RF | fold MCC minus clock | +0.071 | Wilcoxon | 0.495 | 0.820 |
| 99 features (descriptors included) | GB | fold MCC minus clock | +0.035 | Wilcoxon | 0.744 | 0.820 |
| 99 features (descriptors included) | RF+GB | fold MCC minus clock | +0.042 | Wilcoxon | 0.744 | 0.820 |
| 99 features (descriptors included) | LR | fold MCC minus clock | −0.035 | Wilcoxon | 0.706 | 0.820 |
| 99 features (descriptors included) | MLP | fold MCC minus clock | +0.000 | Wilcoxon | 0.632 | 0.820 |
| Leave one recording out | RF | fold MCC minus clock | −0.013 | Wilcoxon | 0.732 | 0.820 |
| Leave one recording out | GB | fold MCC minus clock | −0.044 | Wilcoxon | 0.407 | 0.820 |
| Leave one recording out | RF+GB | fold MCC minus clock | −0.039 | Wilcoxon | 0.493 | 0.820 |
| Leave one recording out | LR | fold MCC minus clock | −0.111 | Wilcoxon | 0.290 | 0.820 |
| Leave one recording out | MLP | fold MCC minus clock | −0.040 | Wilcoxon | 0.458 | 0.820 |
| Merged grouping (20 groups) | RF | fold MCC minus clock | +0.079 | Wilcoxon | 0.528 | 0.820 |
| Merged grouping (20 groups) | GB | fold MCC minus clock | +0.093 | Wilcoxon | 0.495 | 0.820 |
| Merged grouping (20 groups) | RF+GB | fold MCC minus clock | +0.094 | Wilcoxon | 0.495 | 0.820 |
| Merged grouping (20 groups) | LR | fold MCC minus clock | −0.169 | Wilcoxon | 0.093 | 0.820 |
| Merged grouping (20 groups) | MLP | fold MCC minus clock | −0.089 | Wilcoxon | 0.093 | 0.820 |
| Episode recall, primary rule | RF | observed minus shifted alarms | +0.029 | circular shift, one sided | 0.376 | 0.820 |
| Episode recall, primary rule | GB | observed minus shifted alarms | +0.037 | circular shift, one sided | 0.300 | 0.820 |
| Episode recall, primary rule | RF+GB | observed minus shifted alarms | +0.038 | circular shift, one sided | 0.266 | 0.820 |
| Episode recall, primary rule | LR | observed minus shifted alarms | +0.008 | circular shift, one sided | 0.560 | 0.820 |
| Episode recall, primary rule | MLP | observed minus shifted alarms | +0.098 | circular shift, one sided | 0.040 | 0.820 |
| Episode recall, primary rule | Clock | observed minus shifted alarms | +0.042 | circular shift, one sided | 0.310 | 0.820 |
| Episode recall, matched alarm rate 0.44 | RF | observed minus shifted alarms | +0.054 | circular shift, one sided | 0.210 | 0.820 |
| Episode recall, matched alarm rate 0.44 | GB | observed minus shifted alarms | −0.007 | circular shift, one sided | 0.720 | 0.820 |
| Episode recall, matched alarm rate 0.44 | RF+GB | observed minus shifted alarms | +0.033 | circular shift, one sided | 0.358 | 0.820 |
| Episode recall, matched alarm rate 0.44 | LR | observed minus shifted alarms | +0.002 | circular shift, one sided | 0.636 | 0.820 |
| Episode recall, matched alarm rate 0.44 | MLP | observed minus shifted alarms | +0.058 | circular shift, one sided | 0.186 | 0.820 |
| Episode recall, matched alarm rate 0.44 | Clock | observed minus shifted alarms | +0.008 | circular shift, one sided | 0.548 | 0.820 |
| Within group severity ranking | RF | severity ranking minus clock | +0.078 | group bootstrap, two sided | 0.652 | 0.820 |
| Within group severity ranking | GB | severity ranking minus clock | +0.112 | group bootstrap, two sided | 0.640 | 0.820 |
| Within group severity ranking | RF+GB | severity ranking minus clock | +0.099 | group bootstrap, two sided | 0.652 | 0.820 |
| Within group severity ranking | LR | severity ranking minus clock | +0.151 | group bootstrap, two sided | 0.517 | 0.820 |
| Within group severity ranking | MLP | severity ranking minus clock | +0.162 | group bootstrap, two sided | 0.633 | 0.820 |

## Table S2

| Analysis | Detector | Fold MCC ± 95% half width | Fold recall | Pooled MCC | Pooled alarm rate | False alarm rate, all units | Alarm, no sickness groups | S3 missed (of 821) |
|---|---|---|---|---|---|---|---|---|
| 99 features (descriptors included), LOGO | RF | 0.435 ± 0.179 | 0.597 | 0.311 | 0.307 | 0.146 | 0.261 | 412 |
|  | GB | 0.400 ± 0.185 | 0.562 | 0.272 | 0.321 | 0.162 | 0.306 | 451 |
|  | RF+GB | 0.407 ± 0.183 | 0.568 | 0.280 | 0.319 | 0.159 | 0.300 | 431 |
|  | LR | 0.330 ± 0.139 | 0.489 | 0.176 | 0.349 | 0.319 | 0.677 | 370 |
|  | MLP * | 0.365 ± 0.142 | 0.551 | 0.282 | 0.297 | 0.125 | 0.126 | 436 |
| 76 features, leave one recording out | RF | 0.338 ± 0.139 | 0.515 | 0.317 | 0.335 | 0.120 | 0.248 | 471 |
|  | GB | 0.307 ± 0.152 | 0.520 | 0.255 | 0.369 | 0.159 | 0.298 | 426 |
|  | RF+GB | 0.312 ± 0.151 | 0.522 | 0.260 | 0.366 | 0.156 | 0.292 | 428 |
|  | LR | 0.240 ± 0.108 | 0.479 | 0.183 | 0.378 | 0.203 | 0.342 | 246 |
|  | MLP | 0.311 ± 0.139 | 0.515 | 0.238 | 0.348 | 0.179 | 0.152 | 345 |
|  | Clock | 0.351 ± 0.146 | 0.560 | 0.266 | 0.386 | 0.154 | 0.338 | 330 |

## Table S3

| Detector | PPV π=0.44 | PPV π=0.10 | PPV π=0.01 | NPV π=0.44 | NPV π=0.10 | NPV π=0.01 | FA per 1,000 negatives | Alarm onsets per recording |
|---|---|---|---|---|---|---|---|---|
| RF | 0.660 | 0.215 | 0.024 | 0.672 | 0.935 | 0.994 | 205 | 0.69 |
| GB | 0.674 | 0.226 | 0.026 | 0.672 | 0.935 | 0.994 | 189 | 0.66 |
| RF+GB | 0.674 | 0.226 | 0.026 | 0.671 | 0.935 | 0.994 | 188 | 0.60 |
| LR | 0.535 | 0.140 | 0.015 | 0.617 | 0.919 | 0.992 | 312 | 0.86 |
| MLP | 0.601 | 0.175 | 0.019 | 0.635 | 0.925 | 0.993 | 227 | 1.03 |
| Clock | 0.608 | 0.180 | 0.020 | 0.665 | 0.934 | 0.994 | 270 | 0.86 |

## Table S4

| Detector | Posterior = 1 share | π=0.10 alarm | π=0.10 recall | π=0.10 no alarm groups | π=0.01 alarm | π=0.01 recall | π=0.01 no alarm groups |
|---|---|---|---|---|---|---|---|
| RF | 0.175 | 0.176 | 0.244 | 12 | 0.175 | 0.242 | 12 |
| GB | 0.165 | 0.174 | 0.216 | 12 | 0.165 | 0.216 | 12 |
| RF+GB | 0.176 | 0.183 | 0.233 | 11 | 0.177 | 0.232 | 11 |
| LR | 0.109 | 0.114 | 0.157 | 14 | 0.109 | 0.153 | 14 |
| MLP | 0.144 | 0.144 | 0.200 | 14 | 0.144 | 0.199 | 14 |
| Clock | 0.056 | 0.056 | 0.055 | 14 | 0.056 | 0.055 | 14 |

## Table S5

| Detector | Primary alarm | Primary episode recall | Primary shifted | Primary latency (s) | Primary pre onset | Matched episode recall | Matched shifted | Matched latency (s) | Matched pre onset |
|---|---|---|---|---|---|---|---|---|---|
| RF | 0.338 | 0.613 | 0.584 | 41.0 | 0.161 | 0.742 | 0.687 | 13.0 | 0.323 |
| GB | 0.324 | 0.548 | 0.511 | 28.0 | 0.226 | 0.581 | 0.588 | 0.0 | 0.355 |
| RF+GB | 0.323 | 0.548 | 0.510 | 31.0 | 0.194 | 0.677 | 0.645 | 3.0 | 0.323 |
| LR | 0.375 | 0.677 | 0.670 | 54.0 | 0.226 | 0.742 | 0.740 | 25.0 | 0.258 |
| MLP | 0.318 | 0.774 | 0.676 | 18.0 | 0.290 | 0.806 | 0.749 | 15.0 | 0.387 |
| Clock | 0.386 | 0.774 | 0.732 | 68.5 | 0.226 | 0.774 | 0.766 | 51.5 | 0.226 |

## Table S6

| Group | Recordings | Pairs | RF | GB | RF+GB | LR | MLP | Clock |
|---|---|---|---|---|---|---|---|---|
| 10 | 3 | 28,812 | 0.752 | 0.965 | 0.824 | 0.922 | 0.977 | 0.403 |
| 11 | 2 | 1,848 | 0.214 | 0.545 | 0.346 | 0.214 | 0.123 | 0.452 |
| 12 | 1 | 5,856 | 0.824 | 0.866 | 0.860 | 0.978 | 0.918 | 0.909 |
| 14 | 6 | 53,940 | 0.803 | 0.732 | 0.792 | 0.819 | 0.822 | 0.836 |
| 17 | 1 | 3,393 | 0.876 | 0.876 | 0.876 | 0.916 | 0.876 | 0.876 |
| 19 | 1 | 110 | 0.500 | 0.691 | 0.509 | 1.000 | 0.691 | 1.000 |

## Table S7

| Signal | δ | Replicates | Detected, MCC Wilcoxon | Detected, MCC t test | Mean Δ fold AUC | Mean Atime pooled | Mean Atime LPGO | Below reference, pooled | Below reference, LPGO |
|---|---|---|---|---|---|---|---|---|---|
| state | 0 | 200 | 1.0% | 0.5% | −0.000 | 0.444 | 0.528 | 100% | 5.0% |
| state | 0.05 | 200 | 3.0% | 3.5% | −0.000 | 0.451 | 0.535 | 100% | 0% |
| state | 0.1 | 200 | 18% | 16% | −0.001 | 0.470 | 0.554 | 95% | 0% |
| state | 0.15 | 200 | 39% | 36% | −0.000 | 0.502 | 0.584 | 32% | 0% |
| state | 0.2 | 200 | 61% | 57% | −0.000 | 0.543 | 0.622 | 1.0% | 0% |
| state | 0.3 | 200 | 90% | 89% | +0.003 | 0.651 | 0.718 | 0% | 0% |
| trait | 0 | 200 | 0% | 0% | −0.005 | 0.452 | 0.511 | 36% | 30% |
| trait | 0.5 | 200 | 0% | 0% | −0.003 | 0.481 | 0.537 | 28% | 26% |
| trait | 1 | 200 | 1.5% | 0.5% | −0.001 | 0.543 | 0.591 | 15% | 13% |
| trait | 1.5 | 200 | 1.0% | 1.0% | +0.007 | 0.620 | 0.658 | 3.0% | 2.5% |
| trait | 2 | 200 | 0.5% | 0.5% | +0.010 | 0.661 | 0.692 | 0.5% | 0.5% |
| trait | 3 | 200 | 0% | 0% | +0.018 | 0.683 | 0.708 | 0% | 0% |
