"""Inference library for the paired comparisons with the clock and with elapsed time:
  ATime                closed form group bootstrap of the time matched AUC (Supporting Information Note S1); it equals
                       the resampling estimator csp.metrics.time_matched_auc on the same draws
  boot_multiplicities  the shared group bootstrap draws (multiplicity of each group in each resample)
  bh                   Benjamini-Hochberg adjustment
  n_needed             number of two class groups needed for a paired t test to reach a power at a true difference
  aligned_scores       smoothed scores of each model in a common row order (checked label by label)"""
import numpy as np, pandas as pd
from scipy import stats as sps
from sklearn.metrics import roc_auc_score
from csp.metrics_extra import *    # noqa: F401,F403

SUP = ["RF", "GB", "RF+GB", "LR", "MLP"]; K5 = len(SUP)


# ------------------------------------------------------------------ closed form group bootstrap of A_time
class ATime:
    """A_time = sum over bins b with >= 20 positives and >= 20 negatives of (sum of within bin pair scores) divided by
    the number of within bin pairs. Under a group bootstrap with multiplicities m (group g drawn m_g times) every
    positive window of group g meets every negative window of group h m_g * m_h times, so the resampled numerator of
    bin b is m' C_b m and its pair count m' N_b m, with C_b[g, h] the pair score sum between the positives of g and
    the negatives of h (1 for a higher score, 1/2 for a tie) and N_b[g, h] the pair count. This equals the estimator
    on the concatenated resample, which is what roc_auc_score computes (ties count one half)."""

    def __init__(self, y, t, groups, bin_s=BIN):
        self.y = np.asarray(y).astype(int); self.b = (np.asarray(t) // bin_s).astype(int)
        self.ug = np.unique(groups); self.gi = np.searchsorted(self.ug, groups); G = len(self.ug)
        self.bins = np.unique(self.b)
        self.npos = np.zeros((len(self.bins), G)); self.nneg = np.zeros((len(self.bins), G))
        for k, bb in enumerate(self.bins):
            m = self.b == bb
            self.npos[k] = np.bincount(self.gi[m & (self.y == 1)], minlength=G)
            self.nneg[k] = np.bincount(self.gi[m & (self.y == 0)], minlength=G)

    def tables(self, s):
        G = len(self.ug); C = np.zeros((len(self.bins), G, G)); s = np.asarray(s, float)
        for k, bb in enumerate(self.bins):
            m = self.b == bb; neg_by = {}
            for h in range(G):
                v = np.sort(s[m & (self.y == 0) & (self.gi == h)])
                if len(v): neg_by[h] = v
            pm = m & (self.y == 1)
            for g in np.unique(self.gi[pm]):
                sp = s[pm & (self.gi == g)]
                for h, v in neg_by.items():
                    lo = np.searchsorted(v, sp, "left"); hi = np.searchsorted(v, sp, "right")
                    C[k, g, h] = lo.sum() + 0.5 * (hi - lo).sum()
        return C

    def tables_lpo(self, s_logo, pair_s):
        """Leave pair of groups out: positives of g against negatives of h (g != h) use the scores of the model
        trained without both groups, pair_s[(min, max)] = full length array (NaN outside the two groups); within
        group pairs use the LOGO scores s_logo."""
        G = len(self.ug); C = np.zeros((len(self.bins), G, G)); s_logo = np.asarray(s_logo, float)
        for k, bb in enumerate(self.bins):
            m = self.b == bb
            for g in np.unique(self.gi[m & (self.y == 1)]):
                pm = m & (self.y == 1) & (self.gi == g)
                for h in np.unique(self.gi[m & (self.y == 0)]):
                    nm = m & (self.y == 0) & (self.gi == h)
                    s = s_logo if g == h else pair_s[(self.ug[min(g, h)], self.ug[max(g, h)])]
                    v = np.sort(s[nm]); sp = s[pm]
                    assert not (np.isnan(v).any() or np.isnan(sp).any())
                    lo = np.searchsorted(v, sp, "left"); hi = np.searchsorted(v, sp, "right")
                    C[k, g, h] = lo.sum() + 0.5 * (hi - lo).sum()
        return C

    def value(self, C, mult):
        mult = np.asarray(mult, float)
        P = self.npos @ mult; N = self.nneg @ mult; keep = (P >= 20) & (N >= 20)
        num = np.einsum("g,kgh,h->k", mult, C, mult)
        den = (self.npos @ mult) * (self.nneg @ mult)
        return num[keep].sum() / den[keep].sum()


def boot_multiplicities(ug, B=1000, seed=0):
    """Same draws as the resampling code: rng.choice(ug, len(ug)) once per resample."""
    rng = np.random.default_rng(seed); M = np.zeros((B, len(ug)))
    for i in range(B):
        M[i] = np.bincount(np.searchsorted(ug, rng.choice(ug, len(ug))), minlength=len(ug))
    return M


def bh(p):
    p = np.asarray(p, float); k = len(p); o = np.argsort(p); adj = np.empty(k); prev = 1.0
    for i in range(k - 1, -1, -1):
        prev = min(prev, p[o[i]] * k / (i + 1)); adj[o[i]] = prev
    return adj


def n_needed(sd, delta, power=0.80, alpha=0.05):
    """Smallest number of two class units for a paired t test to reach the power at a true mean difference delta."""
    for n in range(3, 5000):
        if (sps.t.ppf(1 - alpha / 2, n - 1) + sps.t.ppf(power, n - 1)) * sd / np.sqrt(n) <= delta: return n
    return np.nan


def aligned_scores(P, order_df):
    """Trailing mean scores of each model, in the row order of order_df (checked label by label)."""
    out = {}
    for m, g in P.groupby("model", sort=False):
        g = pd.concat([g[g.participant == p] for p in order_df.participant.unique()]).reset_index(drop=True)
        assert (g.y.values == order_df.y.values).all() and np.allclose(g.t.values, order_df.t.values)
        out[m] = trailing(g.proba.values, g.session.values, W)
    return out


def fold_mcc(P):
    _, PF = summarise(P, tm=False); return PF

