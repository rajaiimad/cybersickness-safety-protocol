"""Step 16. Positive and negative controls for the evaluation protocol (about 1 hour on 2 CPUs for 200 replicates).

Question: when a detector does carry information beyond elapsed time, do the protocol's tests detect it, and when it
does not, do they stay quiet? The controls use the real labels, recordings, participant groups, elapsed time, LOGO
folds, smoothing rule (w = 61, tau = 0.5) and statistics of the primary analysis. Only one input is synthetic: a
feature z whose relation to the label is set by the experimenter.

  state signal   z_t = delta * y_t + e_t, e_t independent N(0, 1) per window: information about the current state.
  trait signal   z_r = delta * 1[recording r ever reaches severity >= 1] + e_r, e_r N(0, 1) drawn once per recording
                 and constant within it: information about susceptibility, none about onset timing.
delta = 0 gives a detector with no information beyond time (a true null for both signals).

Learner: class balanced logistic regression (the clock's own learner) on [elapsed time, z], robust scaling fitted on
the training groups. For every replicate: fold MCC against the clock over the 16 two class folds (paired t test,
Wilcoxon), fold AUC difference with the clock, and the time matched AUC minus elapsed time from pooled LOGO scores and
from leave pair of groups out scores, each with a 95% group bootstrap interval (closed form, the same 1,000 draws).

Usage: python pipeline/16_controls.py [lr|summary|pilot]
  lr       run the replicates (resumable; REPS replicates per delta, default 200 as reported; the grids can be changed
           with the environment variables STATE and TRAIT) and summarise
  summary  recompute outputs/tables/T_controls.csv from outputs/tables/CTRL_LR.csv
  pilot    one replicate per cell, for a quick check
Outputs: outputs/tables/CTRL_LR.csv (one row per replicate), outputs/tables/T_controls.csv (Table VI, Table S7)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import os, time
import numpy as np, pandas as pd
from scipy import stats as sps
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from csp.inference import *       # noqa: F401,F403

# canonical row order = order of the saved prediction files (groups ascending, dataset order within a group)
PERM = np.concatenate([np.where(d.participant.values == g)[0] for g in np.unique(d.participant.values)])
y_all = d.y.values.astype(int)[PERM]; t_all = d.TimeStamp.values.astype(float)[PERM]; pid = d.participant.values[PERM]
sess = d.session.values[PERM]; SEV = d.DiscomfortLevel.values[PERM]
EVER = pd.Series(y_all).groupby(sess).transform("max").values          # recording ever sick (trait)
REC_IDX = np.searchsorted(np.unique(sess), sess)
FOLDS = [(np.where(pid != g)[0], np.where(pid == g)[0]) for g in np.unique(pid)]
assert all(not set(pid[tr]) & set(pid[te]) for tr, te in FOLDS)


def lr_(): return LogisticRegression(class_weight="balanced", max_iter=1000)


def gb_(): return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                                 l2_regularization=1.0, class_weight="balanced", random_state=42)


LEARNERS = {"LR": lr_, "GB": gb_}


def logo_proba(Xa, make):
    p = np.empty(len(Xa))
    for tr, te in FOLDS:
        sc = RobustScaler().fit(Xa[tr]); m = make().fit(sc.transform(Xa[tr]), y_all[tr])
        p[te] = m.predict_proba(sc.transform(Xa[te]))[:, 1]
    return p


def frame(p, name):
    return pd.DataFrame(dict(model=name, fold=pid, participant=pid, session=sess, y=y_all,
                             sev=SEV, t=t_all, proba=p, hard=np.nan))


# reference objects shared by every replicate (row order of the dataset)
ck_ = load("primary_clock"); ck_["hard"] = np.nan
ORD = frame(np.zeros(len(d)), "order")
CK = aligned_scores(ck_, ORD)["Clock"]
assert np.allclose(pd.concat([ck_[ck_.participant == p] for p in ORD.participant.unique()]).y.values, ORD.y.values)
_, PFc = summarise(ck_, tm=False); CKF = PFc["Clock"]; TWO = CKF.index
FAc = fold_auc(ck_)["Clock"]
AT = ATime(y_all, t_all, pid); ONES = np.ones(len(AT.ug)); MB = boot_multiplicities(AT.ug, 1000, 0)
REF_E = AT.tables(t_all); REF_E_B = np.array([AT.value(REF_E, m_) for m_ in MB]); REF_E0 = AT.value(REF_E, ONES)
import itertools
HASPOS = set(np.unique(pid[y_all == 1]))
PAIRS = [(g, h) for g, h in itertools.combinations(np.unique(pid), 2) if g in HASPOS or h in HASPOS]
PAIR_IDX = {(g, h): (np.where((pid != g) & (pid != h))[0], np.where((pid == g) | (pid == h))[0]) for g, h in PAIRS}
assert all(not {g, h} & set(pid[tr]) for (g, h), (tr, te) in PAIR_IDX.items())


def lpo_scores(Xa, make):
    """Smoothed scores of every pair model on the two held out groups (NaN elsewhere)."""
    out = {}
    for (g, h), (tr, te) in PAIR_IDX.items():
        sc = RobustScaler().fit(Xa[tr]); m = make().fit(sc.transform(Xa[tr]), y_all[tr])
        v = np.full(len(Xa), np.nan); v[te] = trailing(m.predict_proba(sc.transform(Xa[te]))[:, 1], sess[te], W)
        out[(g, h)] = v
    return out


def boot(C):
    return AT.value(C, ONES), np.array([AT.value(C, m_) for m_ in MB])


def evaluate(p, pair_s):
    """All protocol quantities for one detector: LOGO probabilities p (canonical order) and its pair model scores."""
    s = trailing(p, sess, W); pred = (s >= TAU).astype(int); fm = {}; fa = {}
    for g in TWO:
        idx = np.where(pid == g)[0]; fm[g] = rates(*counts(y_all[idx], pred[idx]))["mcc"]
        fa[g] = roc_auc_score(y_all[idx], s[idx])
    fm = pd.Series(fm); fa = pd.Series(fa); dl = fm - CKF.loc[fm.index]
    e, eb = boot(AT.tables(s)); l, lb = boot(AT.tables_lpo(s, pair_s))
    de = eb - REF_E_B; dlp = lb - REF_E_B
    return dict(mcc=fm.mean(), dmcc=dl.mean(), p_t=sps.ttest_rel(fm, CKF.loc[fm.index]).pvalue,
                p_w=sps.wilcoxon(dl).pvalue if (dl.abs() > 1e-12).sum() > 0 else 1.0,
                dauc=(fa - FAc.loc[fa.index]).mean(), tm_pooled=e, tm_lpo=l,
                de=e - REF_E0, de_lo=np.percentile(de, 2.5), de_hi=np.percentile(de, 97.5),
                dl=l - REF_E0, dl_lo=np.percentile(dlp, 2.5), dl_hi=np.percentile(dlp, 97.5))


def synthetic(kind, delta, rng):
    if kind == "state": return delta * y_all + rng.standard_normal(len(y_all))
    e = rng.standard_normal(len(np.unique(sess)))[REC_IDX]; return delta * EVER + e


def one(kind, delta, rep, learner="LR", seed0=2026):
    rng = np.random.default_rng([seed0, {"state": 1, "trait": 2}[kind], int(round(delta * 1000)), rep])
    Xa = np.column_stack([t_all, synthetic(kind, delta, rng)]); make = LEARNERS[learner]
    return dict(learner=learner, kind=kind, delta=delta, rep=rep, **evaluate(logo_proba(Xa, make), lpo_scores(Xa, make)))


def run_grid(grid, reps, out, learner="LR"):
    rows = pd.read_csv(out).to_dict("records") if out.exists() else []
    done = {(r["kind"], round(r["delta"], 6), int(r["rep"])) for r in rows}; t0 = time.time()
    for rep in range(reps):                    # replicate outer loop: every cell advances together
        for kind, deltas in grid.items():
            for delta in deltas:
                if (kind, round(delta, 6), rep) in done: continue
                rows.append(one(kind, delta, rep, learner))
        pd.DataFrame(rows).to_csv(out, index=False)
        print(learner, "rep", rep, f"{time.time() - t0:.0f}s", flush=True)
    return pd.DataFrame(rows)


def summarise_controls(R):
    R = R.copy()
    R["flag_t"] = (R.p_t < 0.05) & (R.dmcc > 0); R["flag_w"] = (R.p_w < 0.05) & (R.dmcc > 0)
    R["flag_pooled"] = R.de_lo > 0; R["flag_lpo"] = R.dl_lo > 0
    R["below_pooled"] = R.de_hi < 0; R["below_lpo"] = R.dl_hi < 0
    R["hw_lpo"] = (R.dl_hi - R.dl_lo) / 2; R["hw_pooled"] = (R.de_hi - R.de_lo) / 2
    S = R.groupby(["learner", "kind", "delta"]).agg(
        reps=("rep", "size"), dmcc=("dmcc", "mean"), dauc=("dauc", "mean"), tm_pooled=("tm_pooled", "mean"),
        tm_lpo=("tm_lpo", "mean"), de=("de", "mean"), dl=("dl", "mean"),
        power_t=("flag_t", "mean"), power_w=("flag_w", "mean"), power_pooled=("flag_pooled", "mean"),
        power_lpo=("flag_lpo", "mean"), below_pooled=("below_pooled", "mean"), below_lpo=("below_lpo", "mean"),
        hw_lpo=("hw_lpo", "mean"), hw_pooled=("hw_pooled", "mean")).reset_index()
    # calibrated decision: detection when the LPGO difference exceeds the 97.5th percentile of that signal's null
    # replicates (one sided 2.5%), instead of the lower bootstrap limit exceeding zero
    cal = {k: float(np.percentile(R[(R.kind == k) & (R.delta == 0)].dl, 97.5)) for k in R.kind.unique()}
    R["flag_cal"] = R.dl > R.kind.map(cal)
    S = S.merge(R.groupby(["learner", "kind", "delta"]).flag_cal.mean().rename("power_cal").reset_index(),
                on=["learner", "kind", "delta"])
    S["t_cal"] = S.kind.map(cal)
    return S


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "lr"
    if mode == "pilot":
        for kind, deltas in {"state": [0, 0.1, 0.2, 0.3], "trait": [0, 1, 2, 3]}.items():
            for delta in deltas:
                t0 = time.time(); r = one(kind, delta, 999)
                print(kind, delta, {k: round(v, 3) for k, v in r.items() if isinstance(v, float)}, f"{time.time() - t0:.1f}s", flush=True)
    elif mode == "summary":
        S = summarise_controls(pd.read_csv(TABLES / "CTRL_LR.csv")); S.to_csv(TABLES / "T_controls.csv", index=False)
        print(S.round(3).to_string())
    elif mode == "lr":
        grid = {"state": [float(x) for x in os.environ.get("STATE", "0 0.05 0.1 0.15 0.2 0.3").split()],
                "trait": [float(x) for x in os.environ.get("TRAIT", "0 0.5 1 1.5 2 3").split()]}
        R = run_grid(grid, int(os.environ.get("REPS", 200)), TABLES / "CTRL_LR.csv")
        S = summarise_controls(R); S.to_csv(TABLES / "T_controls.csv", index=False); print(S.round(3).to_string())
