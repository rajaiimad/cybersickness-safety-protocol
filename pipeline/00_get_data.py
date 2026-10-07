"""Step 00. Download the public dataset at a pinned commit and verify its checksums.

Source: UFFCSData, https://github.com/tmp1986/UFFCSData (Porcino et al.), commit b5128e6 of 2020-05-01, licence
AGPL-3.0 (a copy is written to data/raw/UFFCSData_LICENSE). Files:
  dataset.csv                 the merged file analysed in the paper (9,390 rows, 22 columns)
  DATABASE_SELECTED_DATA.zip  35 selected recordings (used only by step 02, archive linkage)
  RAW_DATABASE.zip            74 raw time stamped sessions (used only by step 02)

A file that is already present is only verified, not downloaded again. A checksum mismatch stops the pipeline:
the results of the paper were computed from exactly these bytes."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import hashlib, urllib.request

from csp.paths import RAW

COMMIT = "b5128e681786b81501d269a73e860d57c495d0aa"
BASE = f"https://raw.githubusercontent.com/tmp1986/UFFCSData/{COMMIT}/"
FILES = {
    "dataset.csv": "2d3ab0a82962a11ef389ea02be4b51e6b7bad6004c53cd778db2b97f6665f740",
    "DATABASE_SELECTED_DATA.zip": "206f27a7fb2ccd83fc2dbdb767ffd641371902ea185ff41d221bea36b316031a",
    "RAW_DATABASE.zip": "7dc386b21922b7a5da1d746ce06c75669e230ea8be2fd26e84e4c0356d6327bc",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    targets = dict(FILES, **{"UFFCSData_LICENSE": None})
    for name, digest in targets.items():
        p = RAW / name
        if not p.exists():
            src = BASE + ("LICENSE" if name == "UFFCSData_LICENSE" else name)
            print("downloading", src, flush=True)
            urllib.request.urlretrieve(src, p)
        if digest is not None:
            got = sha256(p)
            if got != digest:
                sys.exit(f"checksum mismatch for {p}: expected {digest}, got {got}")
            print(f"ok  {name}  sha256 {got[:16]}...")
    print("data ready in", RAW)


if __name__ == "__main__":
    main()
