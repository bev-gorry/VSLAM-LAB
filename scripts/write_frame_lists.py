"""Frame lists for the full multi-session sequences, so the joint run (Ours) and the per-session runs (post-hoc
baselines) use exactly the same frames. Experiments then read them with `rgb_csv: <name>` instead of `rgb_step`.

Why: VSLAM-LAB applies rgb_step to the combined list (Run/run_functions.py), so after a session with an odd frame
count the next session's frames shift by one relative to rgb_step on that session alone. The paper took every 2nd
frame within each session instead.

  --frames <csv>   keep exactly these frames (path_rgb_0 column), e.g. the paper run's rgb_exp.csv (Eiffel Tower)
  otherwise        every --step-th frame within each session, starting at its first frame (Sesoko)

Writes <combined>/<name> and <session>/<name> (rows of each folder's own rgb.csv, in its order).

usage (from the VSLAM-LAB root): pixi run -e vslamlab python scripts/write_frame_lists.py <benchmark>/<DATASET>/<combined seq> <session seq folder> ... [--frames csv]
           [--step 2] [--name rgb_step2.csv]
"""
import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("combined", type=Path, help="combined sequence folder (rgb.csv with a sequence_name column)")
    parser.add_argument("sessions", type=Path, nargs="+", help="each session's own sequence folder")
    parser.add_argument("--frames", type=Path, default=None, help="csv whose path_rgb_0 rows are the frames to keep")
    parser.add_argument("--step", type=int, default=2)
    parser.add_argument("--name", default="rgb_step2.csv")
    args = parser.parse_args()

    combined = pd.read_csv(args.combined / "rgb.csv")
    if args.frames:
        keep = set(pd.read_csv(args.frames)["path_rgb_0"])
        selected = combined[combined["path_rgb_0"].isin(keep)]
        missing = keep - set(selected["path_rgb_0"])
        if missing:
            raise SystemExit(f"{len(missing)} listed frames are not in {args.combined / 'rgb.csv'}, e.g. {sorted(missing)[:3]}")
    else:
        selected = combined[combined.groupby("sequence_name").cumcount() % args.step == 0]
    selected.to_csv(args.combined / args.name, index=False)
    print(f"{args.combined.name}: {len(selected)} of {len(combined)} frames -> {args.name}")

    names = set(selected["path_rgb_0"])
    for folder in args.sessions:
        session = pd.read_csv(folder / "rgb.csv")
        kept = session[session["path_rgb_0"].isin(names)]
        kept.to_csv(folder / args.name, index=False)
        print(f"  {folder.name}: {len(kept)} of {len(session)} frames")
    per_session = selected["sequence_name"].value_counts().to_dict()
    print(f"  per session in the combined list: {per_session}")


if __name__ == "__main__":
    main()
