"""Step 21. Paired fold AUC with the clock, the circularly shifted alarm reference for episode recall (500 shifts),
the jackknife range of A_sev and severity 3 misses per group (with and without the six recording group). From saved
predictions. Outputs: T_foldauc_paired_vs_clock.csv, T_episode_random_reference.csv, T_asev_jackknife.csv,
T_s3_by_group.csv, T_s3_without_big_group.csv."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from csp.metrics_extra import *    # noqa: F401,F403
if __name__ == "__main__":
    prim = pd.concat([load("primary"), load("primary_clock")], ignore_index=True); prim["hard"] = np.nan
    FA = fold_auc(prim); out = []
    for m in ORDER[:-1]:
        d_ = FA[m] - FA["Clock"]
        out.append(dict(model=m, fold_auc=FA[m].mean(), diff=d_.mean(), p_t=sps.ttest_rel(FA[m], FA["Clock"]).pvalue,
                        p_w=sps.wilcoxon(FA[m], FA["Clock"], zero_method="zsplit").pvalue,
                        higher=int((d_ > 1e-12).sum()), ties=int((d_.abs() <= 1e-12).sum()), lower=int((d_ < -1e-12).sum())))
    T = pd.DataFrame(out); T.to_csv(TABLES / "T_foldauc_paired_vs_clock.csv", index=False); print(T.round(3).to_string())
    R = pd.concat([random_reference(prim), random_reference(prim, 0.44)]); R.to_csv(TABLES / "T_episode_random_reference.csv", index=False)
    print(R.round(3).to_string())
    J = a_sev_jackknife(prim); J.to_csv(TABLES / "T_asev_jackknife.csv", index=False); print(J.round(3).to_string())
    G = s3_by_group(prim); G.to_csv(TABLES / "T_s3_by_group.csv", index=False)
    big = G.groupby("group").recordings.max().idxmax()
    tot = G.groupby(["model", "rule"]).apply(lambda x: pd.Series(dict(
        all=x.missed_s3.sum(), without_big=x[x.group != big].missed_s3.sum(), n_without=x[x.group != big].n_s3.sum())))
    tot.to_csv(TABLES / "T_s3_without_big_group.csv"); print("largest group", big); print(tot.to_string())
