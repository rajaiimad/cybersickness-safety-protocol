"""Step 31. The tables of the paper, formatted exactly as printed (same rounding, signs and interval notation), built
from the result tables of steps 01 to 26. Nothing is computed here that is not in outputs/tables; the formatting rules
are those used to typeset the manuscript.

Outputs: outputs/paper_tables/Table_<n>.csv (one file per table, data rows only, printed column labels as header)
         outputs/paper_tables/PAPER_TABLES.md (all tables in one readable file)
Main text: Tables II, III, IV, V, VI and VIII (Table I is the literature table and Table VII the reporting checklist,
neither contains a result). Supporting Information: Tables S1 to S7."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from decimal import Decimal, ROUND_HALF_UP
import numpy as np, pandas as pd

from csp.paths import TABLES, PAPER

DET = ["RF", "GB", "RF+GB", "LR", "MLP"]; ORDER = DET + ["Clock"]


def T(name, idx="model"):
    t = pd.read_csv(TABLES / f"{name}.csv"); return t.set_index(idx) if idx else t


# ---- number formats used in the paper
def f3(x): return f"{x:.3f}"
def f1(x): return f"{x:.1f}"
def sg(x): return ("+" if x >= 0 else "−") + f"{abs(x):.3f}"
def iv(lo, hi): return f"[{lo:.3f}, {hi:.3f}]".replace("-", "−")
def pm(df, m, k): return f"{df.loc[m, k]:.3f} ± {df.loc[m, k + '_ci']:.3f}"
def cnt(x): return f"{int(round(x)):,}"
def pct(x):
    q = Decimal(str(round(100 * x, 6))).quantize(Decimal("0.1") if 0 < x < 0.1 else Decimal("1"), ROUND_HALF_UP)
    return f"{q}%"


PR = T("T_primary"); OR = T("T_original99"); F99 = T("T_full99_mlp"); LO = T("T_loro"); SV = T("T_severity")
S8 = T("T_primary_stats"); LA = T("T_lpgo_atime"); AS = T("T_asev_paired"); ASG = T("T_asev_by_group", None)
CT = T("T_controls", None); CT = CT[CT.learner == "LR"]; SEC = T("T_secondary_tests", None); K = T("T_constants", "name").value
DP = T("T_deploy", None); PSH = T("T_prior_shift", None); EP = T("T_episodes"); ERR = T("T_episode_random_reference", None)
S3B = T("T_s3_by_group", None); DF = T("T_dataset_facts", "name").value
REF = LA.tm_ref.iloc[0]
out = {}

# ---------------------------------------------------------------- Table II  dataset composition
out["II"] = (["Property", "Value"], [
    ["Windows", cnt(DF["windows"])],
    ["Recordings / reconstructed descriptor derived groups", f"{int(DF['recordings'])} / {int(DF['participant_groups'])}"],
    ["Groups with no positive window", str(int(DF["groups_without_positive"]))],
    ["Groups containing both classes", f"{int(DF['groups_with_both_classes'])} of {int(DF['participant_groups'])}"],
    ["Negative windows (st = 0)", cnt(DF["negative_windows"])],
    ["Positive windows (st ≥ 1); prevalence", f"{cnt(DF['positive_windows'])}; {DF['prevalence']:.2f}"],
    ["Severity 1 / 2 / 3 windows", " / ".join(cnt(DF[f"severity_{s}_windows"]) for s in (1, 2, 3))],
    ["Groups with any severity 3 window", str(int(DF["groups_with_severity_3"]))],
    ["Positive episodes", str(int(DF["positive_episodes"]))],
    ["Features, primary / full (Appendix A)", f"{int(DF['features_primary'])} / {int(DF['features_full'])}"]])

# ---------------------------------------------------------------- Table III  primary comparison
rows = []
for m in ORDER:
    r = PR.loc[m]
    tm_ = (f"{f3(REF)} {iv(LA.tm_ref_lo.iloc[0], LA.tm_ref_hi.iloc[0])}" if m == "Clock"
           else f"{f3(LA.loc[m, 'tm_lpo'])} {iv(LA.loc[m, 'tm_lpo_lo'], LA.loc[m, 'tm_lpo_hi'])}")
    rows.append([m if m != "Clock" else "Clock (reference)", pm(PR, m, "mcc"), f3(r.rec), f3(r.spec), f3(r.alarm), tm_,
                 pm(PR, m, "fold_auc"), f3(r.pooled_mcc), f3(r.pooled_alarm), f3(r.fa_all), f3(r.never_sick_alarm)])
out["III"] = (["Detector", "Fold MCC ± 95% half width", "Fold recall", "Fold specificity", "Fold alarm rate",
               "Atime LPGO [95% CI]", "Fold AUC ± 95%", "Pooled MCC", "Pooled alarm rate", "False alarm rate, all 22 groups",
               "Alarm, no sickness groups"], rows)

# ---------------------------------------------------------------- Table IV  paired comparisons
out["IV"] = (["Detector", "MCC", "ΔMCC", "t test p", "Corrected p", "Wilcoxon p", "BH p", "ΔAtime LPGO [95% CI]",
              "Bonferroni CI", "ΔAtime pooled [95% CI]"],
             [[m, f3(S8.loc[m, "mcc"]), sg(S8.loc[m, "dmcc"]), f3(S8.loc[m, "p_t"]), f3(S8.loc[m, "p_nb"]),
               f3(S8.loc[m, "p_w"]), f3(S8.loc[m, "p_bh5"]),
               f"{sg(LA.loc[m, 'd_lpo'])} {iv(LA.loc[m, 'd_lpo_lo'], LA.loc[m, 'd_lpo_hi'])}",
               iv(LA.loc[m, "d_lpo_lo_bonf"], LA.loc[m, "d_lpo_hi_bonf"]),
               f"{sg(LA.loc[m, 'd_pooled'])} {iv(LA.loc[m, 'd_pooled_lo'], LA.loc[m, 'd_pooled_hi'])}"] for m in DET])

# ---------------------------------------------------------------- Table V  severity
rows = []
for m in ORDER:
    r = SV.loc[m]
    base = [m, f3(r.pooled_alarm), str(int(r.missed_s3)), str(int(r.missed_s3_m44)), f3(r.rec), f3(r.spec)]
    if m == "Clock":
        rows.append(base + [f3(AS.a_sev_clock.iloc[0]), "—", "—", "—"])
    else:
        a = AS.loc[m]
        rows.append(base + [f3(a.a_sev), f"{sg(a.d_pooled)} {iv(a.d_lo, a.d_hi)}", f"{sg(a.d_equal)} {iv(a.de_lo, a.de_hi)}",
                            f"{int(a.groups_above_clock)} of 6"])
out["V"] = (["Detector", "Primary rule alarm rate", "Primary rule S3 missed", "Matched 0.44 S3 missed",
             "Matched 0.44 recall", "Matched 0.44 specificity", "Asev", "Δ vs clock [95% CI]", "Δ equal weights [95% CI]",
             "Groups above clock"], rows)

# ---------------------------------------------------------------- Table VI  controls
rows = []
for kind in ("state", "trait"):
    for d_ in sorted(CT[CT.kind == kind].delta):
        r = CT[(CT.kind == kind) & (abs(CT.delta - d_) < 1e-9)].iloc[0]
        rows.append([kind if abs(d_) < 1e-12 else "", f"{d_:g}", sg(r.dmcc), pct(r.power_t), sg(r.de), pct(r.power_pooled),
                     pct(r.below_pooled), sg(r.dl), pct(r.power_lpo), pct(r.power_cal)])
out["VI"] = (["Signal", "δ", "Fold MCC mean Δ", "Fold MCC detected", "Atime pooled mean Δ", "Atime pooled detected",
              "Atime pooled declared worse", "Atime LPGO mean Δ", "Atime LPGO detected", "Atime LPGO detected, calibrated"], rows)

# ---------------------------------------------------------------- Table VIII  features (counted from the code)
from csp.design import cols, PRIMARY, desc, cond          # noqa: E402
def n_(fs, pat): return sum(1 for c in fs if pat(c))
fam = [("Trailing mean", lambda c: "_mean" in c), ("Trailing standard deviation", lambda c: "_sd" in c),
       ("First difference", lambda c: c.endswith("_diff")), ("Cumulative exposure", lambda c: c.startswith("cum_")),
       ("Elapsed time", lambda c: c == "elapsed_in_session"), ("Condition indicators", lambda c: c in cond),
       ("Descriptor indicators", lambda c: c in desc)]
rows = [[name, str(n_(PRIMARY, f)), str(n_(cols, f))] for name, f in fam]
assert sum(int(r[1]) for r in rows) == len(PRIMARY) and sum(int(r[2]) for r in rows) == len(cols)
out["VIII"] = (["Group", "Primary", "Full"], rows + [["Total", str(len(PRIMARY)), str(len(cols))]])

# ---------------------------------------------------------------- Supporting Information
out["S1"] = (["Family", "Detector", "Contrast", "Estimate", "Test", "p", "BH p (all)"],
             [[r_.family, r_.model, r_.contrast, sg(r_.estimate), r_.test, f3(r_.p), f3(r_.p_bh_all)] for r_ in SEC.itertuples()])
rows = []
for lab, TT, ms in [("99 features (descriptors included), LOGO", OR, DET), ("76 features, leave one recording out", LO, ORDER)]:
    first = True
    for m in ms:
        src = F99 if (TT is OR and m == "MLP") else TT
        r_ = src.loc[m]
        rows.append([lab if first else "", m + (" *" if src is F99 else ""), pm(src, m, "mcc"), f3(r_.rec), f3(r_.pooled_mcc),
                     f3(r_.pooled_alarm), f3(r_.fa_all), f3(r_.never_sick_alarm), str(int(r_.missed_s3))]); first = False
out["S2"] = (["Analysis", "Detector", "Fold MCC ± 95% half width", "Fold recall", "Pooled MCC", "Pooled alarm rate",
              "False alarm rate, all units", "Alarm, no sickness groups", "S3 missed (of 821)"], rows)


def dpv(m, pi, k): return DP[(DP.model == m) & (abs(DP.pi - pi) < 1e-9)][k].iloc[0]
def ps(m, pi, k): return PSH[(PSH.model == m) & (abs(PSH.pi - pi) < 1e-9)][k].iloc[0]
def err_(m, tgt):
    x = ERR[(ERR.model == m) & (ERR.target.isna() if tgt is None else ERR.target == tgt)]; return x.iloc[0]


out["S3"] = (["Detector", "PPV π=0.44", "PPV π=0.10", "PPV π=0.01", "NPV π=0.44", "NPV π=0.10", "NPV π=0.01",
              "FA per 1,000 negatives", "Alarm onsets per recording"],
             [[m] + [f3(dpv(m, pi, "ppv")) for pi in (0.44, 0.10, 0.01)] + [f3(dpv(m, pi, "npv")) for pi in (0.44, 0.10, 0.01)]
              + [f"{1000 * (1 - PR.loc[m, 'pooled_spec']):,.0f}", f"{PR.loc[m, 'onsets_per_session']:.2f}"] for m in ORDER])
out["S4"] = (["Detector", "Posterior = 1 share", "π=0.10 alarm", "π=0.10 recall", "π=0.10 no alarm groups",
              "π=0.01 alarm", "π=0.01 recall", "π=0.01 no alarm groups"],
             [[m, f3(ps(m, 0.10, "share_at_max")), f3(ps(m, 0.10, "alarm")), f3(ps(m, 0.10, "rec")),
               str(int(ps(m, 0.10, "folds_no_alarm"))), f3(ps(m, 0.01, "alarm")), f3(ps(m, 0.01, "rec")),
               str(int(ps(m, 0.01, "folds_no_alarm")))] for m in ORDER])
out["S5"] = (["Detector", "Primary alarm", "Primary episode recall", "Primary shifted", "Primary latency (s)",
              "Primary pre onset", "Matched episode recall", "Matched shifted", "Matched latency (s)", "Matched pre onset"],
             [[m, f3(EP.loc[m, "alarm"]), f3(EP.loc[m, "ep_recall"]), f3(err_(m, None)["random_mean"]),
               f1(EP.loc[m, "latency_median"]), f3(EP.loc[m, "pre_onset_share"]), f3(EP.loc[m, "ep_recall_m44"]),
               f3(err_(m, 0.44)["random_mean"]), f1(EP.loc[m, "latency_median_m44"]), f3(EP.loc[m, "pre_onset_share_m44"])]
              for m in ORDER])
pv = ASG.pivot(index="group", columns="model", values="a_sev")[ORDER]
pairs = ASG[ASG.model == "Clock"].set_index("group").pairs; nrec = S3B.groupby("group").recordings.max()
out["S6"] = (["Group", "Recordings", "Pairs"] + ORDER,
             [[str(g), str(int(nrec[g])), f"{int(pairs[g]):,}"] + [f3(pv.loc[g, m]) for m in ORDER] for g in pv.index])
CT_ = CT.sort_values(["kind", "delta"])
out["S7"] = (["Signal", "δ", "Replicates", "Detected, MCC Wilcoxon", "Detected, MCC t test", "Mean Δ fold AUC",
              "Mean Atime pooled", "Mean Atime LPGO", "Below reference, pooled", "Below reference, LPGO"],
             [[r_.kind, f"{r_.delta:g}", str(int(r_.reps)), pct(r_.power_w), pct(r_.power_t), sg(r_.dauc), f3(r_.tm_pooled),
               f3(r_.tm_lpo), pct(r_.below_pooled), pct(r_.below_lpo)] for r_ in CT_.itertuples()])

# ---------------------------------------------------------------- write
md = ["# Tables of the paper, regenerated from outputs/tables\n"]
for k, (hdr, rows) in out.items():
    pd.DataFrame(rows, columns=hdr).to_csv(PAPER / f"Table_{k}.csv", index=False)
    md += [f"\n## Table {k}\n", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    md += ["| " + " | ".join(r) + " |" for r in rows]
(PAPER / "PAPER_TABLES.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"{len(out)} tables written to {PAPER}")
