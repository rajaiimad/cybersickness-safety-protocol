"""Step 13. Analyses that need predictions on validation groups inside each training fold (about 15 minutes on 2 CPUs).

For each of the 22 LOGO folds the three validation groups are the next three groups in sorted order after the held out
group. Every supervised detector and the clock is refitted on the remaining 18 training groups (scaling fitted on them)
and scores the validation groups. The held out group is never used here; its predictions are the saved LOGO
predictions of step 11 (P_primary.csv, P_primary_clock.csv).

  1. Nested smoothing window (sensitivity): in each fold, w is chosen from {1, 15, 31, 61, 121, 201} by the pooled
     validation MCC at tau = 0.5 (ties: the value closest to 61) and applied to that fold's held out predictions.
     Outputs T_nested_w.csv and T_nested_w_choices.csv.
  2. Prior shift transfer (descriptive): isotonic regression maps the smoothed validation score (w = 61) to a
     calibrated posterior; for a deployment prevalence pi the Bayes adjusted rule alarms when the calibrated posterior
     exceeds c / (1 + c), c = pi0 (1 - pi) / ((1 - pi0) pi), pi0 the validation prevalence. Output T_prior_shift.csv.
Writes outputs/predictions/P_nested_val.csv (validation predictions) so the analysis can be rerun without refitting."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from csp.design import *          # noqa: F401,F403
from scipy import stats as sps
from csp.paths import TABLES
from sklearn.isotonic import IsotonicRegression
from csp.data import counts, rates, ci95

N_VAL = 3; WGRID = [1, 15, 31, 61, 121, 201]; TAU = 0.5
ORDER = ["RF", "GB", "RF+GB", "LR", "MLP", "Clock"]


def trailing(v, s, w):
    if w == 1:
        return np.asarray(v, float)
    return pd.Series(np.asarray(v, float)).groupby(np.asarray(s)).transform(
        lambda x: x.rolling(w, min_periods=1).mean()).values


def mcc_of(yy, pp): return rates(*counts(yy, pp))["mcc"]


def fit_validation():
    f = OUT / "P_nested_val.csv"
    if f.exists():
        return pd.read_csv(f)
    parts = sorted(np.unique(pid).tolist()); Xp = X[PRIMARY].values.astype(float)
    Xt = X[["elapsed_in_session"]].values.astype(float); recs = []; t0 = time.time()
    for i, p_test in enumerate(parts):
        rem = [q for q in parts if q != p_test]
        val_ps = [rem[(i + k) % len(rem)] for k in range(N_VAL)]
        tr = np.where(np.isin(pid, [q for q in rem if q not in val_ps]))[0]; va = np.where(np.isin(pid, val_ps))[0]
        assert not set(pid[tr]) & set(pid[va]) and p_test not in set(pid[tr]) | set(pid[va])
        sc = RobustScaler().fit(Xp[tr]); A, B = sc.transform(Xp[tr]), sc.transform(Xp[va]); probs = {}
        for name, fn in [("RF", rf), ("GB", gb), ("LR", lr)]:
            probs[name] = fn().fit(A, y[tr]).predict_proba(B)[:, 1]
        probs["RF+GB"] = (probs["RF"] + probs["GB"]) / 2
        probs["MLP"] = GroupEarlyStopMLP(pid[tr]).fit(A, y[tr]).predict_proba(B)[:, 1]
        sct = RobustScaler().fit(Xt[tr])
        probs["Clock"] = lr().fit(sct.transform(Xt[tr]), y[tr]).predict_proba(sct.transform(Xt[va]))[:, 1]
        for name in ORDER:
            recs.append(pd.DataFrame(dict(model=name, fold=i, test_group=p_test, participant=pid[va], session=sess[va],
                                          y=y[va], sev=sev[va], t=t_el[va], proba=probs[name])))
        print(f"fold {i} (group {p_test}) validation groups {val_ps}: {time.time() - t0:.0f}s", flush=True)
    V = pd.concat(recs, ignore_index=True); V.to_csv(f, index=False)
    return V


def outer_predictions():
    P = pd.concat([pd.read_csv(OUT / "P_primary.csv"), pd.read_csv(OUT / "P_primary_clock.csv")], ignore_index=True)
    return P


if __name__ == "__main__":
    V = fit_validation(); P = outer_predictions()
    parts = sorted(np.unique(pid).tolist())
    fold_of_group = {p: i for i, p in enumerate(parts)}

    # ---------------- 1. nested smoothing window
    choice, fm = [], {m: {} for m in ORDER}
    for m in ORDER:
        vm = V[V.model == m]; pm_ = P[P.model == m]
        for grp, gt in pm_.groupby("participant"):
            k = fold_of_group[grp]; gv = vm[vm.fold == k]
            vm_mcc = {w: mcc_of(gv.y.values, (trailing(gv.proba.values, gv.session.values, w) >= TAU).astype(int))
                      for w in WGRID}
            wbest = max(WGRID, key=lambda w: (vm_mcc[w], -abs(w - 61)))   # ties: the value closest to 61
            choice.append(dict(model=m, fold=k, group=grp, w=wbest, val_mcc=vm_mcc[wbest]))
            yy = gt.y.values
            if 0 < yy.sum() < len(yy):
                pp = (trailing(gt.proba.values, gt.session.values, wbest) >= TAU).astype(int); fm[m][grp] = mcc_of(yy, pp)
    C = pd.DataFrame(choice); C.to_csv(TABLES / "T_nested_w_choices.csv", index=False)
    F = pd.DataFrame(fm); rows = []
    for m in ORDER:
        mu, h, n = ci95(F[m].values); r = dict(model=m, mcc=mu, mcc_ci=h, n=n,
                                              w_median=C[C.model == m].w.median(),
                                              w_61=int((C[C.model == m].w == 61).sum()))
        if m != "Clock":
            dlt = F[m] - F["Clock"]
            r.update(dmcc=dlt.mean(), p_t=sps.ttest_rel(F[m], F["Clock"]).pvalue,
                     p_w=sps.wilcoxon(F[m], F["Clock"]).pvalue, higher=int((dlt > 1e-12).sum()),
                     lower=int((dlt < -1e-12).sum()))
        rows.append(r)
    T = pd.DataFrame(rows); pw = T.p_w.values[:-1]; k_ = len(pw); o = np.argsort(pw); adj = np.empty(k_); prev = 1.0
    for i in range(k_ - 1, -1, -1):
        prev = min(prev, pw[o[i]] * k_ / (i + 1)); adj[o[i]] = prev
    T.loc[T.model != "Clock", "p_bh"] = adj
    T.to_csv(TABLES / "T_nested_w.csv", index=False); print(T.round(3).to_string())
    print(C.groupby(["model", "w"]).size().unstack(fill_value=0).to_string())

    # ---------------- 2. prior shift transfer after isotonic calibration on the validation groups
    rows = []
    for m in ORDER:
        vm = V[V.model == m]; pm_ = P[P.model == m]
        cal, thr = {}, {pi: [] for pi in (0.44, 0.10, 0.01)}
        post, yy_all, grp_all = [], [], []
        for grp, gt in pm_.groupby("participant"):
            k = fold_of_group[grp]; gv = vm[vm.fold == k]
            sv = trailing(gv.proba.values, gv.session.values, 61); st = trailing(gt.proba.values, gt.session.values, 61)
            iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip").fit(sv, gv.y.values)
            pi0 = gv.y.mean(); q = iso.predict(st); post.append(q); yy_all.append(gt.y.values)
            for pi in thr:
                c = pi0 * (1 - pi) / ((1 - pi0) * pi); thr[pi].append((c / (1 + c), q))
        yy = np.concatenate(yy_all); qq = np.concatenate(post)
        for pi, lst in thr.items():
            ts = np.array([t_ for t_, _ in lst]); pred = np.concatenate([(q_ >= t_).astype(int) for t_, q_ in lst])
            TP, TN, FP, FN = counts(yy, pred); r_ = rates(TP, TN, FP, FN)
            rows.append(dict(model=m, pi=pi, thr_median=np.median(ts), thr_min=ts.min(), thr_max=ts.max(),
                             post_min=qq.min(), post_max=qq.max(), share_at_max=float(np.mean(qq >= qq.max() - 1e-12)),
                             alarm=pred.mean(), rec=r_["rec"], spec=r_["spec"],
                             folds_no_alarm=int(sum((q_ >= t_).sum() == 0 for t_, q_ in lst))))
    S = pd.DataFrame(rows); S.to_csv(TABLES / "T_prior_shift.csv", index=False); print(S.round(3).to_string())
