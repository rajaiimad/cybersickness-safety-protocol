"""Step 23. Single numbers quoted in the text, recomputed from the data and saved predictions so that no number is
typed by hand: label persistence rules (previous label; majority of the previous 61 labels, ties positive) as fold mean
MCC over the 16 two class groups; windows of the groups that never report sickness; positive episodes; pooled MCC of the
RF under leave one recording out with the 99 features at the primary rule; number of recordings whose participant
group has another recording; number of distinct bootstrap resamples of six groups.
Output: outputs/tables/T_constants.csv (name, value)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from math import comb
from csp.paths import RAW, PRED, TABLES
from csp.data import load_and_group, counts, rates
import numpy as np, pandas as pd

d = load_and_group(str(RAW / "dataset.csv")); y = d.y.values; C = {}


def fold_mean(pred):
    v = [rates(*counts(y[i], pred[i]))["mcc"] for _, i in d.groupby("participant").groups.items() if 0 < y[i].sum() < len(i)]
    return float(np.mean(v))


C["persist_prev"] = fold_mean(d.groupby("session").y.shift(1).fillna(0).astype(int).values)
C["persist_major61"] = fold_mean((d.groupby("session").y.transform(
    lambda x: x.shift(1).rolling(61, min_periods=1).mean()).fillna(0).values >= 0.5).astype(int))
never = d.groupby("participant").y.sum().pipe(lambda s: s[s == 0].index)
C["never_windows"] = int(d.participant.isin(never).sum())
# episodes (maximal positive runs within a recording) per group
ep = {}
for s_, g in d.groupby("session"):
    yy = g.y.values; starts = int(((yy[1:] == 1) & (yy[:-1] == 0)).sum() + (yy[0] == 1))
    ep[g.participant.iloc[0]] = ep.get(g.participant.iloc[0], 0) + starts
C["episodes"] = sum(ep.values())
# pooled MCC of the RF under LORO with the 99 features (primary rule)
L = pd.read_csv(PRED / "P_loro99_rf.csv"); L = L[L.model == "Random forest"].reset_index(drop=True)
sm = L.groupby("session").proba.transform(lambda x: x.rolling(61, min_periods=1).mean())
C["loro99_rf_pooled_mcc"] = rates(*counts(L.y.values, (sm.values >= 0.5).astype(int)))["mcc"]
C["boot_distinct_6"] = comb(11, 6)
# under leave one recording out, a held out recording shares its descriptor combination (participant group) with a
# training recording when its group has more than one recording
nrec = d.groupby("participant").session.nunique(); C["loro_shared_recordings"] = int(nrec[nrec > 1].sum())
T = pd.DataFrame(sorted(C.items()), columns=["name", "value"]); T.to_csv(TABLES / "T_constants.csv", index=False)
print(T.to_string())
