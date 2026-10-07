"""Step 11. Model fits of the primary design and of the sensitivity designs (about 30 minutes on 2 CPUs).

Writes one prediction file per configuration to outputs/predictions/ (columns: config, model, fold, participant,
session, y, sev, t, proba); a configuration is skipped when its file exists, so the step can be resumed.

  primary_clock, loro_clock, merged_clock   the clock (LR on elapsed time) under LOGO, LORO and the merged grouping
  primary                                   RF, GB, RF+GB, LR, MLP on the 76 primary features, LOGO (22 folds)
  full99                                    MLP with group based early stopping on the 99 features (Table S2)
  ablation_time, ablation_tel, ablation_tel_time   nested feature analysis (temporal figure, panel b) and
                                            the time only negative controls RF and GB
  leak_random_primary, leak_random_full99   RF under random window level 5 fold cross validation (leakage demo)
  merged, loro                              the panel under the merged grouping (20 folds) and LORO (35 folds)"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from csp.design import *          # noqa: F401,F403
if __name__ == "__main__":
    T0 = time.time()
    # clock: logistic regression on elapsed time only (feature set differs, so it is run separately)
    for tag, ids in [("primary_clock", pid), ("loro_clock", sess), ("merged_clock", merged)]:
        run(tag, ids, ["elapsed_in_session"], {"Clock": lr})
    panel = {"RF": rf, "GB": gb, "RF+GB": None, "LR": lr, "MLP": lambda g: GroupEarlyStopMLP(g)}
    run("primary", pid, PRIMARY, panel)
    run("full99", pid, cols, {"MLP": lambda g: GroupEarlyStopMLP(g)})   # MLP of the original set, fixed stopping
    run("ablation_time", pid, ["elapsed_in_session"], {"RF": rf, "GB": gb})
    run("ablation_tel", pid, TEL, {"RF": rf, "GB": gb, "LR": lr})
    run("ablation_tel_time", pid, TEL + ["elapsed_in_session"], {"RF": rf, "GB": gb, "LR": lr})
    rnd = list(KFold(5, shuffle=True, random_state=0).split(X))
    run("leak_random_primary", None, PRIMARY, {"RF": rf}, splits=rnd)
    run("leak_random_full99", None, cols, {"RF": rf}, splits=rnd)
    run("merged", merged, PRIMARY, panel)
    run("loro", sess, PRIMARY, panel)
    print("all done", f"{time.time() - T0:.0f}s", flush=True)
