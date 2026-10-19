"""
Module: VSLAM-LAB - calib_grid - calib_grid.py
- Created: 2026-10-16
- License: GPLv3 License

Helper for a brute-force search over fixed camera intrinsics (focal length, k1, k2) that make a reconstruction flat.
Driven by a grid yaml (calib_grid/grid_*.yaml) and called step by step from run_calib_grid.sh:

  make-exps GRID        write configs/calib_grid/ (one config + one experiment yaml per grid point) and print
                        "<tag> <exp_yaml>" per point
  set-calib GRID TAG    write the grid point's camera into calibration.yaml of every sequence (the original is
                        backed up once as calibration_before_grid.yaml); the run copies it to calibration_exp.yaml
  restore GRID          put every sequence's original calibration.yaml back
  summary GRID          per grid point and sequence: registration, ATE against groundtruth.csv (AUV navigation,
                        Sim3-aligned by VSLAM-LAB's evaluate) and planarity (Refrax's evaluation/planarity.py
                        metrics); writes <evaluation>/calib_grid_<name>_summary.csv

Planarity sign: the plane normal is oriented towards the cameras, so Sagitta/D > 0 means the edges curve up towards
the cameras (bowl) and < 0 means they curve away (dome). 0 is flat.
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

VSLAM_LAB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VSLAM_LAB_DIR))

from path_constants import VSLAMLAB_BENCHMARK, VSLAMLAB_EVALUATION  # noqa: E402

CONFIGS_DIR = VSLAM_LAB_DIR / "configs" / "calib_grid"
PLANARITY_PY = VSLAM_LAB_DIR / "Capabilities" / "sources" / "refrax" / "evaluation" / "planarity.py"
BACKUP_NAME = "calibration_before_grid.yaml"


def load_grid(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def grid_points(grid: dict) -> list[tuple[str, float, float, float]]:
    """(tag, f, k1, k2) for every combination in the grid, e.g. tag f550_k1-0.150_k2+0.000."""
    return [(f"f{f:g}_k1{k1:+.3f}_k2{k2:+.3f}", f, k1, k2)
            for f, k1, k2 in itertools.product(grid["focal_length"], grid["k1"], grid["k2"])]


def exp_name(grid: dict, tag: str) -> str:
    return f"exp_calibgrid_{grid['name']}_{tag}"


def sequence_dir(grid: dict, sequence: str) -> Path:
    return VSLAMLAB_BENCHMARK / grid["dataset"].upper() / sequence


def make_exps(grid: dict) -> None:
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    config = CONFIGS_DIR / f"config_{grid['name']}.yaml"
    config.write_text(yaml.safe_dump({grid["dataset"]: grid["sequences"]}, sort_keys=False))
    for tag, *_ in grid_points(grid):
        exp_yaml = CONFIGS_DIR / f"{exp_name(grid, tag)}.yaml"
        exp = {exp_name(grid, tag): {"Config": f"calib_grid/{config.name}", "NumRuns": 1,
                                     "Parameters": grid["parameters"], "Module": "colmap"}}
        exp_yaml.write_text(yaml.safe_dump(exp, sort_keys=False))
        print(tag, exp_yaml.relative_to(VSLAM_LAB_DIR))


def set_calib(grid: dict, tag: str) -> None:
    _, f, k1, k2 = next(p for p in grid_points(grid) if p[0] == tag)
    for sequence in grid["sequences"]:
        calib = sequence_dir(grid, sequence) / "calibration.yaml"
        backup = calib.with_name(BACKUP_NAME)
        if not backup.exists():  # keep the original from before the first grid point
            shutil.copy2(calib, backup)
        data = yaml.safe_load(backup.read_text())
        cam = next(c for c in data["cameras"] if c["cam_name"] == "rgb_0")
        cam.update({"cam_model": "pinhole", "focal_length": [f, f], "principal_point": grid["principal_point"],
                    "distortion_type": "radtan4", "distortion_coefficients": [k1, k2, 0.0, 0.0]})
        calib.write_text("%YAML 1.2\n---\n" + yaml.safe_dump(data, sort_keys=False))
        print(f"{sequence}: rgb_0 = OPENCV f={f:g} k1={k1:+.3f} k2={k2:+.3f}")


def restore(grid: dict) -> None:
    for sequence in grid["sequences"]:
        backup = sequence_dir(grid, sequence) / BACKUP_NAME
        if backup.exists():
            shutil.move(backup, backup.with_name("calibration.yaml"))
            print(f"{sequence}: original calibration.yaml restored")


def camera_centres(images_txt: Path) -> np.ndarray:
    """Camera centres C = -R^T t from a COLMAP images.txt (every other line is an image's pose)."""
    lines = [line for line in images_txt.read_text().splitlines() if line and not line.startswith("#")]
    centres = []
    for line in lines[::2]:
        qw, qx, qy, qz, tx, ty, tz = map(float, line.split()[1:8])
        R = np.array([[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
                      [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
                      [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]])
        centres.append(-R.T @ np.array([tx, ty, tz]))
    return np.array(centres)


def planarity(model_dir: Path) -> dict:
    """Refrax's planarity metrics for one model, with planarity.py's own preprocessing for a single cloud."""
    spec = importlib.util.spec_from_file_location("planarity", PLANARITY_PY)
    pl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pl)

    points = pl.load_points(model_dir / "points3D.txt")
    diagonal = pl.plane_diagonal(points)
    points = pl.sample(pl.percentile_filter(pl.voxel_downsample(points, diagonal * 0.001)), pl.MAX_POINTS)
    towards_cameras = camera_centres(model_dir / "images.txt").mean(0) - points.mean(0)
    stats = pl.stats(pl.fit_quadric(pl.analyze(points, ref_normal=towards_cameras)))
    return {"rel_rmse_pct": float(stats["Relative RMSE [%]"]), "sagitta_pct": float(stats["Sagitta/D [%]"])}


def summary(grid: dict) -> None:
    rows = []
    for tag, f, k1, k2 in grid_points(grid):
        for sequence in grid["sequences"]:
            seq_dir = VSLAMLAB_EVALUATION / exp_name(grid, tag) / grid["dataset"].upper() / sequence
            row = {"tag": tag, "f": f, "k1": k1, "k2": k2, "sequence": sequence}
            report = seq_dir / "00000_run_report.yaml"
            if report.exists():
                reg = yaml.safe_load(report.read_text())["results"]["registration"]
                row.update(registered=f"{reg['registered_images']}/{reg['input_images']}", sub_models=reg["sub_models"])
            ate = seq_dir / "vslamlab_evaluation" / "ate.csv"
            if ate.exists():
                row["ate_rmse_m"] = float(pd.read_csv(ate)["rmse"].iloc[0])
            model = seq_dir / "colmap_00000"
            if (model / "points3D.txt").exists():
                row.update(planarity(model))
            rows.append(row)

    table = pd.DataFrame(rows)
    out = VSLAMLAB_EVALUATION / f"calib_grid_{grid['name']}_summary.csv"
    table.to_csv(out, index=False)
    pd.set_option("display.width", 200)
    print(table.to_string(index=False))

    # One score per camera: it has to flatten every year at once
    if "sagitta_pct" in table:
        table["abs_sagitta_pct"] = table["sagitta_pct"].abs()
        columns = [c for c in ("abs_sagitta_pct", "rel_rmse_pct", "ate_rmse_m") if c in table]
        print("\nMean over sequences (lower is flatter):")
        print(table.groupby("tag")[columns].mean().sort_values("abs_sagitta_pct").to_string())
    print(f"\nWritten: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["make-exps", "set-calib", "restore", "summary"])
    parser.add_argument("grid", help="grid yaml, e.g. calib_grid/grid_sesoko_half.yaml")
    parser.add_argument("tag", nargs="?", help="grid point tag (set-calib only)")
    args = parser.parse_args()

    grid = load_grid(args.grid)
    if args.command == "make-exps":
        make_exps(grid)
    elif args.command == "set-calib":
        if not args.tag:
            parser.error("set-calib needs a tag")
        set_calib(grid, args.tag)
    elif args.command == "restore":
        restore(grid)
    else:
        summary(grid)


if __name__ == "__main__":
    main()
