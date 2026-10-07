"""Additional evaluation functions: paired fold AUC, the circularly shifted alarm reference for episode recall,
the leave one group out range of A_sev, and severity 3 misses per group. Works on saved predictions."""
from csp.metrics import *          # noqa: F401,F403  (shared definitions: trailing, load, W, TAU, ...)

ORDER = ["RF", "GB", "RF+GB", "LR", "MLP", "Clock"]


def fold_auc(P):
    out = {}
    for name, g in P.groupby("model", sort=False):
        g = g.reset_index(drop=True); s = trailing(g.proba.values, g.session.values, W)
        out[name] = pd.Series({f: roc_auc_score(g.y.values[i], s[i]) for f, i in g.groupby("fold").groups.items()
                               if 0 < g.y.values[i].sum() < len(i)})
    return pd.DataFrame(out)


def episode_list(y, sess):
    E = []
    for s_ in np.unique(sess):
        idx = np.where(sess == s_)[0]; yy = y[idx]; i = 0
        while i < len(yy):
            if yy[i] == 1:
                j = i
                while j + 1 < len(yy) and yy[j + 1] == 1: j += 1
                E.append((idx[i], idx[j])); i = j + 1
            else: i += 1
    return E


def ep_recall(pred, E): return np.mean([pred[a:b + 1].any() for a, b in E])


def random_reference(P, target=None, B=500, seed=0):
    rng = np.random.default_rng(seed); rows = []
    for name, g in P.groupby("model", sort=False):
        g = g.reset_index(drop=True); s = trailing(g.proba.values, g.session.values, W)
        pred = (s >= (TAU if target is None else np.quantile(s, 1 - target))).astype(int)
        sess = g.session.values; E = episode_list(g.y.values, sess)
        groups = [np.where(sess == s_)[0] for s_ in np.unique(sess)]
        obs = ep_recall(pred, E); sim = []
        for _ in range(B):
            q = pred.copy()
            for idx in groups: q[idx] = np.roll(pred[idx], rng.integers(len(idx)))
            sim.append(ep_recall(q, E))
        rows.append(dict(model=name, target=target, alarm=pred.mean(), ep_recall=obs, random_mean=np.mean(sim),
                         random_lo=np.percentile(sim, 2.5), random_hi=np.percentile(sim, 97.5),
                         p_above=np.mean(np.array(sim) >= obs)))
    return pd.DataFrame(rows)


def a_sev_jackknife(P):
    rows = []
    for name, g in P.groupby("model", sort=False):
        g = g.reset_index(drop=True); s = trailing(g.proba.values, g.session.values, W); per = {}
        for grp, idx in g.groupby("participant").groups.items():
            s3 = s[idx][g.sev.values[idx] == 3]; s1 = s[idx][g.sev.values[idx] == 1]
            if len(s3) and len(s1):
                d_ = s3[:, None] - s1[None, :]; per[grp] = ((d_ > 0).sum() + 0.5 * (d_ == 0).sum(), d_.size)
        full = sum(v[0] for v in per.values()) / sum(v[1] for v in per.values())
        jk = [sum(per[k][0] for k in per if k != drop) / sum(per[k][1] for k in per if k != drop) for drop in per]
        rows.append(dict(model=name, a_sev=full, jk_min=min(jk), jk_max=max(jk), groups=len(per)))
    return pd.DataFrame(rows)


def s3_by_group(P, target=0.44):
    rows = []
    for name, g in P.groupby("model", sort=False):
        g = g.reset_index(drop=True); s = trailing(g.proba.values, g.session.values, W)
        for lab, pred in [("primary", (s >= TAU).astype(int)), ("m44", (s >= np.quantile(s, 1 - target)).astype(int))]:
            for grp, idx in g.groupby("participant").groups.items():
                n3 = int((g.sev.values[idx] == 3).sum())
                if n3: rows.append(dict(model=name, rule=lab, group=grp, n_s3=n3,
                                        missed_s3=int(((g.sev.values[idx] == 3) & (pred[idx] == 0)).sum()),
                                        recordings=g.session.values[idx].__len__() and len(np.unique(g.session.values[idx]))))
    return pd.DataFrame(rows)

