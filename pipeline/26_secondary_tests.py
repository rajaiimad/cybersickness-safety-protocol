"""Step 26. One table of every secondary hypothesis test, with a Benjamini-Hochberg false discovery rate adjustment
across the whole set (Supporting Information Table S1). Every test was already run by an earlier step or is recomputed
from saved predictions; nothing is fitted.

Families: fold AUC against the clock; fold MCC against the clock at the five non primary smoothing windows, with the
window chosen on validation groups, at seeds 1 and 2 (RF, RF+GB, MLP; GB is identical across seeds), with the 99
feature representation, under LORO and under the merged grouping; episode recall against the circularly shifted alarm
reference (one sided; the clock is included as a sixth row); within group severity ranking A_sev minus the clock
(group bootstrap, two sided, approximate with six groups). 73 tests in total.
Output: outputs/tables/T_secondary_tests.csv"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from csp.inference import *       # noqa: F401,F403


def paired_mcc(P, Pc, label):
    _, PF = summarise(P, tm=False); _, PFc = summarise(Pc, tm=False); ck = PFc["Clock"]; rows = []
    for m in SUP:
        x = PF[m].loc[ck.index]; dl = x - ck
        rows.append(dict(family=label, model=m, contrast="fold MCC minus clock", estimate=dl.mean(),
                         p=sps.wilcoxon(x, ck).pvalue, p_t=sps.ttest_rel(x, ck).pvalue, n=len(ck), test="Wilcoxon"))
    return rows


if __name__ == "__main__":
    R = []
    T8 = pd.read_csv(TABLES / "T_primary_stats.csv").set_index("model")
    for m in SUP:
        R.append(dict(family="Fold AUC (smoothed score)", model=m, contrast="fold AUC minus clock",
                      estimate=T8.loc[m, "dauc"], p=T8.loc[m, "auc_p_w"], p_t=T8.loc[m, "auc_p_t"], n=16, test="Wilcoxon"))
    SWP = pd.read_csv(TABLES / "T_smoothing_paired_vs_clock.csv")
    for _, r in SWP[SWP.w != W].iterrows():
        R.append(dict(family=f"Smoothing window w = {int(r.w)}", model=r.model, contrast="fold MCC minus clock",
                      estimate=r["diff"], p=r.pw, p_t=r.p, n=16, test="Wilcoxon"))
    NW = pd.read_csv(TABLES / "T_nested_w.csv").set_index("model")
    for m in SUP:
        R.append(dict(family="w chosen on validation groups", model=m, contrast="fold MCC minus clock",
                      estimate=NW.loc[m, "dmcc"], p=NW.loc[m, "p_w"], p_t=NW.loc[m, "p_t"], n=16, test="Wilcoxon"))
    SS = pd.read_csv(TABLES / "T_sup_seeds.csv")
    for _, r in SS[(SS.seed != 42) & SS.model.isin(["RF", "RF+GB", "MLP"])].iterrows():
        R.append(dict(family=f"Training seed {int(r.seed)}", model=r.model, contrast="fold MCC minus clock",
                      estimate=r.dmcc, p=r.p_w, p_t=r.p_t, n=16, test="Wilcoxon"))
    # 99 features: RF, GB, RF+GB and LR of the initial analysis; the MLP refitted with group based early stopping
    # (Appendix B), because the initial MLP stopped on a random 10% of windows
    o99 = original_representation(); o99 = o99[o99.model.isin(["RF", "GB", "RF+GB", "LR"])]
    f99 = load("full99"); f99["hard"] = np.nan
    o99 = pd.concat([o99, f99[["model", "participant", "fold", "session", "y", "sev", "t", "proba", "hard"]]],
                    ignore_index=True)
    R += paired_mcc(o99, load("primary_clock").assign(hard=np.nan), "99 features (descriptors included)")
    R += paired_mcc(load("loro").assign(hard=np.nan), load("loro_clock").assign(hard=np.nan), "Leave one recording out")
    R += paired_mcc(load("merged").assign(hard=np.nan), load("merged_clock").assign(hard=np.nan), "Merged grouping (20 groups)")
    ER = pd.read_csv(TABLES / "T_episode_random_reference.csv")
    for _, r in ER.iterrows():
        R.append(dict(family="Episode recall, " + ("primary rule" if pd.isna(r.target) else "matched alarm rate 0.44"),
                      model=r.model, contrast="observed minus shifted alarms", estimate=r.ep_recall - r.random_mean,
                      p=r.p_above, p_t=np.nan, n=31, test="circular shift, one sided"))
    # A_sev minus clock: two sided bootstrap p from the same 4,000 resamples as T_asev_paired
    per = pd.read_csv(TABLES / "T_asev_by_group.csv")
    pv = per.pivot(index="group", columns="model", values="a_sev"); pairs = per.pivot(index="group", columns="model", values="pairs")
    rng = np.random.default_rng(0); MBs = np.array([np.bincount(rng.integers(0, 6, 6), minlength=6) for _ in range(4000)])
    den = pairs["Clock"].values
    for m in SUP:
        num_m, num_c = pv[m].values * den, pv["Clock"].values * den
        b = (MBs @ num_m) / (MBs @ den) - (MBs @ num_c) / (MBs @ den)
        est = num_m.sum() / den.sum() - num_c.sum() / den.sum()
        R.append(dict(family="Within group severity ranking", model=m, contrast="severity ranking minus clock",
                      estimate=est, p=min(1.0, 2 * min((b <= 0).mean(), (b >= 0).mean())), p_t=np.nan, n=6,
                      test="group bootstrap, two sided"))
    T = pd.DataFrame(R); T["p_bh_all"] = bh(T.p.values)
    T.to_csv(TABLES / "T_secondary_tests.csv", index=False)
    print(len(T), "tests;", int((T.p < 0.05).sum()), "unadjusted p < 0.05;", int((T.p_bh_all < 0.05).sum()), "after BH")
    print(T[T.p < 0.05].round(3).to_string())
    print(T.groupby("family").size().to_string())
