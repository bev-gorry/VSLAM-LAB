"""
Module: VSLAM-LAB - Datasets - dataset_iphone.py
- Author: Alejandro Fontan
- Assisted by: Claude (Fable 5.1)
- Version: 1.0
- Created: 2026-10-12
- License: GPLv3 License
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Final

import numpy as np
from scipy.spatial.transform import Rotation

from Datasets.DatasetVSLAMLAB import DatasetVSLAMLAB
from utilities import make_printers, write_csv_rows

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "
print_info, print_warning = make_printers(SCRIPT_LABEL)

# An ARStream recording (`arstream record`, github.com/VSLAM-LAB/arstream) is one folder per sequence holding
# rgb/<timestamp>.jpg (the phone's JPEGs, not re-encoded), frames.jsonl (one JSON object per frame: the streamed
# header - seq, timestamp (s, phone uptime clock), width, height, K (3x3 row-major, for the sent resolution),
# T_world_camera (ARKit axes), tracking, exposure_duration - plus file and T_world_camera_opencv, the 4x4 row-major
# camera-to-world pose in OpenCV camera axes), and two derived files (rgb.txt, arkit_poses.txt) this dataset does not
# read. The recording folder is the sequence folder: `pixi run record-iphone` writes it straight to
# self.sequence_path(sequence_name), and the hooks below derive rgb_0/ etc. next to it, all from frames.jsonl.
_FRAMES_FILE: Final = "frames.jsonl"
_RAW_RGB_DIR: Final = "rgb"

# Relative spread of the per-frame intrinsics above which the recording was made with autofocus on (the app
# streams a constant K otherwise).
_INTRINSICS_TOLERANCE: Final = 1e-3


class IphoneDataset(DatasetVSLAMLAB):
    """iPhone (ARStream app) recordings dataset helper for VSLAM-LAB benchmark."""

    def __init__(self, dataset_name: str = "iphone") -> None:
        super().__init__(dataset_name)

        # All sequences are local (scalar in the yaml) - user recordings written by `pixi run record-iphone`.
        self.sequence_location = self.cfg["sequence_location"]

    def download_sequence_data(self, sequence_name: str) -> None:
        if self._has_raw_recording(sequence_name):
            return
        print_info(
            f"Sequence '{sequence_name}' is marked as 'local'. Record it with 'pixi run record-iphone {sequence_name}' "
            f"or place an ARStream recording ({_RAW_RGB_DIR}/, {_FRAMES_FILE}) at {self.sequence_path(sequence_name)}."
        )

    def create_rgb_folder(self, sequence_name: str) -> None:
        rgb_path = self.rgb_path(sequence_name)
        if rgb_path.exists():
            return
        if not self._has_raw_recording(sequence_name):
            raise FileNotFoundError(
                f"ARStream recording for '{sequence_name}' not found at {self.sequence_path(sequence_name)} "
                f"(sequence marked as 'local')."
            )
        # The phone's JPEGs are already at the streamed resolution (no target_resolution): the raw folder becomes
        # rgb_0/ as is, keeping each frame's <timestamp>.jpg name that frames.jsonl points at.
        (self.sequence_path(sequence_name) / _RAW_RGB_DIR).replace(rgb_path)

    def create_rgb_csv(self, sequence_name: str) -> None:
        rgb_path = self.rgb_path(sequence_name)
        rows = []
        for frame in self._frames(sequence_name):
            name = Path(frame["file"]).name
            if not (rgb_path / name).is_file():
                print_warning(f"{sequence_name}: frame {name} listed in {_FRAMES_FILE} is missing from {rgb_path.name}/ - dropped")
                continue
            rows.append([self._timestamp_ns(frame), f"{rgb_path.name}/{name}"])
        rows.sort(key=lambda row: row[0])

        header = ["ts_rgb_0 (ns)", "path_rgb_0"]
        write_csv_rows(self.rgb_csv_path(sequence_name), header, rows)

    def create_calibration_yaml(self, sequence_name: str) -> None:
        K = self._intrinsics(sequence_name)
        rgb0: dict[str, Any] = {
            "cam_name": "rgb_0",
            "cam_type": "rgb",
            "cam_model": "pinhole",
            "focal_length": [float(K[0, 0]), float(K[1, 1])],
            "principal_point": [float(K[0, 2]), float(K[1, 2])],
            "fps": float(self.rgb_hz),
            "T_BS": np.eye(4),
        }
        self.write_calibration_yaml(sequence_name=sequence_name, rgb=[rgb0])

    def create_groundtruth_csv(self, sequence_name: str) -> None:
        # ARKit's visual-inertial pose, camera-to-world in OpenCV camera axes (world: gravity-aligned, y up, origin
        # where the session started). Only frames ARKit itself marked reliable (tracking 'normal') are written:
        # 'limited_*' poses (initialising, excessive motion, relocalising) would put ARKit's own drift into the
        # groundtruth. It remains a VIO estimate, not a metrological reference.
        rows = []
        for frame in self._frames(sequence_name):
            if frame.get("tracking") != "normal":
                continue
            T = np.array(frame["T_world_camera_opencv"], dtype=np.float64).reshape(4, 4)
            qx, qy, qz, qw = Rotation.from_matrix(T[:3, :3]).as_quat()  # scipy: (x, y, z, w)
            rows.append([self._timestamp_ns(frame), *(float(v) for v in T[:3, 3]), float(qx), float(qy), float(qz), float(qw)])
        rows.sort(key=lambda row: row[0])

        header = ["ts (ns)", "tx (m)", "ty (m)", "tz (m)", "qx", "qy", "qz", "qw"]
        write_csv_rows(self.groundtruth_csv_path(sequence_name), header, rows)

    def remove_unused_files(self, sequence_name: str) -> None:
        # Deliberate no-op at every retention tier, including MINIMAL: the recording is the user's own data with no
        # re-download path (same rationale as dataset_pupil_labs.py), and frames.jsonl is what every hook reads.
        return

    def _has_raw_recording(self, sequence_name: str) -> bool:
        sequence_path = self.sequence_path(sequence_name)
        has_frames = (sequence_path / _RAW_RGB_DIR).is_dir() or self.rgb_path(sequence_name).is_dir()
        return has_frames and (sequence_path / _FRAMES_FILE).is_file()

    def _frames(self, sequence_name: str) -> list[dict]:
        frames_file = self.sequence_path(sequence_name) / _FRAMES_FILE
        with open(frames_file, "r", encoding="utf-8") as f:
            frames = [json.loads(line) for line in f if line.strip()]
        if not frames:
            raise ValueError(f"{frames_file} holds no frames")
        return frames

    @staticmethod
    def _timestamp_ns(frame: dict) -> int:
        return int(round(float(frame["timestamp"]) * 1e9))

    def _intrinsics(self, sequence_name: str) -> np.ndarray:
        """The 3x3 K of the recording, already rescaled by the app to the streamed resolution: the per-element
        median over the frames, since ARKit's per-frame intrinsics jitter by a few 1e-4 even with fixed focus. A
        larger spread means the recording was made with autofocus on, which is warned about."""
        Ks = np.array([frame["K"] for frame in self._frames(sequence_name)], dtype=np.float64).reshape(-1, 3, 3)
        K = np.median(Ks, axis=0)
        spread = np.abs(Ks - K).max() / max(abs(K[0, 0]), 1.0)
        if spread > _INTRINSICS_TOLERANCE:
            print_warning(f"{sequence_name}: intrinsics vary across frames (relative spread {spread:.2e}, autofocus on?) - "
                          f"calibration.yaml takes their median")
        return K
