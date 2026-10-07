"""Step 14. Leave one recording out (35 folds) for the random forest of the initial analysis on the full 99 features
(about 5 minutes on 2 CPUs). Gives the pooled MCC of the RF under LORO with the 99 features quoted in Section V-A and
in the note of Supporting Information Table S2 (descriptor effect: under LORO, 20 of the 35 held out recordings share
their descriptor combination with training recordings).

Output: outputs/predictions/P_loro99_rf.csv (columns config, model, fold, participant, session, y, sev, proba)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np, pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestClassifier
from csp.paths import RAW, PRED
from csp.data import load_and_group, make_features


def rf_initial():
    return RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample",
                                  n_jobs=-1, random_state=42)


if __name__ == "__main__":
    out = PRED / "P_loro99_rf.csv"
    if out.exists():
        print("skip loro99"); raise SystemExit
    d = load_and_group(str(RAW / "dataset.csv")); X = make_features(d)
    y = d.y.values; sev = d.DiscomfortLevel.values; pid = d.participant.values; sess = d.session.values
    Xa = X[list(X.columns)].values; recs = []
    for f in np.unique(sess):
        te = sess == f; tr = ~te
        sc = RobustScaler().fit(Xa[tr]); Xtr, Xte = sc.transform(Xa[tr]), sc.transform(Xa[te])
        m = rf_initial(); m.fit(Xtr, y[tr])
        recs.append(pd.DataFrame(dict(config="A_leave_one_recording_out", model="Random forest", fold=f,
                                      participant=pid[te], session=sess[te], y=y[te], sev=sev[te],
                                      proba=m.predict_proba(Xte)[:, 1])))
    pd.concat(recs, ignore_index=True).to_csv(out, index=False)
    print("written", out)
