"""Step 12. Training variance of the stochastic detectors (about 15 minutes on 2 CPUs).

The primary predictions use seed 42 for every stochastic component. Here RF, GB, RF+GB and MLP of the primary design
(76 features, 22 LOGO folds) are refitted with seeds 1 and 2 (random_state of RF, GB and MLP, and the seed of the MLP's
validation group split); LR and the clock have no random component. Every seed is scored with the code of the primary
tables and paired with the clock.
Outputs: outputs/predictions/P_primary_seed1.csv, P_primary_seed2.csv; outputs/tables/T_sup_seeds.csv."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from csp.design import *          # noqa: F401,F403


class SeededMLP(GroupEarlyStopMLP):
    def __init__(self, groups, seed): self.groups = groups; self.seed = seed

    def _net(self):
        return MLPClassifier(hidden_layer_sizes=(256, 128), max_iter=1, warm_start=True, random_state=self.seed)

    def fit(self, Xtr, ytr):
        import warnings
        from sklearn.exceptions import ConvergenceWarning
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        for s in range(self.seed * 1000, self.seed * 1000 + 100):
            tr, va = next(GroupShuffleSplit(1, test_size=0.15, random_state=s).split(Xtr, ytr, self.groups))
            if 0 < ytr[va].sum() < len(va) and 0 < ytr[tr].sum() < len(tr):
                break
        else:
            raise RuntimeError("no validation split with both classes in 100 seeds")
        net = self._net(); best, best_ep, wait = np.inf, 1, 0
        for ep in range(1, 151):
            net.fit(Xtr[tr], ytr[tr])
            ll = log_loss(ytr[va], net.predict_proba(Xtr[va])[:, 1], labels=[0, 1])
            if ll < best - 1e-4: best, best_ep, wait = ll, ep, 0
            else:
                wait += 1
                if wait >= 10: break
        self.epochs_ = best_ep; self.net = self._net()
        for _ in range(best_ep):
            self.net.fit(Xtr, ytr)
        return self

if __name__ == "__main__":
    for s in (1, 2):
        panel = {"RF": lambda s=s: RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample",
                                                          n_jobs=-1, random_state=s),
                 "GB": lambda s=s: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                                                  l2_regularization=1.0, class_weight="balanced", random_state=s),
                 "RF+GB": None, "MLP": lambda g, s=s: SeededMLP(g, s)}
        run(f"primary_seed{s}", pid, PRIMARY, panel)
    # score every seed with the table code
    from csp.metrics import *     # noqa: F401,F403  (scoring code of the primary tables)
    from scipy import stats as sps
    ck_ = load("primary_clock"); ck_["hard"] = np.nan; _, PFC = summarise(ck_, tm=False); ckf = PFC["Clock"]
    rows = []
    for s in (42, 1, 2):
        P = load("primary" if s == 42 else f"primary_seed{s}"); P = P[P.model.isin(["RF", "GB", "RF+GB", "MLP"])].copy()
        P["hard"] = np.nan; S, PF = summarise(P, tm=False); M = matched_alarm(P, 0.44).set_index("model")
        for _, r in S.iterrows():
            f = PF[r.model].loc[ckf.index]
            rows.append(dict(model=r.model, seed=s, mcc=r.mcc, rec=r.rec, spec=r.spec, pooled_alarm=r.pooled_alarm,
                             fa_all=r.fa_all, never_sick_alarm=r.never_sick_alarm, missed_s3=r.missed_s3,
                             missed_s3_m44=M.loc[r.model, "missed_s3"], fold_auc=r.fold_auc,
                             dmcc=(f - ckf).mean(), p_t=sps.ttest_rel(f, ckf).pvalue, p_w=sps.wilcoxon(f, ckf).pvalue))
    T = pd.DataFrame(rows); T.to_csv(TABLES / "T_sup_seeds.csv", index=False); print(T.round(3).to_string())
