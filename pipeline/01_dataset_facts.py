"""Step 01. Facts about the dataset, the recovered units and the feature representation that the paper reports in
Section III-A/B, Table II and Section IV-A, computed from dataset.csv (no model is fitted).

Outputs
  outputs/tables/T_dataset_facts.csv     name, value
  outputs/tables/T_recovered_units.csv   one row per recording: recording, participant group, merged group, first and
                                         last row of dataset.csv (0 based, header excluded), windows, maximum severity,
                                         positive windows. This is the unit definition used by every later step."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np, pandas as pd

from csp.paths import TABLES
from csp.design import d, X, y, pid, sess, merged, PRIMARY, cols

F = {}
F["windows"] = len(d)
F["positive_windows"] = int(y.sum()); F["negative_windows"] = int((1 - y).sum()); F["prevalence"] = y.mean()
for s in (1, 2, 3):
    F[f"severity_{s}_windows"] = int((d.DiscomfortLevel == s).sum())
F["recordings"] = d.session.nunique(); F["participant_groups"] = d.participant.nunique()
F["merged_groups"] = len(np.unique(merged))
pos_by_group = d.groupby("participant").y.sum(); n_by_group = d.groupby("participant").size()
F["groups_without_positive"] = int((pos_by_group == 0).sum())
F["groups_with_both_classes"] = int(((pos_by_group > 0) & (pos_by_group < n_by_group)).sum())
F["groups_with_severity_3"] = int((d[d.DiscomfortLevel == 3].participant.nunique()))
s3 = set(d[d.DiscomfortLevel == 3].participant); s1 = set(d[d.DiscomfortLevel == 1].participant)
F["groups_with_severity_3_and_1"] = len(s3 & s1)
# episodes: maximal runs of positive windows within a recording
F["positive_episodes"] = int(sum(((g.y.values[1:] == 1) & (g.y.values[:-1] == 0)).sum() + (g.y.values[0] == 1)
                                 for _, g in d.groupby("session")))
F["recordings_starting_at_severity_0"] = int((d.groupby("session").DiscomfortLevel.first() == 0).sum())
ch = d.groupby("session").y.apply(lambda s: int((s.diff().fillna(0) != 0).sum()))
F["recordings_label_never_changes"] = int((ch == 0).sum()); F["recordings_label_changes_once"] = int((ch == 1).sum())
F["recordings_label_changes_more_than_once"] = int((ch > 1).sum())
L = d.groupby("session").size()
F["recording_length_median"] = float(L.median()); F["recording_length_min"] = int(L.min()); F["recording_length_max"] = int(L.max())
F["fov_values_per_recording_max"] = int(d.groupby("session").CameraFieldOfView.nunique().max())
F["fov_distinct_values"] = int(d.CameraFieldOfView.nunique())
for c in ["StaticFrame", "CameraAutoMovement", "RegionOfInterest"]:
    F[f"recordings_where_{c}_varies"] = int((d.groupby("session")[c].nunique() > 1).sum())
rpg = d.groupby("participant").session.nunique()
F["groups_with_more_than_one_recording"] = int((rpg > 1).sum()); F["largest_group_recordings"] = int(rpg.max())
F["severity_3_windows_in_largest_group"] = int((d[d.participant == rpg.idxmax()].DiscomfortLevel == 3).sum())
pos_by_rec = d.groupby("session").y.sum(); n_by_rec = d.groupby("session").size()
F["loro_folds_with_both_classes"] = int(((pos_by_rec > 0) & (pos_by_rec < n_by_rec)).sum())
G = d.participant.nunique(); never = int((pos_by_group == 0).sum())
F["lpgo_pairs_total"] = G * (G - 1) // 2
F["lpgo_pairs_fitted"] = G * (G - 1) // 2 - never * (never - 1) // 2   # pairs with at least one positive window
F["features_full"] = len(cols); F["features_primary"] = len(PRIMARY)
# features whose training interquartile range is zero in a LOGO fold (RobustScaler then centres without rescaling)
Xp = X[PRIMARY].values.astype(float); zero = []
for g in np.unique(pid):
    tr = pid != g
    q75, q25 = np.percentile(Xp[tr], [75, 25], axis=0); zero.append(int(((q75 - q25) == 0).sum()))
zero = pd.Series(zero).value_counts().sort_index()
for k, v in zero.items():
    F[f"logo_folds_with_{k}_zero_iqr_primary_features"] = int(v)
T = pd.DataFrame(list(F.items()), columns=["name", "value"]); T.to_csv(TABLES / "T_dataset_facts.csv", index=False)
print(T.to_string(index=False))

idx = np.arange(len(d))
U = pd.DataFrame(dict(recording=sess, group=pid, merged_group=merged, row=idx, y=y, sev=d.DiscomfortLevel.values))
U = U.groupby("recording").agg(group=("group", "first"), merged_group=("merged_group", "first"),
                               first_row=("row", "min"), last_row=("row", "max"), windows=("row", "size"),
                               max_severity=("sev", "max"), positive_windows=("y", "sum")).reset_index()
assert (U.last_row - U.first_row + 1 == U.windows).all()          # every recording is one contiguous block of rows
U.to_csv(TABLES / "T_recovered_units.csv", index=False)
print(f"\n{len(U)} recordings written to T_recovered_units.csv")
