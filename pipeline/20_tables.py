"""Step 20. Every metric of the primary comparison and of the sensitivity designs, from saved predictions (no model
is fitted). About 10 minutes.

Outputs (outputs/tables/):
  T_primary.csv                     Table III (fold mean and pooled metrics, false alarms, fold AUC, pooled A_time)
  T_paired_vs_clock.csv             paired fold MCC tests and resampling A_time intervals (used as a check in step 24)
  T_smoothing.csv, T_smoothing_paired_vs_clock.csv   smoothing window sweep (temporal figure, Table S1)
  T_severity.csv                    Table V (primary rule, matched alarm rate 0.44, A_sev)
  CURVE_s3_vs_alarm.csv             severity figure, panel a
  T_episodes.csv, T_deploy.csv      Tables S5 and S3
  T_original99.csv                  99 feature rows of Table S2
  T_loro.csv, T_merged.csv, T_full99_mlp.csv, T_ablation.csv   sensitivity designs, Table S2, temporal figure b
  T_leakage.csv                     leakage demonstration (random 5 fold against LOGO, unsmoothed, pooled)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from csp.metrics import *          # noqa: F401,F403
if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)
    ORDER = ["RF", "GB", "RF+GB", "LR", "MLP", "Clock"]
    prim = pd.concat([load("primary"), load("primary_clock")], ignore_index=True)
    prim["hard"] = np.nan
    S, PF = summarise(prim); S = S.set_index("model").loc[ORDER].reset_index(); save(S, "T_primary")
    T, mde = paired(PF, "Clock", ORDER)
    clock = prim[prim.model == "Clock"].reset_index(drop=True)
    sc = clock.t.values.astype(float)   # reference for time matched differences: elapsed time itself
    dif = []
    for m in ORDER[:-1]:
        g = prim[prim.model == m].reset_index(drop=True)
        assert (g.y.values == clock.y.values).all()
        s = trailing(g.proba.values, g.session.values, W)
        r_ = time_matched_auc(g.y.values, s, g.t.values, g.participant.values, other=sc)
        dif.append(dict(model=m, tm_diff=r_["diff"], tm_dlo=r_["dlo"], tm_dhi=r_["dhi"]))
    T = T.merge(pd.DataFrame(dif), on="model"); save(T, "T_paired_vs_clock")
    print(S.round(3).to_string()); print(T.round(3).to_string()); print(mde)
    # smoothing sweep
    sw = []
    for w in (1, 15, 31, 61, 121, 201):
        for name, g in prim.groupby("model", sort=False):
            g = g.reset_index(drop=True); pred = (trailing(g.proba.values, g.session.values, w) >= TAU).astype(int)
            v = [rates(*counts(g.y.values[i], pred[i]))["mcc"] for _, i in g.groupby("fold").groups.items()
                 if 0 < g.y.values[i].sum() < len(i)]
            sw.append(dict(w=w, model=name, mcc=np.mean(v)))
    save(pd.DataFrame(sw), "T_smoothing")
    # paired comparison with the clock at every smoothing window (does the conclusion depend on w?)
    swp = []
    for w in (1, 15, 31, 61, 121, 201):
        F = {}
        for name, g in prim.groupby("model", sort=False):
            g = g.reset_index(drop=True); pred = (trailing(g.proba.values, g.session.values, w) >= TAU).astype(int)
            F[name] = pd.Series({f: rates(*counts(g.y.values[i], pred[i]))["mcc"] for f, i in g.groupby("fold").groups.items()
                                 if 0 < g.y.values[i].sum() < len(i)})
        for m in ORDER[:-1]:
            swp.append(dict(w=w, model=m, diff=(F[m] - F["Clock"]).mean(), p=sps.ttest_rel(F[m], F["Clock"]).pvalue,
                            pw=sps.wilcoxon(F[m], F["Clock"]).pvalue))
    save(pd.DataFrame(swp), "T_smoothing_paired_vs_clock")
    # severity
    sev = S[["model", "pooled_alarm", "missed_s1", "missed_s2", "missed_s3"]]
    m44 = matched_alarm(prim, 0.44); asv = a_sev(prim)    # 0.44 = label prevalence; the threshold uses no labels
    save(sev.merge(m44, on="model", suffixes=("", "_m44")).merge(asv, on="model"), "T_severity")
    curve = []
    for name, g in prim.groupby("model", sort=False):
        g = g.reset_index(drop=True); s = trailing(g.proba.values, g.session.values, W)
        for a in np.linspace(0.05, 0.95, 91):
            p_ = (s >= np.quantile(s, 1 - a)).astype(int)
            curve.append(dict(model=name, alarm=p_.mean(), missed_s3=int(((g.sev.values == 3) & (p_ == 0)).sum()),
                              rec=p_[g.y.values == 1].mean()))
    save(pd.DataFrame(curve), "CURVE_s3_vs_alarm")
    # episodes
    save(episodes(prim).merge(episodes(prim, 0.44), on="model", suffixes=("", "_m44")), "T_episodes")
    # deployment
    save(deploy(S), "T_deploy")
    # initial representation (99 features, five supervised detectors of the initial analysis)
    O = original_representation(); SO, PFO = summarise(O)
    OO = ["RF", "RF+GB", "GB", "LR", "MLP"]
    SO = SO.set_index("model").loc[OO].reset_index(); save(SO, "T_original99")
    # sensitivity designs
    for tag, unit in [("loro", "fold"), ("merged", "fold")]:
        P_ = pd.concat([load(tag), load(f"{tag}_clock")], ignore_index=True); P_["hard"] = np.nan
        s_, _ = summarise(P_, unit, tm=False); save(s_, f"T_{tag}")
    f99 = load("full99"); f99["hard"] = np.nan; s_, _ = summarise(f99, tm=False); save(s_, "T_full99_mlp")
    ab = []
    for tag in ("ablation_time", "ablation_tel", "ablation_tel_time"):
        A_ = load(tag); A_["hard"] = np.nan; s_, _ = summarise(A_, tm=False); s_["config"] = tag; ab.append(s_)
    save(pd.concat(ab), "T_ablation")
    # leakage demonstration (window level, unsmoothed, pooled)
    lk = []
    for tag, P_ in [("random 5 fold, 76 features", load("leak_random_primary")),
                    ("random 5 fold, 99 features", load("leak_random_full99")),
                    ("group disjoint, 76 features", load("primary").query("model == 'RF'")),
                    ("group disjoint, 99 features", O[O.model == "RF"])]:
        r_ = window_level(P_); r_["split"] = tag; lk.append(r_)
    save(pd.concat(lk), "T_leakage")
    print("tables written to", TABLES)
