"""Step 24. Statistics of the primary comparison, from saved predictions (no model is fitted).

  T_primary_stats.csv   fold MCC against the clock over the 16 two class folds: paired t test, the resampling corrected
                        t test of Nadeau and Bengio, Wilcoxon with Benjamini-Hochberg over 5, minimum detectable
                        difference (80% power, two sided 5%), two class groups needed for a true MCC difference of
                        0.10, 0.15 and 0.20; pooled time matched AUC against elapsed time from one set of 1,000 group
                        bootstrap resamples shared by all detectors (95% and Bonferroni 0.05/5 intervals); fold AUC
                        against the clock with Benjamini-Hochberg over 5 (Table IV)
  T_asev_paired.csv     A_sev minus the clock, pair and equal weights, 4,000 group bootstrap resamples (Table V)
  T_asev_by_group.csv   A_sev per detector and group (Table S6)
  T_time_only.csv       negative control: RF and GB fitted on elapsed time alone, against the clock
  T_leakage_loro.csv    RF under leave one recording out, unsmoothed and pooled (leakage figure)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from csp.inference import *       # noqa: F401,F403
if __name__ == "__main__":
    prim = load("primary"); prim["hard"] = np.nan; ck_ = load("primary_clock"); ck_["hard"] = np.nan
    PFs = fold_mcc(prim); PFc = fold_mcc(ck_); ck = PFc["Clock"]; J = len(ck)
    F = {m: PFs[m].loc[ck.index] for m in SUP}
    sizes = d.groupby("participant").size(); ntot = len(d)
    rho = np.mean([sizes[g] / (ntot - sizes[g]) for g in ck.index])
    mult = (sps.t.ppf(0.975, J - 1) + sps.t.ppf(0.80, J - 1)) / np.sqrt(J)
    rows = []
    for m, x in F.items():
        dl = x - ck; sd = dl.std(ddof=1); t_nb = dl.mean() / np.sqrt((1 / J + rho) * sd ** 2)
        rows.append(dict(model=m, mcc=x.mean(), dmcc=dl.mean(), sd_diff=sd, p_t=sps.ttest_rel(x, ck).pvalue,
                         p_nb=2 * sps.t.sf(abs(t_nb), J - 1), p_w=sps.wilcoxon(x, ck).pvalue,
                         higher=int((dl > 1e-12).sum()), lower=int((dl < -1e-12).sum()), mde=mult * sd,
                         n010=n_needed(sd, 0.10), n015=n_needed(sd, 0.15), n020=n_needed(sd, 0.20)))
    T = pd.DataFrame(rows); T["p_bh5"] = bh(T.p_w); T["rho"] = rho; T["clock_mcc"] = ck.mean()

    # fold AUC against the clock (smoothed score), Benjamini-Hochberg over five
    FA = fold_auc(pd.concat([prim, ck_], ignore_index=True))
    fa = []
    for m in SUP:
        d_ = FA[m] - FA["Clock"]
        fa.append(dict(model=m, fold_auc=FA[m].mean(), fold_auc_ci=ci95(list(FA[m].values))[1], dauc=d_.mean(),
                       auc_p_t=sps.ttest_rel(FA[m], FA["Clock"]).pvalue,
                       auc_p_w=sps.wilcoxon(FA[m], FA["Clock"], zero_method="zsplit").pvalue,
                       auc_higher=int((d_ > 1e-12).sum()), auc_lower=int((d_ < -1e-12).sum())))
    FAT = pd.DataFrame(fa); FAT["auc_p_bh5"] = bh(FAT.auc_p_w); T = T.merge(FAT, on="model")

    # time matched AUC, closed form bootstrap shared by all detectors
    clk = ck_.reset_index(drop=True); AT = ATime(clk.y.values, clk.t.values, clk.participant.values)
    SC = aligned_scores(prim, clk); Cref = AT.tables(clk.t.values.astype(float))
    M = boot_multiplicities(AT.ug, 1000, 0); ones = np.ones(len(AT.ug))
    ref = AT.value(Cref, ones); ref_b = np.array([AT.value(Cref, m_) for m_ in M])
    a2 = 0.05 / K5 / 2; tm = []
    for m in SUP:
        C = AT.tables(SC[m]); e = AT.value(C, ones); eb = np.array([AT.value(C, m_) for m_ in M]); dd = eb - ref_b
        tm.append(dict(model=m, tm_auc=e, tm_lo=np.percentile(eb, 2.5), tm_hi=np.percentile(eb, 97.5),
                       tm_diff=e - ref, tm_dlo=np.percentile(dd, 2.5), tm_dhi=np.percentile(dd, 97.5),
                       tm_dlo_bonf=np.percentile(dd, 100 * a2), tm_dhi_bonf=np.percentile(dd, 100 * (1 - a2))))
    T = T.merge(pd.DataFrame(tm), on="model"); T["tm_ref"] = ref
    T["tm_ref_lo"], T["tm_ref_hi"] = np.percentile(ref_b, 2.5), np.percentile(ref_b, 97.5)
    # the closed form must reproduce the resampling estimator csp.metrics.time_matched_auc (same 1,000 draws, seed 0),
    # whose values step 20 wrote to T_primary.csv (estimate) and T_paired_vs_clock.csv (difference with elapsed time)
    PR = pd.read_csv(TABLES / "T_primary.csv").set_index("model"); PV = pd.read_csv(TABLES / "T_paired_vs_clock.csv").set_index("model")
    for m in SUP:
        r = T.set_index("model").loc[m]
        assert abs(r.tm_auc - PR.loc[m, "tm_auc"]) < 1e-9 and abs(r.tm_lo - PR.loc[m, "tm_lo"]) < 1e-9 \
            and abs(r.tm_hi - PR.loc[m, "tm_hi"]) < 1e-9, (m, r.tm_auc, PR.loc[m, "tm_auc"])
        assert abs(r.tm_diff - PV.loc[m, "tm_diff"]) < 1e-9 and abs(r.tm_dlo - PV.loc[m, "tm_dlo"]) < 1e-9 \
            and abs(r.tm_dhi - PV.loc[m, "tm_dhi"]) < 1e-9, (m, r.tm_dlo, PV.loc[m, "tm_dlo"])
        assert abs(r.mcc - PR.loc[m, "mcc"]) < 1e-12 and abs(r.p_t - PV.loc[m, "p_t"]) < 1e-12
    assert abs(ref - PR.loc["Clock", "tm_auc"]) < 1e-9
    print("closed form bootstrap reproduces the resampling estimator to within 1e-9")
    T.to_csv(TABLES / "T_primary_stats.csv", index=False)
    print(T[["model", "mcc", "dmcc", "p_t", "p_nb", "p_w", "p_bh5", "mde", "n010", "n015", "n020", "dauc", "auc_p_w",
             "auc_p_bh5", "tm_auc", "tm_diff", "tm_dlo", "tm_dhi", "tm_dlo_bonf", "tm_dhi_bonf"]].round(3).to_string())
    print("clock", round(ck.mean(), 3), "elapsed time A_time", round(ref, 3))

    # ------------------------------------------------------------ A_sev: paired with the clock
    ALLp = pd.concat([prim, ck_], ignore_index=True); per = {}
    for name, g in ALLp.groupby("model", sort=False):
        g = g.reset_index(drop=True); s = trailing(g.proba.values, g.session.values, W); pg = {}
        for grp, idx in g.groupby("participant").groups.items():
            s3 = s[idx][g.sev.values[idx] == 3]; s1 = s[idx][g.sev.values[idx] == 1]
            if len(s3) and len(s1):
                dd = s3[:, None] - s1[None, :]; pg[grp] = ((dd > 0).sum() + 0.5 * (dd == 0).sum(), dd.size)
        per[name] = pg
    groups6 = sorted(per["Clock"]); assert len(groups6) == 6 and all(sorted(per[m]) == groups6 for m in SUP)
    NUMS = {m: np.array([per[m][k][0] for k in groups6]) for m in per}; DEN = np.array([per["Clock"][k][1] for k in groups6])
    rng = np.random.default_rng(0); MB = np.array([np.bincount(rng.integers(0, 6, 6), minlength=6) for _ in range(4000)])

    def pooled(m, w): return (w * NUMS[m]).sum(-1) / (w * DEN).sum(-1)

    def equal(m, w): return (w * (NUMS[m] / DEN)).sum(-1) / w.sum(-1)
    rows = []; byg = []
    for m in SUP + ["Clock"]:
        for k, g_ in enumerate(groups6):
            byg.append(dict(model=m, group=g_, a_sev=NUMS[m][k] / DEN[k], pairs=int(DEN[k])))
    for m in SUP:
        dp = pooled(m, np.ones(6)) - pooled("Clock", np.ones(6)); de = equal(m, np.ones(6)) - equal("Clock", np.ones(6))
        bp = pooled(m, MB) - pooled("Clock", MB); be = equal(m, MB) - equal("Clock", MB)
        wins = int((NUMS[m] / DEN > NUMS["Clock"] / DEN + 1e-12).sum())
        jk = [pooled(m, np.eye(6)[i] * 0 + (1 - np.eye(6)[i])) - pooled("Clock", 1 - np.eye(6)[i]) for i in range(6)]
        rows.append(dict(model=m, a_sev=pooled(m, np.ones(6)), a_sev_clock=pooled("Clock", np.ones(6)), d_pooled=dp,
                         d_lo=np.percentile(bp, 2.5), d_hi=np.percentile(bp, 97.5), a_sev_equal=equal(m, np.ones(6)),
                         a_sev_equal_clock=equal("Clock", np.ones(6)), d_equal=de, de_lo=np.percentile(be, 2.5),
                         de_hi=np.percentile(be, 97.5), groups_above_clock=wins, groups=6,
                         d_jk_min=min(jk), d_jk_max=max(jk), largest_group_share=DEN.max() / DEN.sum()))
    AS = pd.DataFrame(rows)
    # where the pooled difference comes from: the group in which the clock ranks worst, and the group with most pairs
    gi_low = int(np.argmin(NUMS["Clock"] / DEN)); gi_big = int(np.argmax(DEN)); keep = np.ones(6); keep[gi_low] = 0
    AS["group_clock_low"] = groups6[gi_low]; AS["group_most_pairs"] = groups6[gi_big]
    AS["d_pooled_without_low"] = [pooled(m, keep) - pooled("Clock", keep) for m in SUP]
    AS["clock_beats_in_most_pairs_group"] = [bool(NUMS["Clock"][gi_big] > NUMS[m][gi_big]) for m in SUP]
    AS["share_resamples_without_low"] = float((MB[:, gi_low] == 0).mean())
    AS["p_boot_two_sided"] = [min(1.0, 2 * min(((pooled(m, MB) - pooled("Clock", MB)) <= 0).mean(),
                                               ((pooled(m, MB) - pooled("Clock", MB)) >= 0).mean())) for m in SUP]
    AS.to_csv(TABLES / "T_asev_paired.csv", index=False)
    pd.DataFrame(byg).to_csv(TABLES / "T_asev_by_group.csv", index=False)
    print(AS.round(3).to_string())
    print(pd.DataFrame(byg).pivot(index="group", columns="model", values="a_sev").round(3).to_string())

    # ------------------------------------------------------------ negative control: time only detectors
    tonly = load("ablation_time"); tonly["hard"] = np.nan; PFt = fold_mcc(tonly); SCt = aligned_scores(tonly, clk)
    nrow = []
    for m in ["RF", "GB"]:
        x = PFt[m].loc[ck.index]; dl = x - ck; C = AT.tables(SCt[m]); e = AT.value(C, ones)
        dd = np.array([AT.value(C, m_) for m_ in M]) - ref_b
        FAt = fold_auc(tonly)[m].loc[FA.index]; da = FAt - FA["Clock"]
        nrow.append(dict(model=f"{m} (elapsed time only)", mcc=x.mean(), dmcc=dl.mean(), p_t=sps.ttest_rel(x, ck).pvalue,
                         p_w=sps.wilcoxon(x, ck).pvalue if (dl.abs() > 1e-12).any() else 1.0,
                         fold_auc=FAt.mean(), dauc=da.mean(), tm_auc=e, tm_diff=e - ref,
                         tm_dlo=np.percentile(dd, 2.5), tm_dhi=np.percentile(dd, 97.5)))
    NT = pd.DataFrame(nrow); NT.to_csv(TABLES / "T_time_only.csv", index=False); print(NT.round(3).to_string())

    # ------------------------------------------------------------ leakage demonstration: recording holdout, unsmoothed
    from sklearn.metrics import matthews_corrcoef, accuracy_score
    lo = load("loro"); r_ = lo[lo.model == "RF"]; hard = (r_.proba.values >= 0.5).astype(int)
    pd.DataFrame([dict(model="RF", split="leave one recording out, 76 features", acc=accuracy_score(r_.y, hard),
                       mcc=matthews_corrcoef(r_.y, hard), auc=roc_auc_score(r_.y, r_.proba))]) \
        .to_csv(TABLES / "T_leakage_loro.csv", index=False)
