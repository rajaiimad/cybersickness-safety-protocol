"""Step 25. Time matched AUC with leave pair of groups out (LPGO) scoring, from the pair model predictions of step 15
and the LOGO predictions of step 11 (no model is fitted).

For every detector: A_time under LPGO and under pooled LOGO scoring, each minus elapsed time itself, with one set of
1,000 group bootstrap resamples shared by all detectors (closed form, csp.inference.ATime), 95% intervals and
Bonferroni intervals at level 1 - 0.05/5. Negative controls: the clock and RF and GB fitted on elapsed time alone.
Output: outputs/tables/T_lpgo_atime.csv (Tables III and IV, time matched columns; controls figure, panel a)."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import glob
from csp.inference import *       # noqa: F401,F403
from csp.paths import LPGO
if __name__ == "__main__":
    ck_ = load("primary_clock"); ck_["hard"] = np.nan; clk = ck_.reset_index(drop=True)
    y = clk.y.values; t = clk.t.values.astype(float); pid = clk.participant.values; sess = clk.session.values
    AT = ATime(y, t, pid); ones = np.ones(len(AT.ug)); MB = boot_multiplicities(AT.ug, 1000, 0)
    Cref = AT.tables(t); ref = AT.value(Cref, ones); ref_b = np.array([AT.value(Cref, m_) for m_ in MB])
    files = sorted(glob.glob(str(LPGO / "pair_*.csv")))
    haspos = set(np.unique(pid[y == 1])); ug = np.unique(pid)
    need = [(g, h) for i, g in enumerate(ug) for h in ug[i + 1:] if g in haspos or h in haspos]
    assert len(files) == len(need) == 216, (len(files), len(need))
    # LOGO scores (canonical order) of every model, including the time only negative controls
    prim = load("primary"); prim["hard"] = np.nan; tonly = load("ablation_time"); tonly["hard"] = np.nan
    LOGO = aligned_scores(prim, clk); LOGO["Clock"] = aligned_scores(ck_, clk)["Clock"]
    to = aligned_scores(tonly, clk); LOGO["RF time only"] = to["RF"]; LOGO["GB time only"] = to["GB"]
    MODELS = SUP + ["Clock", "RF time only", "GB time only"]
    pos_of = {g: np.where(pid == g)[0] for g in ug}
    PAIR = {m: {} for m in MODELS}
    for f in files:
        Pp = pd.read_csv(f); g, h = int(Pp.pair_g.iloc[0]), int(Pp.pair_h.iloc[0])
        idx = np.concatenate([pos_of[g], pos_of[h]])
        for m in MODELS:
            q = Pp[Pp.model == m]
            q = pd.concat([q[q.participant == g], q[q.participant == h]])
            assert (q.y.values == y[idx]).all() and np.allclose(q.t.values, t[idx])
            v = np.full(len(y), np.nan); v[idx] = trailing(q.proba.values, sess[idx], W); PAIR[m][(g, h)] = v
    rows = []; a2 = 0.05 / len(SUP) / 2
    for m in MODELS:
        Cl = AT.tables_lpo(LOGO[m], PAIR[m]); Cp = AT.tables(LOGO[m])
        el = AT.value(Cl, ones); ep = AT.value(Cp, ones)
        bl = np.array([AT.value(Cl, m_) for m_ in MB]); bp = np.array([AT.value(Cp, m_) for m_ in MB])
        dl, dp = bl - ref_b, bp - ref_b
        rows.append(dict(model=m, tm_lpo=el, tm_lpo_lo=np.percentile(bl, 2.5), tm_lpo_hi=np.percentile(bl, 97.5),
                         d_lpo=el - ref, d_lpo_lo=np.percentile(dl, 2.5), d_lpo_hi=np.percentile(dl, 97.5),
                         d_lpo_lo_bonf=np.percentile(dl, 100 * a2), d_lpo_hi_bonf=np.percentile(dl, 100 * (1 - a2)),
                         tm_pooled=ep, d_pooled=ep - ref, d_pooled_lo=np.percentile(dp, 2.5),
                         d_pooled_hi=np.percentile(dp, 97.5), tm_ref=ref, tm_ref_lo=np.percentile(ref_b, 2.5),
                         tm_ref_hi=np.percentile(ref_b, 97.5)))
    T = pd.DataFrame(rows)
    S8 = pd.read_csv(TABLES / "T_primary_stats.csv").set_index("model")
    for m in SUP:        # the pooled column must equal the primary statistics (same estimator, same draws)
        r = T.set_index("model").loc[m]; assert abs(r.tm_pooled - S8.loc[m, "tm_auc"]) < 1e-9 and abs(r.d_pooled_lo - S8.loc[m, "tm_dlo"]) < 1e-9
    T.to_csv(TABLES / "T_lpgo_atime.csv", index=False); print(T.round(3).to_string())
