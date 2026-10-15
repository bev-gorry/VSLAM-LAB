"""
Module: VSLAM-LAB - Datasets - extra-files - record_iphone.py
- Author: Alejandro Fontan Villacampa
- Assisted by: Claude (Fable 5.1)
- Version: 1.1
- Created: 2026-10-12
- Updated: 2026-10-12
- License: GPLv3 License

Records a sequence of the `iphone` dataset (or, with --lidar, of `iphone-lidar`: LiDAR phones, ARKit
depth alongside every frame) from an iPhone running the ARStream app (github.com/VSLAM-LAB/arstream):
RGB + intrinsics + ARKit pose, over USB (default, macOS) or Wi-Fi (--wifi / --host). The recording
itself runs in the arstream repository's own environment (cloned to Datasets/sources/arstream,
installed on first use); this script runs in the vslamlab environment and

  1. over USB on macOS, brings the app to the foreground on the phone first (arstream's `ios-launch`
     task; iOS suspends the app's listener otherwise and the connection is refused) - --no-launch
     skips it, and over Wi-Fi the app has to be opened on the phone by hand,
  2. records the raw ARStream layout straight into VSLAM-LAB-Benchmark/IPHONE/<sequence_name>/
     (rgb/<timestamp>.jpg, frames.jsonl, rgb.txt, arkit_poses.txt) until Ctrl-C or --duration,
  3. appends <sequence_name> to Datasets/dataset_files/dataset_iphone.yaml's sequence_names,
  4. runs the dataset's download_sequence so rgb_0/, rgb.csv, calibration.yaml and groundtruth.csv
     exist at once (Datasets/dataset_files/dataset_iphone.py).

    pixi run record-iphone                      # USB, sequence named YYYYMMDD_HHMMSS
    pixi run record-iphone my_desk --wifi       # phone found via Bonjour
    pixi run record-iphone my_desk --host 192.168.x.y --duration 30 --view
    pixi run record-iphone --lidar my_desk      # LiDAR phone -> iphone-lidar (rgb + depth_0), fails if no depth arrives
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from arstream_tools import add_phone_args, arstream_task, launch_app, phone_args  # noqa: E402
from Datasets.get_dataset import get_dataset  # noqa: E402
from utilities import make_printers  # noqa: E402

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "
print_info, print_warning = make_printers(SCRIPT_LABEL)

DATASETS = {False: "iphone", True: "iphone-lidar"}  # --lidar -> dataset
FRAMES_FILE = "frames.jsonl"


def dataset_yaml(dataset_name: str) -> Path:
    return REPO_ROOT / "Datasets" / "dataset_files" / f"dataset_{dataset_name}.yaml"


def register_sequence(dataset_name: str, sequence_name: str) -> bool:
    """Appends sequence_name to the dataset yaml's sequence_names block (last list item), keeping the
    file's formatting. Returns False when it was already listed."""
    yaml_path = dataset_yaml(dataset_name)
    with open(yaml_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("sequence_names:"))
    except StopIteration:
        sys.exit(f"{SCRIPT_LABEL}no 'sequence_names:' block in {yaml_path}")

    end = start + 1
    while end < len(lines) and lines[end].lstrip().startswith("- "):
        end += 1
    listed = [line.strip()[2:].strip().strip("'\"") for line in lines[start + 1:end]]
    if sequence_name in listed:
        return False

    lines.insert(end, f"  - {sequence_name}\n")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True


def frame_count(sequence_path: Path) -> tuple[int, int]:
    """(frames recorded, frames with a depth map)."""
    frames_file = sequence_path / FRAMES_FILE
    if not frames_file.is_file():
        return 0, 0
    total = with_depth = 0
    with open(frames_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                total += 1
                if '"depth_file"' in line:
                    with_depth += 1
    return total, with_depth


def record(sequence_path: Path, args: argparse.Namespace) -> None:
    forwarded = phone_args(args)
    if args.view:
        forwarded.append("--view")
    if args.duration is not None:
        forwarded += ["--duration", str(args.duration)]

    # Ctrl-C reaches the whole foreground process group: arstream stops and closes its files on it,
    # and pixi may report that as a non-zero exit - what matters is whether frames were written.
    try:
        arstream_task("record").run_args([str(sequence_path), *forwarded])
    except (KeyboardInterrupt, subprocess.CalledProcessError):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sequence_name", nargs="?", default=datetime.now().strftime("%Y%m%d_%H%M%S"),
                        help="name of the new sequence (default: YYYYMMDD_HHMMSS)")
    add_phone_args(parser)
    parser.add_argument("--lidar", action="store_true",
                        help="LiDAR phone: record into the iphone-lidar dataset (depth_0 from ARKit's sceneDepth)")
    parser.add_argument("--view", action="store_true", help="also show the rerun viewer while recording")
    parser.add_argument("--duration", type=float, help="stop after this many seconds (default: until Ctrl-C)")
    args = parser.parse_args()

    dataset_name = DATASETS[args.lidar]
    dataset = get_dataset(dataset_name)
    sequence_path = dataset.sequence_path(args.sequence_name)
    if sequence_path.exists():
        sys.exit(f"{SCRIPT_LABEL}{sequence_path} already exists - pick another sequence name")
    sequence_path.parent.mkdir(parents=True, exist_ok=True)

    print_info(f"Recording sequence {dataset.dataset_color}{args.sequence_name}\033[0m of {dataset.dataset_label} to {sequence_path}")
    launch_app(args)
    record(sequence_path, args)

    n_frames, n_depth = frame_count(sequence_path)
    if n_frames == 0:
        print_warning("No frames were recorded (is the ARStream app open on the phone?) - nothing registered")
        for child in sequence_path.glob("*"):
            if child.is_dir() and not any(child.iterdir()):
                child.rmdir()
            elif child.is_file():
                child.unlink()
        if sequence_path.is_dir() and not any(sequence_path.iterdir()):
            sequence_path.rmdir()
        sys.exit(1)
    print_info(f"Recorded {n_frames} frames" + (f", {n_depth} with depth" if n_depth else ""))
    if args.lidar and n_depth == 0:
        print_warning(f"No depth map arrived (not a LiDAR phone, or Depth off in the app): the recording stays at "
                      f"{sequence_path} but is not registered - record it without --lidar for the iphone dataset")
        sys.exit(1)
    if not args.lidar and n_depth:
        print_info("The recording carries depth maps; `--lidar` would make an rgbd sequence of iphone-lidar out of it")

    if register_sequence(dataset_name, args.sequence_name):
        print_info(f"Added '{args.sequence_name}' to {dataset_yaml(dataset_name).relative_to(REPO_ROOT)}")

    # A fresh dataset instance re-reads the yaml with the new sequence; download_sequence turns the raw
    # recording into the standardised layout.
    get_dataset(dataset_name).download_sequence(args.sequence_name)


if __name__ == "__main__":
    main()
