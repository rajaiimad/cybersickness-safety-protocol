"""Feature sets, cross validation designs, detectors and the generic fitting loop.

Feature sets (asserted): the primary 76 features are the 99 features minus the 19 one hot indicators of the seven
participant descriptors (they define the held out unit) and minus the 4 camera field of view features that are constant
within every recording (its three standard deviations and its first difference): 66 telemetry, 2 cumulative exposure,
elapsed time and 7 condition indicators. TEL (68) = telemetry + exposure, used in the nested feature analysis.

Designs (fold ids): pid (leave one participant group out, 22 folds, primary), sess (leave one recording out, 35),
merged (two restart pairs with differing descriptors merged, 20).

Detectors: RF, GB (histogram gradient boosting), RF+GB (mean of the RF and GB probabilities of the same fold), LR, MLP
with group based early stopping, and the clock (LR on elapsed time alone). Every fit uses training rows only;
RobustScaler is fitted on the training rows of each fold."""
import time
import numpy as np, pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GroupShuffleSplit, KFold
from sklearn.metrics import log_loss

from csp.paths import RAW, PRED
from csp.data import load_and_group, make_features, CATS, DEMO

OUT = PRED
d = load_and_group(str(RAW / "dataset.csv"))
X = make_features(d)
y = d.y.values.astype(int); sev = d.DiscomfortLevel.values; t_el = d.TimeStamp.values
pid = d.participant.values; sess = d.session.values
cols = list(X.columns)
onehot = [c for c in cols if any(c.startswith(k + "_") for k in CATS)]
desc = [c for c in onehot if c.split("_")[0] in DEMO]
cond = [c for c in onehot if c not in desc]
const = [c for c in cols if X[c].nunique() == 1]
PRIMARY = [c for c in cols if c not in desc and c not in const]
TEL = [c for c in cols if c not in onehot and c not in const and c != "elapsed_in_session"]
assert (len(desc), len(cond), len(const), len(PRIMARY), len(TEL)) == (19, 7, 4, 76, 68), \
    (len(desc), len(cond), len(const), len(PRIMARY), len(TEL))

# merged grouping: restart pairs whose descriptors differ (recordings 4 -> 5 and 30 -> 31)
merged = pid.copy()
g4, g5 = pid[sess == 4][0], pid[sess == 5][0]; g30, g31 = pid[sess == 30][0], pid[sess == 31][0]
# the two restarts after a short recording whose next recording has other descriptors (step 02 derives them from the
# archive start times: recording 4 -> 5 after 2.1 min, recording 30 -> 31 after 3.8 min)
assert g4 != g5 and g30 != g31 and (sess == 4).sum() < 120 and (sess == 30).sum() < 120
merged[merged == g4] = g5; merged[merged == g30] = g31
assert len(np.unique(merged)) == 20


def rf(cw="balanced_subsample"):
    return RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight=cw, n_jobs=-1, random_state=42)


def gb():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                          l2_regularization=1.0, class_weight="balanced", random_state=42)


def lr():
    return LogisticRegression(class_weight="balanced", max_iter=1000)


class GroupEarlyStopMLP:
    """MLP (256, 128), Adam. The number of epochs is chosen on validation GROUPS drawn from the training groups
    (about 15% of groups, both classes required), with patience 10 on validation log loss, at most 150 epochs;
    the model is then refit on all training groups for that number of epochs.

    Implementation note: each epoch is one call of MLPClassifier.fit with max_iter=1 and warm_start=True. In
    scikit-learn this keeps the weights between calls but recreates the Adam optimiser state and reuses the same
    shuffling seed at every call. This is the procedure that produced the reported results."""
    def __init__(self, groups): self.groups = groups

    def _net(self):
        return MLPClassifier(hidden_layer_sizes=(256, 128), max_iter=1, warm_start=True, random_state=42)

    def fit(self, Xtr, ytr):
        import warnings
        from sklearn.exceptions import ConvergenceWarning
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        for seed in range(42, 142):
            tr, va = next(GroupShuffleSplit(1, test_size=0.15, random_state=seed).split(Xtr, ytr, self.groups))
            if 0 < ytr[va].sum() < len(va) and 0 < ytr[tr].sum() < len(tr):
                break
        else:
            raise RuntimeError("no validation split with both classes in 100 seeds")
        net = self._net(); best, best_ep, wait = np.inf, 1, 0
        for ep in range(1, 151):
            net.fit(Xtr[tr], ytr[tr])
            ll = log_loss(ytr[va], net.predict_proba(Xtr[va])[:, 1], labels=[0, 1])
            if ll < best - 1e-4: best, best_ep, wait = ll, ep, 0
            else:
                wait += 1
                if wait >= 10: break
        self.epochs_ = best_ep
        self.net = self._net()
        for _ in range(best_ep):
            self.net.fit(Xtr, ytr)
        return self

    def predict_proba(self, Xte): return self.net.predict_proba(Xte)


def run(tag, fold_ids, feats, models, splits=None):
    """Fit every model of `models` in every fold and write the held out probabilities to outputs/predictions/
    P_<tag>.csv (columns config, model, fold, participant, session, y, sev, t, proba). Skipped if the file exists."""
    f = OUT / f"P_{tag}.csv"
    if f.exists():
        print("skip", tag, flush=True); return
    t0 = time.time(); Xa = X[feats].values.astype(float); recs = []
    if splits is None:
        splits = [(np.where(fold_ids != g)[0], np.where(fold_ids == g)[0]) for g in np.unique(fold_ids)]
        # leakage invariant: no held out unit (group, merged group or recording) has a row in the training partition
        for tr, te in splits:
            assert not set(fold_ids[tr]) & set(fold_ids[te]), "a held out unit appears in training"
            if fold_ids is pid:
                assert not set(sess[tr]) & set(sess[te]), "a recording appears on both sides of a LOGO fold"
    for k, (tr, te) in enumerate(splits):
        sc = RobustScaler().fit(Xa[tr]); Xtr, Xte = sc.transform(Xa[tr]), sc.transform(Xa[te])
        probs = {}
        for name, fn in models.items():
            if name == "RF+GB":
                probs[name] = (probs["RF"] + probs["GB"]) / 2; continue
            m = fn(pid[tr]) if name == "MLP" else fn()
            m.fit(Xtr, y[tr]); probs[name] = m.predict_proba(Xte)[:, 1]
        for name, p in probs.items():
            recs.append(pd.DataFrame(dict(config=tag, model=name, fold=k, participant=pid[te], session=sess[te],
                                          y=y[te], sev=sev[te], t=t_el[te], proba=p)))
    pd.concat(recs, ignore_index=True).to_csv(f, index=False)
    print(tag, f"{time.time() - t0:.0f}s", flush=True)
