"""Runs the pipeline in order and stops at the first failure.

  python run_all.py            fast path (about 6 minutes): every table, paper table and figure is recomputed from the
                               shipped window level predictions in outputs/predictions, then verified (step 40)
  python run_all.py --full     full reproduction from the raw data (about 3.5 hours on 2 CPUs): download, every model
                               fit, the 216 LPGO pair models and the 2,400 control replicates, then all tables,
                               figures and the verification. Use a fresh output directory so that the shipped outputs
                               stay available for comparison:
                                   CSP_OUTPUTS=/tmp/csp_refit python run_all.py --full
  python run_all.py --from 20  start at a given step (fast path); --only 30 runs a single step

Every step skips a model fit whose prediction file already exists, so an interrupted --full run can be restarted
with the same command."""
import argparse, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
P = ROOT / "pipeline"
FAST = [("01_dataset_facts.py", []), ("02_archive_linkage.py", []),
        ("12_fit_seeds.py", []), ("13_fit_nested.py", []), ("16_controls.py", ["summary"]),
        ("20_tables.py", []), ("21_tables_extra.py", []), ("22_loro_diagnostic.py", []), ("23_constants.py", []),
        ("24_primary_statistics.py", []), ("25_lpgo_statistics.py", []), ("26_secondary_tests.py", []),
        ("30_figures.py", []), ("31_paper_tables.py", []), ("40_verify.py", [])]
FULL = [("00_get_data.py", []), ("01_dataset_facts.py", []), ("02_archive_linkage.py", []),
        ("10_fit_initial99.py", []), ("11_fit_designs.py", []), ("12_fit_seeds.py", []), ("13_fit_nested.py", []),
        ("14_fit_loro99.py", []), ("15_fit_lpgo.py", []), ("16_controls.py", ["lr"]),
        ("20_tables.py", []), ("21_tables_extra.py", []), ("22_loro_diagnostic.py", []), ("23_constants.py", []),
        ("24_primary_statistics.py", []), ("25_lpgo_statistics.py", []), ("26_secondary_tests.py", []),
        ("30_figures.py", []), ("31_paper_tables.py", []), ("40_verify.py", [])]

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--full", action="store_true"); ap.add_argument("--from", dest="start", default=None)
ap.add_argument("--only", default=None); ap.add_argument("--tol", default=None, help="tolerance passed to step 40")
a = ap.parse_args()
steps = FULL if a.full else FAST
if a.only: steps = [s for s in steps if s[0].startswith(a.only)]
elif a.start: steps = [s for s in steps if s[0][:2] >= a.start]
if not (ROOT / "data" / "raw" / "dataset.csv").exists() and not a.full:
    sys.exit("data/raw/dataset.csv is missing: run  python pipeline/00_get_data.py  first")
# Thread count of the reported run: 2 (a 2 CPU machine, library defaults). The logistic regression on the 76 features
# (lbfgs) reaches a slightly different optimum with another number of BLAS threads (docs/AUDIT.md, section 3), so every
# step is pinned to the reported value. Set CSP_THREADS to change it (results may then differ in the LR predictions).
THREADS = os.environ.get("CSP_THREADS", "2")
T0 = time.time()
for name, extra in steps:
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        env[k] = THREADS
    if name.startswith("40_") and a.tol:
        extra = extra + ["--tol", a.tol]
    print(f"\n######## {name} {' '.join(extra)}", flush=True); t0 = time.time()
    r = subprocess.run([sys.executable, str(P / name)] + extra, cwd=ROOT, env=env)
    print(f"######## {name} finished in {time.time() - t0:.0f} s (exit {r.returncode})", flush=True)
    if r.returncode != 0:
        sys.exit(f"stopped: {name} failed")
print(f"\nall steps done in {(time.time() - T0) / 60:.1f} min")
