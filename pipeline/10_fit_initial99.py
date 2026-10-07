"""Step 10. The initial analysis: five supervised detectors on the full 99 feature representation under leave one
participant group out (22 folds), with the detector definitions of the initial analysis. About 10 minutes on 2 CPUs.

Used for the 99 feature sensitivity rows (Supporting Information Table S2, the descriptor effect in Section V-A) and the
leakage demonstration with 99 features. The MLP of this initial panel uses scikit-learn early stopping on a random 10%
of training windows; Table S2 therefore reports the MLP refitted with group based early stopping (P_full99.csv,
step 11) instead, as its note states.

Output: outputs/predictions/P_initial99.csv (columns model, participant, session, y, proba)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np, pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from csp.paths import RAW, PRED
from csp.data import load_and_group, make_features


def _rf():
    return RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                  class_weight="balanced_subsample", n_jobs=-1,
                                  random_state=42)


def _gb():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
                                          max_leaf_nodes=31, l2_regularization=1.0,
                                          class_weight="balanced", random_state=42)


def models_initial():
    return {
        "Random forest": _rf(),
        "Gradient boosting": _gb(),
        "Multilayer perceptron": MLPClassifier(hidden_layer_sizes=(256, 128), max_iter=150,
                                               early_stopping=True, random_state=42),
        "Logistic regression": LogisticRegression(class_weight="balanced", max_iter=1000),
        "RF + GB ensemble": VotingClassifier(
            estimators=[("rf", _rf()), ("gb", _gb())], voting="soft", n_jobs=-1),
    }


if __name__ == "__main__":
    out = PRED / "P_initial99.csv"
    if out.exists():
        print("skip initial99"); raise SystemExit
    d = load_and_group(str(RAW / "dataset.csv"))
    X = make_features(d).values
    y = d.y.values; pid = d.participant.values; sess = d.session.values
    recs = []
    for p in sorted(np.unique(pid)):
        te = pid == p; tr = ~te
        sc = RobustScaler().fit(X[tr]); Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
        for name in models_initial():
            m = models_initial()[name]; m.fit(Xtr, y[tr])
            recs.append(pd.DataFrame(dict(model=name, participant=p, session=sess[te],
                                          y=y[te], proba=m.predict_proba(Xte)[:, 1])))
        print(f"  fold p{p:02d} done", flush=True)
    pd.concat(recs, ignore_index=True).to_csv(out, index=False)
    print("written", out)
