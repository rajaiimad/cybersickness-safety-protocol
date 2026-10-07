"""Step 15. Leave pair of groups out (LPGO) models for the time matched AUC (about 1 hour on 2 CPUs).

Thread settings of the reported run: the first 14 pairs were fitted with 2 threads and the run was then resumed with
OMP_NUM_THREADS=1 for the other 202 pairs. Only the logistic regression on the 76 features depends on the number of
BLAS threads (lbfgs reaches a slightly different optimum; its LPGO time matched AUC changes by at most 1.1e-5). To
reproduce the reported predictions exactly, this step fits the first REPORTED_2THREAD_PAIRS pairs with the thread
count set by run_all.py (2) and the others with one thread (threadpoolctl). docs/AUDIT.md, section 3.

Within a 30 s bin of elapsed time the positive and negative windows of a pair mostly come from different participant
groups. Under LOGO the two windows are scored by two different fold models, each trained without the group it scores;
removing a group that becomes sick lowers the training prevalence and removing a group that never does raises it, so
pooled held out scores are biased against their own labels. Following the leave pair out principle (Airola et al.,
2011), each cross group pair is scored by one model trained without both groups.

For every unordered pair of groups {g, h} of which at least one contains a positive window (216 of the 231 pairs),
every detector is fitted on the other 20 groups (same features, scaling on the training rows, same hyperparameters
and seeds as the primary run) and predicts all windows of g and h. Detectors: RF, GB, LR, MLP on the 76 primary
features (RF+GB is the mean of the RF and GB probabilities), the clock, and RF and GB on elapsed time alone (negative
controls).

Output: outputs/predictions/lpgo/pair_<g>_<h>.csv (columns pair_g, pair_h, model, participant, session, y, sev, t,
proba); resumable."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import itertools
from threadpoolctl import threadpool_limits
from csp.design import *          # noqa: F401,F403
from csp.paths import LPGO

LPO = LPGO
HASPOS = set(np.unique(pid[y == 1]))
PAIRS = [(g, h) for g, h in itertools.combinations(np.unique(pid), 2) if g in HASPOS or h in HASPOS]
TIME = ["elapsed_in_session"]
REPORTED_2THREAD_PAIRS = 14       # pairs fitted with 2 threads in the reported run (in the order of PAIRS)
FITS = [("RF", PRIMARY, rf), ("GB", PRIMARY, gb), ("LR", PRIMARY, lr), ("MLP", PRIMARY, None),
        ("Clock", TIME, lr), ("RF time only", TIME, rf), ("GB time only", TIME, gb)]

if __name__ == "__main__":
    print(len(PAIRS), "pairs", flush=True); T0 = time.time()
    for k, (g, h) in enumerate(PAIRS):
        f = LPO / f"pair_{g}_{h}.csv"
        if f.exists(): continue
        te = np.where((pid == g) | (pid == h))[0]; tr = np.where((pid != g) & (pid != h))[0]; recs = []; probs = {}
        assert not {g, h} & set(pid[tr]) and not set(sess[tr]) & set(sess[te])      # held out pair absent from training
        with threadpool_limits(limits=None if k < REPORTED_2THREAD_PAIRS else 1):
            for name, feats, fn in FITS:
                Xa = X[feats].values.astype(float); sc = RobustScaler().fit(Xa[tr])
                m = GroupEarlyStopMLP(pid[tr]) if name == "MLP" else fn()
                m.fit(sc.transform(Xa[tr]), y[tr]); probs[name] = m.predict_proba(sc.transform(Xa[te]))[:, 1]
        probs["RF+GB"] = (probs["RF"] + probs["GB"]) / 2
        for name, p in probs.items():
            recs.append(pd.DataFrame(dict(pair_g=g, pair_h=h, model=name, participant=pid[te], session=sess[te],
                                          y=y[te], sev=sev[te], t=t_el[te], proba=p)))
        pd.concat(recs, ignore_index=True).to_csv(f, index=False)
        print(k + 1, "/", len(PAIRS), (g, h), f"{time.time() - T0:.0f}s", flush=True)
    print("done", f"{time.time() - T0:.0f}s", flush=True)
