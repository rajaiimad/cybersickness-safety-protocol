"""Step 30. The six figures of the paper, from outputs/tables (and the primary predictions for the fold values of
Fig. 3(a)). Every plotted value is read from the analysis outputs.

  fig1_protocol.png   Fig. 1  evaluation protocol (counts from T_dataset_facts.csv)
  fig2_leakage.png    Fig. 2  random window splitting against group disjoint evaluation (T_leakage, T_leakage_loro)
  fig3_primary.png    Fig. 3  primary comparison (T_primary, T_lpgo_atime, P_primary)
  fig4_severity.png   Fig. 4  severity at controlled operating points (CURVE_s3_vs_alarm, T_asev_paired, T_asev_by_group)
  fig5_temporal.png   Fig. 5  smoothing window and nested feature analysis (T_smoothing, T_ablation, T_original99)
  fig6_controls.png   Fig. 6  positive and negative controls (T_lpgo_atime, T_controls)

Usage: python pipeline/30_figures.py [1 2 3 4 5 6]   (default: all)
Note: Fig. 2 of the submitted manuscript was drawn separately with the same values; this script redraws it from the
tables in a matching style. Figures 1 and 3 to 6 are byte for byte the ones in the manuscript when run with the
same matplotlib version."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D
import pandas as pd, numpy as np

from csp.paths import TABLES, PRED, FIGS as OUT

DF = pd.read_csv(TABLES / "T_dataset_facts.csv").set_index("name").value
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300, "axes.edgecolor": "#52514e",
                     "axes.labelcolor": "#0b0b0b", "xtick.color": "#52514e", "ytick.color": "#52514e"})
# validated categorical order (dataviz reference palette, slots 1 to 5); the clock is the neutral reference
COL = {"RF": "#2a78d6", "GB": "#eb6834", "RF+GB": "#1baf7a", "LR": "#eda100", "MLP": "#e87ba4", "Clock": "#52514e"}
DET = ["RF", "GB", "RF+GB", "LR", "MLP"]; ORDER = DET + ["Clock"]
GRID = dict(color="#d9d8d4", lw=0.5)
which = set(sys.argv[1:]) or {"1", "2", "3", "4", "5", "6"}


def tag(ax, s, x=-0.14):
    ax.text(x, 1.04, s, transform=ax.transAxes, fontsize=9, fontweight="bold")


def fold_mcc(g):
    s_ = g.groupby("session").proba.transform(lambda x: x.rolling(61, min_periods=1).mean()); pr_ = (s_ >= 0.5).astype(int)
    out = {}
    for f_, gg in g.assign(pr=pr_).groupby("participant"):
        yy, pp = gg.y.values, gg.pr.values
        if 0 < yy.sum() < len(yy):
            TP = ((pp == 1) & (yy == 1)).sum(); TN = ((pp == 0) & (yy == 0)).sum()
            FP = ((pp == 1) & (yy == 0)).sum(); FN = ((pp == 0) & (yy == 1)).sum()
            den = np.sqrt(float(TP + FP) * (TP + FN) * (TN + FP) * (TN + FN)); out[f_] = (TP * TN - FP * FN) / den if den else 0.0
    return pd.Series(out)


# ---------------- Figure 1: protocol ----------------
if "1" in which:
    stages = [
        ("Public VR gameplay dataset", f"{int(DF['windows']):,} windows, {int(DF['recordings'])} recordings, four severity levels", "#f2f2f2", "#7f7f7f"),
        ("Participant group and recording recovery", f"{int(DF['participant_groups'])} descriptor defined groups; archive start times checked", "#e3ecf7", "#2a78d6"),
        ("Group disjoint evaluation", f"leave one participant group out: {int(DF['participant_groups'])} folds, {int(DF['groups_with_both_classes'])} with both classes", "#e3ecf7", "#2a78d6"),
        ("Past only features, unit variables excluded", f"{int(DF['features_primary'])} features; participant descriptor indicators left out", "#e3ecf7", "#2a78d6"),
        ("Training only preprocessing", "robust scaling fitted on training groups; no oversampling", "#e3ecf7", "#2a78d6"),
        ("Five detectors and an elapsed time clock", "RF, GB, RF+GB, LR, MLP; the clock is the reference", "#eeecf6", "#4a3aa7"),
        ("One prespecified operating rule", "trailing mean over w = 61 windows, threshold τ = 0.5, for all", "#eeecf6", "#4a3aa7"),
        ("Comparison with elapsed time", "fold MCC against the clock; time matched AUC scored with LPGO models", "#e6f3ea", "#008300"),
        ("Safety and deployment endpoints", "false alarms in all groups; severity at a matched alarm rate; prevalence", "#e6f3ea", "#008300"),
        ("Controls and sensitivity", "synthetic signals, time only models; 99 features, LORO, nested w", "#fcebe4", "#eb6834"),
    ]
    fig, ax = plt.subplots(figsize=(4.6, 6.2)); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    n = len(stages); top = 9.6; step = 9.2 / (n - 1); h = 0.74; ys = []
    for i, (t1, t2, fc, ec) in enumerate(stages):
        y = top - i * step; ys.append(y)
        ax.add_patch(FancyBboxPatch((0.8, y - h / 2), 9.1, h, boxstyle="round,pad=0.02,rounding_size=0.12", lw=0.9,
                                    edgecolor=ec, facecolor=fc))
        ax.text(5.35, y + 0.13, t1, ha="center", va="center", fontsize=7.6, fontweight="bold", color="#0b0b0b")
        ax.text(5.35, y - 0.18, t2, ha="center", va="center", fontsize=6.3, color="#333333")
    for i in range(n - 1):
        ax.add_patch(FancyArrowPatch((5.35, ys[i] - h / 2), (5.35, ys[i + 1] + h / 2), arrowstyle="-|>",
                                     mutation_scale=7, lw=0.8, color="#555555"))
    ax.plot([0.45, 0.45], [ys[1] + h / 2, ys[4] - h / 2], color="#2a78d6", lw=0.9)
    ax.text(0.2, (ys[1] + ys[4]) / 2, "leakage control", rotation=90, ha="center", va="center", fontsize=7,
            color="#2a78d6", style="italic")
    fig.savefig(OUT / "fig1_protocol.png", bbox_inches="tight", pad_inches=0.02); plt.close(fig)

# ---------------- Figure 2: leakage demonstration ----------------
if "2" in which:
    LK = pd.read_csv(TABLES / "T_leakage.csv").set_index("split"); LL = pd.read_csv(TABLES / "T_leakage_loro.csv").iloc[0]
    rnd76, logo76 = LK.loc["random 5 fold, 76 features"], LK.loc["group disjoint, 76 features"]
    rnd99, logo99 = LK.loc["random 5 fold, 99 features"], LK.loc["group disjoint, 99 features"]
    STY = [("Random 5 fold (windows)", "#b01c2e", None), ("Leave one recording out", "#8c8c8c", "//"),
           ("Leave one group out", "#2166ac", ".")]
    with plt.rc_context({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                         "font.size": 9, "hatch.linewidth": 0.8}):
        fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.25, 0.8]})
        a = ax[0]; metrics = [("Accuracy", "acc"), ("MCC", "mcc"), ("AUC", "auc")]; bw = 0.26
        for j, (vals, (lab, col, hat)) in enumerate(zip([rnd76, LL, logo76], STY)):
            for i, (_, k) in enumerate(metrics):
                v = float(vals[k]); x = i + (j - 1) * bw
                a.bar(x, v, bw, color=col, edgecolor="black", linewidth=0.6, hatch=hat, label=lab if i == 0 else None)
                a.text(x, v + 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=7)
        a.set_xticks(range(3)); a.set_xticklabels([m for m, _ in metrics]); a.set_ylim(0, 1.12)
        a.set_ylabel("Value (pooled held out windows)"); a.set_title("(a) RF, 76 features", fontsize=9)
        a = ax[1]; bw = 0.36
        for j, ((r, lg), (lab, col, hat)) in enumerate(zip([((rnd76, rnd99), 0), ((logo76, logo99), 2)], [STY[0], STY[2]])):
            for i, v in enumerate([float(r[0]["mcc"]), float(r[1]["mcc"])]):
                x = i + (j - 0.5) * bw
                a.bar(x, v, bw, color=col, edgecolor="black", linewidth=0.6, hatch=hat)
                a.text(x, v + 0.015, f"{v:.3f}", ha="center", va="bottom", fontsize=7)
        a.set_xticks(range(2)); a.set_xticklabels(["76 features", "99 features"]); a.set_ylim(0, 1.12)
        a.set_ylabel("MCC"); a.set_title("(b) MCC by feature representation", fontsize=9)
        for a in ax:
            a.grid(axis="y", color="#d9d8d4", lw=0.5); a.set_axisbelow(True)
        fig.legend(*ax[0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False, fontsize=8,
                   bbox_to_anchor=(0.5, -0.04))
        fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=2.0)
        fig.savefig(OUT / "fig2_leakage.png", bbox_inches="tight", pad_inches=0.03); plt.close(fig)

# ---------------- Figure 3: primary panel ----------------
if "3" in which:
    S = pd.read_csv(TABLES / "T_primary.csv").set_index("model").loc[ORDER]
    LA = pd.read_csv(TABLES / "T_lpgo_atime.csv").set_index("model")
    P_ = pd.concat([pd.read_csv(PRED / "P_primary.csv"), pd.read_csv(PRED / "P_primary_clock.csv")], ignore_index=True)
    FMC = {m: fold_mcc(g) for m, g in P_.groupby("model")}
    for m in ORDER: assert abs(FMC[m].mean() - S.loc[m, "mcc"]) < 1e-9, m
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.7))
    x = np.arange(len(ORDER)); cols = [COL[m] for m in ORDER]; rng_ = np.random.default_rng(1)
    a = ax[0]; v = S.mcc.values
    a.bar(x, v, color=cols, width=0.66, edgecolor="white", linewidth=0.8)
    for i, m in enumerate(ORDER):
        a.scatter(i + rng_.uniform(-0.2, 0.2, len(FMC[m])), FMC[m].values, s=5, color="#0b0b0b", zorder=3, lw=0)
    a.errorbar(x, v, yerr=S.mcc_ci.values, fmt="none", ecolor="#0b0b0b", elinewidth=0.8, capsize=2, zorder=4)
    a.axhline(S.loc["Clock", "mcc"], color=COL["Clock"], ls=":", lw=0.9)
    a.set_ylabel("MCC, 16 two class folds"); tag(a, "(a)")
    a = ax[1]; ref = LA.tm_ref.iloc[0]
    for i, m in enumerate(DET):
        r = LA.loc[m]
        a.errorbar(i - 0.13, r.tm_lpo, yerr=[[r.tm_lpo - r.tm_lpo_lo], [r.tm_lpo_hi - r.tm_lpo]], fmt="o", ms=5,
                   color=COL[m], mec="#0b0b0b", mew=0.4, elinewidth=0.9, capsize=2)
        a.errorbar(i + 0.13, r.tm_pooled, yerr=[[r.tm_pooled - S.loc[m, "tm_lo"]], [S.loc[m, "tm_hi"] - r.tm_pooled]],
                   fmt="o", ms=5, mfc="white", color=COL[m], mew=1.0, elinewidth=0.9, capsize=2)
        assert abs(r.tm_pooled - S.loc[m, "tm_auc"]) < 1e-9
    rr = LA.iloc[0]
    a.errorbar(5, ref, yerr=[[ref - rr.tm_ref_lo], [rr.tm_ref_hi - ref]], fmt="s", ms=5, color=COL["Clock"],
               elinewidth=0.9, capsize=2)
    a.axhline(ref, color=COL["Clock"], ls=":", lw=0.9); a.axhline(0.5, color="#b0aea8", ls="--", lw=0.7)
    a.set_ylabel("Time matched AUC, $A_{time}$"); tag(a, "(b)")
    a.legend(handles=[Line2D([], [], marker="o", ls="", color="#52514e", ms=5, label="LPGO"),
                      Line2D([], [], marker="o", ls="", mfc="white", color="#52514e", ms=5, label="pooled LOGO"),
                      Line2D([], [], marker="s", ls="", color="#52514e", ms=5, label="elapsed time")],
             fontsize=6.3, frameon=False, loc="upper right")
    a = ax[2]; v = S.fa_all.values
    a.bar(x, v, color=cols, width=0.66, edgecolor="white", linewidth=0.8)
    a.errorbar(x, v, yerr=S.fa_all_ci.values, fmt="none", ecolor="#0b0b0b", elinewidth=0.8, capsize=2)
    a.axhline(S.loc["Clock", "fa_all"], color=COL["Clock"], ls=":", lw=0.9)
    a.set_ylabel("False alarm rate, all 22 groups"); tag(a, "(c)")
    for a in ax:
        a.set_xticks(x); a.set_xticklabels(ORDER, rotation=40, ha="right", fontsize=7); a.grid(axis="y", **GRID)
        a.set_axisbelow(True)
    fig.tight_layout(w_pad=1.4); fig.savefig(OUT / "fig3_primary.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

# ---------------- Figure 4: severity ----------------
if "4" in which:
    C = pd.read_csv(TABLES / "CURVE_s3_vs_alarm.csv"); S = pd.read_csv(TABLES / "T_primary.csv").set_index("model")
    AS = pd.read_csv(TABLES / "T_asev_paired.csv").set_index("model"); G = pd.read_csv(TABLES / "T_asev_by_group.csv")
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.3, 1.0]})
    a = ax[0]
    for m in ORDER:
        c = C[C.model == m].sort_values("alarm")
        a.plot(c.alarm, c.missed_s3, lw=1.3, color=COL[m], label=m, ls=":" if m == "Clock" else "-")
        a.plot(S.loc[m, "pooled_alarm"], S.loc[m, "missed_s3"], "o", color=COL[m], ms=4.5, mec="white", mew=0.8)
    a.axvline(0.44, color="#8a8984", ls="--", lw=0.7)
    a.set_xlabel("Pooled alarm rate (threshold swept without labels)"); a.set_ylabel("Missed severity 3 windows (of 821)")
    a.legend(fontsize=6.5, frameon=False, ncol=2, loc="upper right"); a.grid(**GRID); a.set_axisbelow(True); tag(a, "(a)", -0.12)
    a = ax[1]; ck = G[G.model == "Clock"].set_index("group"); wmax = ck.pairs.max()
    for i, m in enumerate(DET):
        g = G[G.model == m].set_index("group"); dlt = g.a_sev - ck.a_sev
        a.scatter(np.full(len(dlt), i) + np.linspace(-0.18, 0.18, len(dlt)), dlt.values, s=8 + 60 * ck.pairs / wmax,
                  color=COL[m], alpha=0.75, edgecolors="white", linewidths=0.5, zorder=3)
        r = AS.loc[m]
        a.errorbar(i + 0.3, r.d_pooled, yerr=[[r.d_pooled - r.d_lo], [r.d_hi - r.d_pooled]], fmt="D", ms=4,
                   color="#0b0b0b", elinewidth=0.8, capsize=1.5, zorder=4)
        a.errorbar(i + 0.42, r.d_equal, yerr=[[r.d_equal - r.de_lo], [r.de_hi - r.d_equal]], fmt="s", ms=4, mfc="white",
                   color="#0b0b0b", elinewidth=0.8, capsize=1.5, zorder=4)
    a.axhline(0, color="#52514e", lw=0.8)
    a.set_xticks(range(len(DET))); a.set_xticklabels(DET, rotation=40, ha="right", fontsize=7)
    a.set_ylabel("$A_{sev}$, detector minus clock"); a.grid(axis="y", **GRID); a.set_axisbelow(True); tag(a, "(b)", -0.2)
    a.legend(handles=[Line2D([], [], marker="o", ls="", color="#8a8984", ms=5, label="per group"),
                      Line2D([], [], marker="D", ls="", color="#0b0b0b", ms=4, label="pair weighted"),
                      Line2D([], [], marker="s", ls="", mfc="white", color="#0b0b0b", ms=4, label="equal weights")],
             fontsize=6.3, frameon=False, loc="lower left")
    fig.tight_layout(w_pad=1.6); fig.savefig(OUT / "fig4_severity.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

# ---------------- Figure 5: temporal ----------------
if "5" in which:
    S = pd.read_csv(TABLES / "T_primary.csv").set_index("model"); SW = pd.read_csv(TABLES / "T_smoothing.csv")
    AB = pd.read_csv(TABLES / "T_ablation.csv"); O = pd.read_csv(TABLES / "T_original99.csv").set_index("model")
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
    a = ax[0]
    for m in ORDER:
        s = SW[SW.model == m].sort_values("w")
        a.plot(s.w, s.mcc, marker="o", lw=1.3, ms=3.5, color=COL[m], label=m, ls=":" if m == "Clock" else "-")
    a.axvline(61, ls="--", color="#8a8984", lw=0.8); a.set_xscale("log"); a.set_xticks([1, 15, 31, 61, 121, 201])
    a.set_xticklabels(["1", "15", "31", "61", "121", "201"]); a.minorticks_off()
    a.set_xlabel("Trailing smoothing window w (log scale)"); a.set_ylabel("MCC, 16 two class folds")
    a.legend(fontsize=6.5, frameon=False, ncol=3, loc="lower left"); a.grid(**GRID); a.set_axisbelow(True); tag(a, "(a)", -0.13)
    cfg = [("time", "Elapsed time"), ("tel", "Telemetry"), ("tel_time", "Telemetry + time"), ("primary", "Primary (76)"),
           ("full", "Full (99)")]
    shade = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]      # sequential blue, ordinal steps
    a = ax[1]
    for j, m in enumerate(["RF", "GB", "LR"]):
        for i, (k, lab) in enumerate(cfg):
            if k == "time":
                if m == "LR": mu, ci = S.loc["Clock", "mcc"], S.loc["Clock", "mcc_ci"]
                else:
                    r = AB[(AB.config == "ablation_time") & (AB.model == m)].iloc[0]; mu, ci = r.mcc, r.mcc_ci
            elif k in ("tel", "tel_time"):
                r = AB[(AB.config == f"ablation_{k}") & (AB.model == m)].iloc[0]; mu, ci = r.mcc, r.mcc_ci
            elif k == "primary": mu, ci = S.loc[m, "mcc"], S.loc[m, "mcc_ci"]
            else: mu, ci = O.loc[m, "mcc"], O.loc[m, "mcc_ci"]
            xx = j * 6 + i
            a.bar(xx, mu, color=shade[i], width=0.86, label=lab if j == 0 else None, edgecolor="white", linewidth=0.6)
            a.errorbar(xx, mu, yerr=ci, fmt="none", ecolor="#0b0b0b", elinewidth=0.7, capsize=1.5)
    a.set_xticks([2, 8, 14]); a.set_xticklabels(["RF", "GB", "LR"]); a.set_ylabel("MCC, 16 two class folds")
    a.grid(axis="y", **GRID); a.set_axisbelow(True); a.set_ylim(0, 0.85)
    a.legend(fontsize=6.3, frameon=False, ncol=3, loc="upper center"); tag(a, "(b)", -0.13)
    fig.tight_layout(w_pad=1.6); fig.savefig(OUT / "fig5_temporal.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)

# ---------------- Figure 6: controls ----------------
if "6" in which:
    LA = pd.read_csv(TABLES / "T_lpgo_atime.csv").set_index("model"); CT = pd.read_csv(TABLES / "T_controls.csv")
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.7), gridspec_kw={"width_ratios": [0.9, 1.0, 1.0]})
    a = ax[0]; NEG = ["Clock", "RF time only", "GB time only"]
    labs = ["Clock\n(LR, time)", "RF,\ntime only", "GB,\ntime only"]
    for i, m in enumerate(NEG):
        r = LA.loc[m]
        a.errorbar(i - 0.12, r.d_pooled, yerr=[[r.d_pooled - r.d_pooled_lo], [r.d_pooled_hi - r.d_pooled]], fmt="o",
                   ms=5, mfc="white", color="#52514e", mew=1.0, elinewidth=0.9, capsize=2)
        a.errorbar(i + 0.12, r.d_lpo, yerr=[[r.d_lpo - r.d_lpo_lo], [r.d_lpo_hi - r.d_lpo]], fmt="o", ms=5,
                   color="#2a78d6", elinewidth=0.9, capsize=2)
    a.axhline(0, color="#52514e", lw=0.8)
    a.set_xticks(range(3)); a.set_xticklabels(labs, fontsize=6.6); a.set_xlim(-0.5, 2.5)
    a.set_ylabel("$A_{time}$ minus elapsed time"); a.grid(axis="y", **GRID); a.set_axisbelow(True)
    a.legend(handles=[Line2D([], [], marker="o", ls="", mfc="white", color="#52514e", ms=5, label="pooled LOGO"),
                      Line2D([], [], marker="o", ls="", color="#2a78d6", ms=5, label="LPGO")],
             fontsize=6.3, frameon=False, loc="lower right"); tag(a, "(a)", -0.25)
    TESTS = [("power_t", "MCC, paired $t$ test", "#eb6834", "^", "-"), ("power_pooled", "$A_{time}$, pooled LOGO", "#8a8984", "o", "--"),
             ("power_lpo", "$A_{time}$, LPGO", "#2a78d6", "o", "-")]
    for a, kind, lab in [(ax[1], "state", "(b)"), (ax[2], "trait", "(c)")]:
        c = CT[CT.kind == kind].sort_values("delta")
        for k, name, col, mk, ls in TESTS:
            a.plot(c.delta, c[k], marker=mk, ms=4, lw=1.3, color=col, ls=ls, label=name,
                   mfc="white" if k == "power_pooled" else col)
        a.plot(c.delta, c["power_cal"], marker="o", ms=3, lw=1.1, color="#2a78d6", ls=":", mfc="white",
               label="$A_{time}$, LPGO, calibrated")
        a.axhline(0.025, color="#b0aea8", ls=":", lw=0.8); a.axhline(0.8, color="#b0aea8", ls="--", lw=0.7)
        a.set_ylim(-0.02, 1.02); a.set_xlabel(f"Signal strength δ ({kind} signal)")
        a.set_ylabel("Share of replicates detected"); a.grid(**GRID); a.set_axisbelow(True); tag(a, lab, -0.2)
    ax[2].legend(handles=ax[1].get_legend_handles_labels()[0], labels=ax[1].get_legend_handles_labels()[1],
                 fontsize=6.3, frameon=False, loc="upper left")
    fig.tight_layout(w_pad=1.3); fig.savefig(OUT / "fig6_controls.png", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
print("figures written", sorted(which))
