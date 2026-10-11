"""
Module: VSLAM-LAB - Datasets - extra-files - record_iphone.py
- Author: Alejandro Fontan Villacampa
- Assisted by: Claude (Fable 5.1)
- Version: 1.0
- Created: 2026-10-12
- Updated: 2026-10-12
- License: GPLv3 License

Records a sequence of the `iphone` dataset from an iPhone running the ARStream app
(github.com/VSLAM-LAB/arstream): RGB + intrinsics + ARKit pose, over USB (default, macOS) or Wi-Fi
(--wifi / --host). The recording itself runs in the arstream repository's own environment (cloned to
Datasets/sources/arstream, installed on first use); this script runs in the vslamlab environment and

  1. records the raw ARStream layout straight into VSLAM-LAB-Benchmark/IPHONE/<sequence_name>/
     (rgb/<timestamp>.jpg, frames.jsonl, rgb.txt, arkit_poses.txt) until Ctrl-C or --duration,
  2. appends <sequence_name> to Datasets/dataset_files/dataset_iphone.yaml's sequence_names,
  3. runs the dataset's download_sequence so rgb_0/, rgb.csv, calibration.yaml and groundtruth.csv
     exist at once (Datasets/dataset_files/dataset_iphone.py).

    pixi run record-iphone                      # USB, sequence named YYYYMMDD_HHMMSS
    pixi run record-iphone my_desk --wifi       # phone found via Bonjour
    pixi run record-iphone my_desk --host 192.168.x.y --duration 30 --view
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from Capabilities.CapabilityVSLAMLAB import CapabilityVSLAMLAB  # noqa: E402
from Datasets.get_dataset import get_dataset  # noqa: E402
from utilities import make_printers  # noqa: E402

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "
print_info, print_warning = make_printers(SCRIPT_LABEL)

DATASET_NAME = "iphone"
DATASET_YAML = REPO_ROOT / "Datasets" / "dataset_files" / f"dataset_{DATASET_NAME}.yaml"
FRAMES_FILE = "frames.jsonl"

# The arstream repository: its pixi.toml carries the client's stack (opencv, rerun, zeroconf) and the
# `record` / `view` / `ios-install` tasks; `record` takes the output folder plus the connection flags.
ARSTREAM = CapabilityVSLAMLAB("arstream", "VSLAM-LAB/arstream", path=REPO_ROOT / "Datasets" / "sources" / "arstream",
                              inference_task="record")


def register_sequence(sequence_name: str) -> bool:
    """Appends sequence_name to the yaml's sequence_names block (last list item), keeping the file's
    formatting. Returns False when it was already listed."""
    with open(DATASET_YAML, "r", encoding="utf-8") as f:
        lines = f.readlines()

    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("sequence_names:"))
    except StopIteration:
        sys.exit(f"{SCRIPT_LABEL}no 'sequence_names:' block in {DATASET_YAML}")

    end = start + 1
    while end < len(lines) and lines[end].lstrip().startswith("- "):
        end += 1
    listed = [line.strip()[2:].strip().strip("'\"") for line in lines[start + 1:end]]
    if sequence_name in listed:
        return False

    lines.insert(end, f"  - {sequence_name}\n")
    with open(DATASET_YAML, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True


def frame_count(sequence_path: Path) -> int:
    frames_file = sequence_path / FRAMES_FILE
    if not frames_file.is_file():
        return 0
    with open(frames_file, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def record(sequence_path: Path, args: argparse.Namespace) -> None:
    forwarded = []
    if args.wifi:
        forwarded.append("--wifi")
    if args.host:
        forwarded += ["--host", args.host]
    if args.port is not None:
        forwarded += ["--port", str(args.port)]
    if args.serial:
        forwarded += ["--serial", args.serial]
    if args.view:
        forwarded.append("--view")
    if args.duration is not None:
        forwarded += ["--duration", str(args.duration)]

    # Ctrl-C reaches the whole foreground process group: arstream stops and closes its files on it,
    # and pixi may report that as a non-zero exit - what matters is whether frames were written.
    try:
        ARSTREAM.run_args([str(sequence_path), *forwarded])
    except (KeyboardInterrupt, subprocess.CalledProcessError):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sequence_name", nargs="?", default=datetime.now().strftime("%Y%m%d_%H%M%S"),
                        help="name of the new sequence (default: YYYYMMDD_HHMMSS)")
    parser.add_argument("--wifi", action="store_true", help="find the phone on Wi-Fi via Bonjour (default: USB)")
    parser.add_argument("--host", help="phone IP for Wi-Fi (shown in the app)")
    parser.add_argument("--port", type=int, help="port the app listens on (default: arstream's 5555)")
    parser.add_argument("--serial", help="device serial/UDID if several phones are plugged in")
    parser.add_argument("--view", action="store_true", help="also show the rerun viewer while recording")
    parser.add_argument("--duration", type=float, help="stop after this many seconds (default: until Ctrl-C)")
    args = parser.parse_args()

    dataset = get_dataset(DATASET_NAME)
    sequence_path = dataset.sequence_path(args.sequence_name)
    if sequence_path.exists():
        sys.exit(f"{SCRIPT_LABEL}{sequence_path} already exists - pick another sequence name")
    sequence_path.parent.mkdir(parents=True, exist_ok=True)

    print_info(f"Recording sequence {dataset.dataset_color}{args.sequence_name}\033[0m of {dataset.dataset_label} to {sequence_path}")
    record(sequence_path, args)

    n_frames = frame_count(sequence_path)
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
    print_info(f"Recorded {n_frames} frames")

    if register_sequence(args.sequence_name):
        print_info(f"Added '{args.sequence_name}' to {DATASET_YAML.relative_to(REPO_ROOT)}")

    # A fresh dataset instance re-reads the yaml with the new sequence; download_sequence turns the raw
    # recording into the standardised layout.
    get_dataset(DATASET_NAME).download_sequence(args.sequence_name)


if __name__ == "__main__":
    main()
