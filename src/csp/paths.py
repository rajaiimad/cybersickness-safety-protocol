"""Paths used by every module and pipeline step, anchored at the repository root.

Outputs go to <repo>/outputs by default. Set the environment variable CSP_OUTPUTS to write a fresh run somewhere else
(for example to rerun everything from scratch and compare the result with the shipped outputs)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"                                   # dataset.csv and the two UFFCSData archives
OUTPUTS = Path(os.environ.get("CSP_OUTPUTS", str(ROOT / "outputs"))).resolve()
PRED = OUTPUTS / "predictions"                                # window level predictions of every model fit
LPGO = PRED / "lpgo"                                          # one file per leave pair of groups out model pair
TABLES = OUTPUTS / "tables"                                   # every result table read by the paper
FIGS = OUTPUTS / "figures"                                    # figures of the paper
PAPER = OUTPUTS / "paper_tables"                              # tables formatted as printed in the paper
REFERENCE = ROOT / "reference"                                # checksums and copies of the outputs used in the paper

for _p in (PRED, LPGO, TABLES, FIGS, PAPER):
    _p.mkdir(parents=True, exist_ok=True)
