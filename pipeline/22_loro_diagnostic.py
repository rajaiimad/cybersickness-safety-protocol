"""Step 22. Where the leave one recording out (LORO) scores differ from LOGO. For a group with a single recording the
LORO and LOGO training sets are identical, so their predictions coincide; a difference can only arise in the 20
recordings of groups with several recordings. Pooled MCC at the primary rule for single recording groups, multi
recording groups, the six recording group and the other multi recording groups, under both designs.
Output: outputs/tables/T_loro_by_grouptype.csv."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from csp.paths import PRED, TABLES
from csp.data import counts, rates
import numpy as np, pandas as pd
G = pd.concat([pd.read_csv(PRED / "P_primary.csv"), pd.read_csv(PRED / "P_primary_clock.csv")])
L = pd.concat([pd.read_csv(PRED / "P_loro.csv"), pd.read_csv(PRED / "P_loro_clock.csv")])
nrec = G[G.model == "Clock"].groupby("participant").session.nunique(); multi = set(nrec[nrec > 1].index)
big = int(nrec.idxmax())
rows = []
for design, P in (("LOGO", G), ("LORO", L)):
    for m, g in P.groupby("model"):
        g = g.copy(); g["p"] = (g.groupby("session").proba.transform(lambda x: x.rolling(61, min_periods=1).mean()) >= 0.5).astype(int)
        sets = {"all": np.ones(len(g), bool), "single": ~g.participant.isin(multi).values,
                "multi": g.participant.isin(multi).values, "big": (g.participant == big).values,
                "multi_not_big": (g.participant.isin(multi) & (g.participant != big)).values}
        for k, mk in sets.items():
            rows.append(dict(design=design, model=m, subset=k, recordings=int(g.session[mk].nunique()),
                             mcc=rates(*counts(g.y.values[mk], g.p.values[mk]))["mcc"]))
T = pd.DataFrame(rows); T.to_csv(TABLES / "T_loro_by_grouptype.csv", index=False)
W = T.pivot_table(index=["model", "subset"], columns="design", values="mcc"); print(W.round(3).to_string())
single = W.xs("single", level="subset"); assert (abs(single.LOGO - single.LORO) < 1e-9).all()
