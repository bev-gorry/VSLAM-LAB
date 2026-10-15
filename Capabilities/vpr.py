"""
Module: VSLAM-LAB - Capabilities - vpr.py
- Author: Alejandro Fontan Villacampa
- Assisted by: Claude (Sonnet 5)
- Version: 2.0
- Created: 2026-07-23
- Updated: 2026-10-10
- License: GPLv3 License

VPR distance matrix capability: <sequence>/vpr-lab/D.npy (faiss squared L2 between the global descriptors of every
pair of rgb_0 frames, minimum over 0/90/180/270 degree rotations; D_<angle>.npy per rotation), the input of
rgb_vpr (Datasets/extra-files/sample_vpr.py) and rgb_placecell (Capabilities/placecell.py). The extraction code, its
environment and the weights live in the capability's repository (github.com/alejandrofontan/VPR-methods-evaluation,
a fork of gmberton/VPR-methods-evaluation with the vslamlab_vpr.py entry point, cloned to Capabilities/sources/vpr);
this driver runs in the vslamlab environment, resolves the sequence targets (CLAUDE.md's sequence-target argument
convention) into sequence folders and runs the capability's `inference` task on them:
  pixi run vpr <dataset> [<sequence> ...]
  pixi run vpr --datasets d1 d2 ... | --sequences d1 s1 s2 ... | --exp exp.yaml | --configs config.yaml

Sequences that already have a D.npy are skipped unless --overwrite. --method selects the VPR method (default:
megaloc). The Hugging Face token from path_constants is passed to the capability as HF_TOKEN.
Next to every newly computed D.npy, vpr_info.yaml records the method, rotations, image count, processing time and GPU
of the run, which the colmap baseline's run report reads.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Capabilities.CapabilityVSLAMLAB import CapabilityVSLAMLAB  # noqa: E402
from path_constants import HUGGINGFACE_TOKEN  # noqa: E402
from utilities import add_sequence_target_args, resolve_sequence_targets_or_exit, sequence_path  # noqa: E402

CAPABILITY = CapabilityVSLAMLAB("vpr", "alejandrofontan/VPR-methods-evaluation")
DEFAULT_METHOD = "megaloc"


def sequence_vpr_dir(dataset_name: str, sequence_name: str) -> Path:
    """<sequence_path>/vpr-lab - where the capability writes D.npy and the per-rotation matrices."""
    return sequence_path(dataset_name, sequence_name) / "vpr-lab"


def sequence_d_matrix(dataset_name: str, sequence_name: str) -> Path:
    return sequence_vpr_dir(dataset_name, sequence_name) / "D.npy"


def compute_d_matrix(pairs: list[tuple[str, str]], extra_args: list[str] | None = None) -> None:
    """Run the capability on (dataset, sequence) pairs, one sequence at a time so each run can be timed."""
    if HUGGINGFACE_TOKEN is not None:
        os.environ["HF_TOKEN"] = HUGGINGFACE_TOKEN  # inherited by the capability's pixi run
    for dataset, sequence in pairs:
        d_matrix = sequence_d_matrix(dataset, sequence)
        mtime_before = d_matrix.stat().st_mtime if d_matrix.exists() else None
        start = time.perf_counter()
        CAPABILITY.run([sequence_path(dataset, sequence)], extra_args)
        # A skipped sequence (D.npy exists, no --overwrite) keeps its previous vpr_info.yaml
        if d_matrix.exists() and d_matrix.stat().st_mtime != mtime_before:
            write_vpr_info(dataset, sequence, extra_args, time.perf_counter() - start)


def write_vpr_info(dataset: str, sequence: str, extra_args: list[str] | None, runtime_s: float) -> None:
    method = next((arg.split("=", 1)[1] for arg in extra_args or [] if arg.startswith("--method=")), DEFAULT_METHOD)
    rgb_csv = sequence_path(dataset, sequence) / "rgb.csv"
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                         capture_output=True, text=True).stdout.strip() if shutil.which("nvidia-smi") else ""
    info = {
        "method": method,
        # the capability always extracts at 4 rotations and keeps the element-wise minimum (vslamlab_vpr.py --rot_360)
        "rotations_deg": [0, 90, 180, 270],
        "combination": "element-wise minimum over rotations",
        "num_images": sum(1 for _ in open(rgb_csv)) - 1,
        "rgb_csv": str(rgb_csv),
        # wall-clock of the capability run: model load, descriptors at every rotation, distance matrices, saving
        "runtime_s": round(runtime_s, 1),
        "gpu": gpu or "none detected",
        "date": datetime.now().isoformat(timespec="seconds"),
    }
    with open(sequence_vpr_dir(dataset, sequence) / "vpr_info.yaml", "w") as f:
        yaml.safe_dump(info, f, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute the VPR distance matrix <sequence>/vpr-lab/D.npy (runs the VPR capability repository "
                    "in its own environment)."
    )
    add_sequence_target_args(parser)
    parser.add_argument("--method", default=DEFAULT_METHOD, help=f"VPR method to run (default: {DEFAULT_METHOD})")
    parser.add_argument("--overwrite", action="store_true", help="Recompute D.npy even if it already exists for a sequence")
    parser.add_argument("--prefetch", action="store_true", help="Clone + install the capability and download its weights, then exit")
    args = parser.parse_args()

    if args.prefetch:
        CAPABILITY.install()
        return

    extra_args = [f"--method={args.method}"] + (["--overwrite"] if args.overwrite else [])
    compute_d_matrix(resolve_sequence_targets_or_exit(args, parser), extra_args)


if __name__ == "__main__":
    main()
