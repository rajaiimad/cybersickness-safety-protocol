"""Step 02. Links the 35 recordings of dataset.csv to the two archives of UFFCSData and derives the start times used
in Section III-A to judge whether a participant group is one person. No model is fitted; nothing later depends on it.

Inputs: data/raw/DATABASE_SELECTED_DATA.zip and data/raw/RAW_DATABASE.zip (step 00).

Findings
  * DATABASE_SELECTED_DATA.zip holds 35 folders, one recording (FILE.xml) each; RAW_DATABASE.zip holds 74 time
    stamped session folders (47 flight, 27 race), each with a VRSQ_FILE.xml questionnaire.
  * every recording of dataset.csv matches exactly one selected and one raw session (same length and same first 20
    camera rotation values, asserted); the raw folder name gives the start date and time.
  * no file carries a participant identifier; the extra raw fields (symptoms, posture, haptic feedback, degree of
    control, DoF simulation, locomotion) are constant across the recordings.

Outputs
  outputs/tables/T_archive_sessions.csv      one row per recording, sorted by start time
  outputs/tables/T_raw_archive_sessions.csv  one row per raw session folder (game and start time)
  outputs/tables/T_archive_facts.csv         the numbers quoted in Section III-A"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import os, re, zipfile, tempfile
import xml.etree.ElementTree as ET
import numpy as np, pandas as pd

from csp.paths import RAW, TABLES
from csp.data import load_and_group

src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else RAW
tmp = pathlib.Path(tempfile.mkdtemp())
for z in ("DATABASE_SELECTED_DATA.zip", "RAW_DATABASE.zip"):
    zipfile.ZipFile(src / z).extractall(tmp)


def rows(p):
    return pd.DataFrame([{c.tag: c.text for c in e} for e in ET.parse(p).getroot().findall("Data")])


def num(s): return pd.to_numeric(s.astype(str).str.replace(",", "."), errors="coerce")


def sig(df): return (len(df), tuple(np.round(num(df.CameraRotationY).values[:20], 4)))


# ---- raw archive: every session folder, from the folder names
pat = re.compile(r"DATA_EXPORT_(Race|Flight)_(\d{4})_(\d{1,2})_(\d{1,2})_(\d{1,2})_(\d{1,2})_(\d{1,2})/")
folders = {}
for n in zipfile.ZipFile(src / "RAW_DATABASE.zip").namelist():
    m = pat.search(n)
    if m:
        g, yy, mo, dd, h, mi, s = m.groups()
        folders[m.group(0)] = dict(folder=m.group(0).rstrip("/"), game=g,
                                   start=pd.Timestamp(int(yy), int(mo), int(dd), int(h), int(mi), int(s)))
RA = pd.DataFrame(folders.values()).sort_values("start"); RA.to_csv(TABLES / "T_raw_archive_sessions.csv", index=False)

# ---- link every recording to one selected and one raw session
sel = {int(f): rows(tmp / "DATABASE" / f / "FILE.xml") for f in os.listdir(tmp / "DATABASE")}
raw = {}
for f in sorted(os.listdir(tmp / "RAW_DATABASE")):
    p = tmp / "RAW_DATABASE" / f / "FILE.xml"
    if p.exists():
        r = rows(p)
        if len(r): raw[f] = r
extra = ["UserSymptoms", "UserPosture", "HapticFeedback", "DegreeOfControl", "DofSimulation", "Locomotion"]
extra_values = {k: sorted({str(r[k].iloc[0]).lower() for r in sel.values()}) for k in extra}
print("selected recordings", len(sel), "| raw session folders", len(RA), RA.game.value_counts().to_dict(),
      "| extra fields:", extra_values)

d = load_and_group(str(RAW / "dataset.csv")); out = []
for s, g in d.groupby("session"):
    k = (len(g), tuple(np.round(g.CameraRotationY.values[:20], 4)))
    hs = [i for i, r in sel.items() if sig(r) == k]; hr = [f for f, r in raw.items() if sig(r) == k]
    assert len(hs) == 1 and len(hr) == 1, (s, hs, hr)
    m = re.match(r"DATA_EXPORT_(\w+?)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)", hr[0])
    out.append(dict(session=s, group=int(g.participant.iloc[0]), windows=len(g), max_severity=int(g.DiscomfortLevel.max()),
                    selected_folder=hs[0], raw_folder=hr[0], game=m.group(1),
                    start=pd.Timestamp(*map(int, m.groups()[1:]))))
T = pd.DataFrame(out).sort_values("start")
T["minutes_since_previous"] = (T.start.diff().dt.total_seconds() / 60).round(1)
T.to_csv(TABLES / "T_archive_sessions.csv", index=False)

# ---- numbers quoted in Section III-A
F = {"selected_recordings": len(sel), "raw_session_folders": len(RA),
     "raw_flight_sessions": int((RA.game == "Flight").sum()), "raw_race_sessions": int((RA.game == "Race").sum()),
     "recordings_linked": len(T), "extra_fields_constant": int(all(len(v) == 1 for v in extra_values.values()))}
gap = T.start.diff().dt.total_seconds() / 60
same_day = (T.start.dt.date == T.start.dt.date.shift()).values
F["same_day_consecutive_pairs"] = int(same_day.sum())
F["same_day_gap_median_min"] = float(gap[same_day].median())                       # unrounded: 7.25
F["same_day_gap_median_of_rounded_min"] = float(T.minutes_since_previous[same_day].median())   # 7.2 as printed
multi = T.groupby("group").filter(lambda x: len(x) > 1)
F["groups_with_more_than_one_recording"] = multi.group.nunique()
for gid, x in multi.groupby("group"):
    x = x.sort_values("start"); between = T[(T.start > x.start.min()) & (T.start < x.start.max()) & (T.group != gid)]
    F[f"group_{gid}_recordings"] = len(x)
    F[f"group_{gid}_days"] = x.start.dt.date.nunique()
    F[f"group_{gid}_span_min"] = round((x.start.max() - x.start.min()).total_seconds() / 60, 1)
    F[f"group_{gid}_max_gap_min"] = round(x.start.diff().dt.total_seconds().max() / 60, 1)
    F[f"group_{gid}_other_recordings_between"] = len(between)
    F[f"group_{gid}_other_profiles_between"] = between.group.nunique()
short = T[T.windows < 120]; changed = 0
for _, r in short.iterrows():
    nxt = T[T.start > r.start].iloc[0]; changed += int(nxt.group != r.group)
    print(f"  short recording {r.session} ({r.windows} windows, group {r.group}) -> recording {nxt.session} "
          f"(group {nxt.group}) after {(nxt.start - r.start).total_seconds() / 60:.1f} min")
F["restarts_after_short_recording"] = len(short); F["restarts_with_different_descriptors"] = changed
FT = pd.DataFrame(list(F.items()), columns=["name", "value"]); FT.to_csv(TABLES / "T_archive_facts.csv", index=False)
print(FT.to_string(index=False))
