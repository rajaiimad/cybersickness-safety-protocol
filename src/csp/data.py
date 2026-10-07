"""Dataset loading, recovery of recordings and participant groups, the feature representation, and confusion matrix
helpers.

The public file dataset.csv carries no participant or recording identifier. Both are recovered here:
  recording (column "session")       = maximal run of rows between two decreases of TimeStamp          -> 35
  participant group ("participant")  = one combination of the seven participant descriptor columns      -> 22
The recovery is asserted every time the data are loaded. A participant group is a descriptor profile, not a verified
person (see docs/AUDIT.md and the paper, Section III-A).

The feature representation (make_features) has 99 columns; the primary 76 feature set is selected in csp.design."""
import numpy as np, pandas as pd
from scipy import stats

from csp.paths import RAW

DEMO = ["UserGenere", "UserAge", "UserExperience", "UserFlicker", "UserGlassesUse",
        "UserVisionProblems", "UserEyeDominance"]                      # participant descriptors (define the groups)
CATS = DEMO + ["StaticFrame", "CameraAutoMovement", "RegionOfInterest"]  # one hot encoded columns
CHANNELS = ["CameraFieldOfView", "PlayerSpeed", "PlayerAcceleration",
            "CameraRotationX", "CameraRotationY", "CameraRotationZ",
            "PlayerPositionX", "PlayerPositionY", "PlayerPositionZ", "GameFps"]
SCALES = [30, 120, 300]                                                # trailing horizons, in windows


def load_and_group(path=str(RAW / "dataset.csv")):
    """Load the rows of dataset.csv and recover the participant group and recording of every row."""
    d = pd.read_csv(path)
    # participant group: the descriptor tuple is constant within a recording
    d["participant"] = d.groupby(DEMO, sort=False).ngroup()
    # recording: TimeStamp restarts at each new recording
    d["session"] = np.concatenate([[0], np.cumsum(np.diff(d.TimeStamp.values) < 0)])
    d["y"] = (d.DiscomfortLevel.values >= 1).astype(int)
    # --- leakage critical invariants ---
    assert d.participant.nunique() == 22, f"expected 22 participant groups, got {d.participant.nunique()}"
    assert d.session.nunique() == 35, f"expected 35 recordings, got {d.session.nunique()}"
    assert (d.groupby("session").participant.nunique() == 1).all(), "a recording spans two participant groups"
    return d


def make_features(d):
    """The full 99 feature representation. Every rolling and expanding statistic is computed within a recording from
    the current and previous rows only (trailing windows), so no feature uses future data or another recording."""
    g = d.groupby("session", sort=False)
    feats = {}
    for c in CHANNELS:
        for w in SCALES:
            feats[f"{c}_mean{w}"] = g[c].transform(lambda s, w=w: s.rolling(w, min_periods=1).mean())
            feats[f"{c}_sd{w}"] = g[c].transform(lambda s, w=w: s.rolling(w, min_periods=1).std()).fillna(0.0)
        feats[f"{c}_diff"] = g[c].transform(lambda s: s.diff()).fillna(0.0)
    X = pd.DataFrame(feats)
    rot = d[["CameraRotationX", "CameraRotationY", "CameraRotationZ"]].abs().sum(axis=1)
    X["cum_rotation"] = rot.groupby(d.session).transform(lambda s: s.expanding().mean())
    X["cum_accel"] = d.PlayerAcceleration.abs().groupby(d.session).transform(lambda s: s.expanding().mean())
    X["elapsed_in_session"] = d.TimeStamp.values
    X = pd.concat([X, pd.get_dummies(d[CATS].astype(str), prefix=CATS)], axis=1)
    return X.astype(np.float32)


def counts(yt, yp):
    """TP, TN, FP, FN."""
    return (int(((yp == 1) & (yt == 1)).sum()), int(((yp == 0) & (yt == 0)).sum()),
            int(((yp == 1) & (yt == 0)).sum()), int(((yp == 0) & (yt == 1)).sum()))


def rates(TP, TN, FP, FN):
    rec = TP / (TP + FN) if TP + FN else np.nan          # undefined with no positives in the fold
    spec = TN / (TN + FP) if TN + FP else np.nan
    den = np.sqrt(float(TP + FP) * (TP + FN) * (TN + FP) * (TN + FN))
    # den == 0 means the model predicted a single class; MCC is 0 by the usual convention, so every model is averaged
    # over the same folds.
    mcc = ((TP * TN) - (FP * FN)) / den if den else 0.0
    acc = (TP + TN) / max(TP + TN + FP + FN, 1)
    bal = (rec + spec) / 2 if not (np.isnan(rec) or np.isnan(spec)) else np.nan
    return dict(acc=acc, bal_acc=bal, mcc=mcc, rec=rec, spec=spec)


def ci95(v):
    """Mean, 95% t interval half width and n of the non missing values."""
    v = np.asarray([x for x in v if not np.isnan(x)], float)
    m = v.mean(); h = v.std(ddof=1) / np.sqrt(len(v)) * stats.t.ppf(0.975, len(v) - 1)
    return m, h, len(v)
