"""Evaluation library: the primary decision rule, threshold dependent and threshold free metrics, severity, episode and
deployment quantities. Everything here works on saved predictions; no model is fitted.

Primary rule: trailing mean of the score within the recording, w = 61, tau = 0.5.
Time matched AUC: pair weighted mean of AUCs within 30 s bins of elapsed time that contain at least 20 positive and 20
negative windows; group bootstrap over the 22 participant groups (resampling version; the closed form used for the
reported intervals is csp.inference.ATime, which reproduces this estimator exactly)."""
import numpy as np, pandas as pd
from scipy import stats as sps
from sklearn.metrics import roc_auc_score, matthews_corrcoef, accuracy_score

from csp.paths import RAW, PRED, TABLES
from csp.data import load_and_group, counts, rates, ci95

W, TAU, BIN = 61, 0.5, 30          # primary smoothing window, threshold, time bin (s)
d = load_and_group(str(RAW / "dataset.csv"))
NEVER = set(d.groupby("participant").y.sum().pipe(lambda s: s[s == 0].index))
d["idx"] = d.groupby("participant").cumcount()


def trailing(v, sess, w):
    if w == 1:
        return np.asarray(v, float)
    return pd.Series(np.asarray(v, float)).groupby(np.asarray(sess)).transform(
        lambda x: x.rolling(w, min_periods=1).mean()).values


def r3(x): return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 3)


# ------------------------------------------------------------------ data loading
def load(tag):
    return pd.read_csv(PRED / f"P_{tag}.csv")


def original_representation():
    """The five supervised detectors of the initial 99 feature analysis, from saved predictions (P_initial99.csv)."""
    sup = pd.read_csv(PRED / "P_initial99.csv")
    sup["idx"] = sup.groupby(["model", "participant"]).cumcount()
    sup = sup.merge(d[["participant", "idx", "session", "TimeStamp", "DiscomfortLevel"]],
                    on=["participant", "idx"], suffixes=("", "_d"))
    assert (sup.session == sup.session_d).all()
    sup = sup.rename(columns={"TimeStamp": "t", "DiscomfortLevel": "sev"})
    sup["hard"] = np.nan
    names = {"Random forest": "RF", "Gradient boosting": "GB", "RF + GB ensemble": "RF+GB",
             "Logistic regression": "LR", "Multilayer perceptron": "MLP"}
    cols_ = ["model", "participant", "idx", "session", "y", "sev", "t", "proba", "hard"]
    A = sup[cols_].copy()
    A["model"] = A.model.map(names); A["fold"] = A.participant
    A["_o"] = A.model.map({m: i for i, m in enumerate(names.values())})
    return A.sort_values(["_o", "participant", "idx"]).drop(columns="_o").reset_index(drop=True)


# ------------------------------------------------------------------ metrics
def decisions(g, w=W, tau=TAU):
    """Primary rule: threshold the trailing mean of the score. (Rows with a hard decision column instead of a score
    would vote over hard decisions; no detector of this paper has one.)"""
    if g.hard.notna().all() if "hard" in g else False:
        return (trailing(g.hard.values, g.session.values, w) >= tau).astype(int)
    return (trailing(g.proba.values, g.session.values, w) >= tau).astype(int)


def time_matched_auc(y, s, t, groups, B=1000, seed=0, other=None):
    """Pair weighted mean of AUCs within 30 s bins of elapsed time (bins with >= 20 positives and negatives).
    Returns estimate, group bootstrap 95% interval and, if other (score of a second detector) is given,
    the bootstrap interval of the difference."""
    b = (t // BIN).astype(int)

    def est(idx, sc):
        num = den = 0.0
        yy, ss, bb = y[idx], sc[idx], b[idx]
        for k in np.unique(bb):
            m = bb == k; yk = yy[m]; npos = yk.sum(); nneg = len(yk) - npos
            if npos >= 20 and nneg >= 20:
                wgt = float(npos) * nneg; num += roc_auc_score(yk, ss[m]) * wgt; den += wgt
        return num / den if den else np.nan
    allidx = np.arange(len(y)); e = est(allidx, s)
    ug = np.unique(groups); pos = {g_: np.where(groups == g_)[0] for g_ in ug}
    rng = np.random.default_rng(seed); bs, bd = [], []
    for _ in range(B):
        idx = np.concatenate([pos[g_] for g_ in rng.choice(ug, len(ug))])
        a = est(idx, s); bs.append(a)
        if other is not None: bd.append(a - est(idx, other))
    out = dict(est=e, lo=np.nanpercentile(bs, 2.5), hi=np.nanpercentile(bs, 97.5))
    if other is not None:
        out.update(diff=e - est(allidx, other), dlo=np.nanpercentile(bd, 2.5), dhi=np.nanpercentile(bd, 97.5))
    return out


def summarise(P, unit="fold", tm=True):
    rows, per_fold = [], {}
    for name, g in P.groupby("model", sort=False):
        g = g.reset_index(drop=True)
        pred = decisions(g); s = trailing(g.proba.values, g.session.values, W)
        per = {k: [] for k in ("mcc", "rec", "spec", "bal_acc", "acc", "alarm")}
        fa, auc, auc1, fm = [], [], 0, {}
        for u, idx in g.groupby(unit).groups.items():
            yy, pp = g.y.values[idx], pred[idx]
            if (yy == 0).any(): fa.append(pp[yy == 0].mean())
            if 0 < yy.sum() < len(yy):
                r = rates(*counts(yy, pp))
                for k in ("mcc", "rec", "spec", "bal_acc", "acc"): per[k].append(r[k])
                per["alarm"].append(pp.mean()); fm[u] = r["mcc"]
                a = roc_auc_score(yy, s[idx]); auc.append(a); auc1 += a > 0.99999
        per_fold[name] = pd.Series(fm)
        row = dict(model=name)
        for k, v in per.items():
            mu, h, n = ci95(v); row[k] = mu; row[k + "_ci"] = h
        row["n_two_class"] = n
        TP, TN, FP, FN = counts(g.y.values, pred); pr = rates(TP, TN, FP, FN)
        row.update(pooled_mcc=pr["mcc"], pooled_rec=pr["rec"], pooled_spec=pr["spec"], pooled_alarm=pred.mean(),
                   TP=TP, FN=FN, FP=FP, TN=TN)
        mu, h, n = ci95(fa); row.update(fa_all=mu, fa_all_ci=h, fa_units=n)
        nv = g.participant.isin(NEVER).values
        row["never_sick_alarm"] = pred[nv].mean()
        pg = pd.Series(pred[nv]).groupby(g.participant.values[nv]).mean()
        row["never_min"], row["never_max"], row["never_above_06"] = pg.min(), pg.max(), int((pg > 0.6).sum())
        for sv in (1, 2, 3): row[f"missed_s{sv}"] = int(((g.sev.values == sv) & (pred == 0)).sum())
        mu, h, n = ci95(auc); row.update(fold_auc=mu, fold_auc_ci=h, folds_auc1=int(auc1))
        on = sum(int(p_.values[0] == 1) + int(np.sum(np.diff(p_.values) == 1))
                 for _, p_ in pd.Series(pred).groupby(g.session.values))
        row["onsets_per_session"] = on / g.session.nunique(); row["onsets_per_hour"] = on / (len(g) / 3600)
        if tm:
            # the clock is monotone in elapsed time within each fold; across folds its fitted intercepts differ, so
            # pooling its probabilities would rank groups by fold specific offsets. Its time matched AUC therefore
            # uses elapsed time itself, the same score in every fold (identical ranking within each fold).
            s_tm = g.t.values.astype(float) if name == "Clock" else s
            r_ = time_matched_auc(g.y.values, s_tm, g.t.values, g.participant.values)
            row.update(tm_auc=r_["est"], tm_lo=r_["lo"], tm_hi=r_["hi"])
        rows.append(row)
    return pd.DataFrame(rows), per_fold


def paired(per_fold, ref, order):
    out = []; F = pd.DataFrame(per_fold)
    for m in order:
        if m == ref: continue
        dlt = (F[m] - F[ref]).dropna()
        out.append(dict(model=m, dmcc=dlt.mean(), p_t=sps.ttest_rel(F[m], F[ref]).pvalue,
                        p_w=sps.wilcoxon(F[m], F[ref]).pvalue, higher=int((dlt > 1e-12).sum()),
                        ties=int((dlt.abs() <= 1e-12).sum()), lower=int((dlt < -1e-12).sum()), n=len(dlt)))
    T = pd.DataFrame(out)
    pw = T.p_w.values; k = len(pw); o = np.argsort(pw); adj = np.empty(k); prev = 1.0
    for i in range(k - 1, -1, -1):
        prev = min(prev, pw[o[i]] * k / (i + 1)); adj[o[i]] = prev
    T["p_bh"] = adj
    sds = [np.std(F[a] - F[b], ddof=1) for i, a in enumerate(F.columns) for b in F.columns[i + 1:]]
    n = len(F); mult = sps.t.ppf(0.975, n - 1) + sps.t.ppf(0.80, n - 1)
    return T, dict(mde_median=mult * np.median(sds) / np.sqrt(n),
                   mde_min=mult * min(sds) / np.sqrt(n), mde_max=mult * max(sds) / np.sqrt(n))


def a_sev(P, B=4000, seed=0):
    out = []
    for name, g in P.groupby("model", sort=False):
        g = g.reset_index(drop=True); s = trailing(g.proba.values, g.session.values, W)
        per = {}
        for grp, idx in g.groupby("participant").groups.items():
            s3 = s[idx][g.sev.values[idx] == 3]; s1 = s[idx][g.sev.values[idx] == 1]
            if len(s3) and len(s1):
                diff = s3[:, None] - s1[None, :]
                per[grp] = ((diff > 0).sum() + 0.5 * (diff == 0).sum(), diff.size)
        ks = list(per); num = sum(per[k][0] for k in ks); den = sum(per[k][1] for k in ks)
        rng = np.random.default_rng(seed); bs = []
        for _ in range(B):
            pick = rng.choice(ks, len(ks)); bs.append(sum(per[k][0] for k in pick) / sum(per[k][1] for k in pick))
        out.append(dict(model=name, a_sev=num / den, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5),
                        pairs=int(den), groups=len(ks)))
    return pd.DataFrame(out)


def matched_alarm(P, target):
    """Label free: threshold on the pooled smoothed score so that the pooled alarm rate equals target."""
    rows = []
    for name, g in P.groupby("model", sort=False):
        g = g.reset_index(drop=True); s = trailing(g.proba.values, g.session.values, W)
        thr = np.quantile(s, 1 - target); pred = (s >= thr).astype(int)
        TP, TN, FP, FN = counts(g.y.values, pred); r = rates(TP, TN, FP, FN)
        rows.append(dict(model=name, target=target, alarm=pred.mean(), rec=r["rec"], spec=r["spec"],
                         mcc=r["mcc"], **{f"missed_s{v}": int(((g.sev.values == v) & (pred == 0)).sum())
                                          for v in (1, 2, 3)}))
    return pd.DataFrame(rows)


def episodes(P, target=None):
    rows = []
    for name, g in P.groupby("model", sort=False):
        g = g.reset_index(drop=True)
        if target is None: pred = decisions(g)
        else:
            s = trailing(g.proba.values, g.session.values, W); pred = (s >= np.quantile(s, 1 - target)).astype(int)
        det, lat, pre, n_pre, E = 0, [], 0, 0, 0
        for _, idx in g.groupby("session").groups.items():
            idx = np.asarray(idx); yy, pp, tt = g.y.values[idx], pred[idx], g.t.values[idx]
            i = 0
            while i < len(yy):
                if yy[i] == 1:
                    j = i
                    while j + 1 < len(yy) and yy[j + 1] == 1: j += 1
                    E += 1
                    if i > 0:
                        n_pre += 1; pre += int(pp[i - 1] == 1)
                    hit = np.where(pp[i:j + 1] == 1)[0]
                    if len(hit): det += 1; lat.append(tt[i + hit[0]] - tt[i])
                    i = j + 1
                else: i += 1
        rows.append(dict(model=name, alarm=pred.mean(), episodes=E, detected=det, ep_recall=det / E,
                         latency_median=np.median(lat) if lat else np.nan, pre_onset_share=pre / n_pre,
                         pre_onset_n=n_pre))
    return pd.DataFrame(rows)


def deploy(S, pis=(0.44, 0.10, 0.01)):
    rows = []
    for _, r in S.iterrows():
        for pi in pis:
            ppv = r.pooled_rec * pi / (r.pooled_rec * pi + (1 - r.pooled_spec) * (1 - pi))
            npv = r.pooled_spec * (1 - pi) / (r.pooled_spec * (1 - pi) + (1 - r.pooled_rec) * pi)
            rows.append(dict(model=r.model, pi=pi, ppv=ppv, npv=npv, fa_per_1000=1000 * (1 - r.pooled_spec) * (1 - pi)))
    return pd.DataFrame(rows)


def window_level(P):
    rows = []
    for name, g in P.groupby("model", sort=False):
        hard = (g.proba.values >= 0.5).astype(int)
        rows.append(dict(model=name, acc=accuracy_score(g.y, hard), mcc=matthews_corrcoef(g.y, hard),
                         auc=roc_auc_score(g.y, g.proba)))
    return pd.DataFrame(rows)


def save(df, name):
    df.to_csv(TABLES / f"{name}.csv", index=False)
    return df

