"""
Module: VSLAM-LAB - Datasets - dataset_iphone_lidar.py
- Author: Alejandro Fontan
- Assisted by: Claude (Fable 5.1)
- Version: 1.0
- Created: 2026-10-13
- License: GPLv3 License
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Final

import cv2
import numpy as np

from Datasets.dataset_files.dataset_iphone import IphoneDataset
from utilities import make_printers, write_csv_rows

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "
print_info, print_warning = make_printers(SCRIPT_LABEL)

# An ARStream recording of a LiDAR phone adds, next to rgb/ and frames.jsonl (see dataset_iphone.py), ARKit's
# sceneDepth per frame: depth/<timestamp>.png (16-bit, millimetres, 0 = no measurement, ARKit's native 256x192 aligned
# with the image) and confidence/<timestamp>.png (8-bit, 0 low / 1 medium / 2 high); frames.jsonl names them in
# depth_file / confidence_file. depth_0/ is derived from them at the RGB resolution (nearest-neighbour upsampling, never
# an interpolating resample) with low-confidence pixels set to 0, and the raw depth/ and confidence/ folders stay.
_DEPTH_KEY: Final = "depth_file"
_CONFIDENCE_KEY: Final = "confidence_file"
_RAW_DEPTH_DIR: Final = "depth"


class IphoneLidarDataset(IphoneDataset):
    """LiDAR iPhone (ARStream app) recordings dataset helper for VSLAM-LAB benchmark."""

    def __init__(self, dataset_name: str = "iphone-lidar") -> None:
        super().__init__(dataset_name)

        # Depth factor and ARKit confidence threshold of depth_0/
        self.depth_factor = float(self.cfg["depth_factor"])
        self.min_confidence = int(self.cfg.get("min_confidence", 1))

    def download_sequence_data(self, sequence_name: str) -> None:
        if self._has_raw_recording(sequence_name):
            return
        print_info(
            f"Sequence '{sequence_name}' is marked as 'local'. Record it on a LiDAR iPhone with "
            f"'pixi run record-iphone --lidar {sequence_name}' or place an ARStream recording with depth (rgb/, "
            f"{_RAW_DEPTH_DIR}/, frames.jsonl) at {self.sequence_path(sequence_name)}."
        )

    def create_rgb_folder(self, sequence_name: str) -> None:
        super().create_rgb_folder(sequence_name)  # rgb/ -> rgb_0/

        depth_path = self.depth_path(sequence_name)
        if depth_path.exists():
            return
        sequence_path = self.sequence_path(sequence_name)
        if not (sequence_path / _RAW_DEPTH_DIR).is_dir():
            raise FileNotFoundError(f"ARStream recording of '{sequence_name}' has no {_RAW_DEPTH_DIR}/ folder (not a LiDAR recording?)")

        # Decode into a staging folder and rename at the end, so a crash mid-way never leaves a partial depth_0/
        # that the exists() check above would take for a finished one.
        staging = depth_path.with_name(f".{depth_path.name}_tmp")
        if staging.exists():
            for leftover in staging.iterdir():
                leftover.unlink()
        staging.mkdir(parents=True, exist_ok=True)

        written = skipped = 0
        for frame in self._frames(sequence_name):
            if _DEPTH_KEY not in frame:
                skipped += 1
                continue
            depth = cv2.imread(str(sequence_path / frame[_DEPTH_KEY]), cv2.IMREAD_UNCHANGED)
            if depth is None or depth.dtype != np.uint16:
                skipped += 1
                continue
            if _CONFIDENCE_KEY in frame and self.min_confidence > 0:
                confidence = cv2.imread(str(sequence_path / frame[_CONFIDENCE_KEY]), cv2.IMREAD_UNCHANGED)
                if confidence is not None and confidence.shape == depth.shape:
                    depth = np.where(confidence >= self.min_confidence, depth, 0).astype(np.uint16)
            depth = cv2.resize(depth, (int(frame["width"]), int(frame["height"])), interpolation=cv2.INTER_NEAREST)
            cv2.imwrite(str(staging / f"{Path(frame[_DEPTH_KEY]).stem}.png"), depth)
            written += 1
        if skipped:
            print_warning(f"{sequence_name}: {skipped} frames without a usable depth map (dropped from the rgbd pairing)")
        print_info(f"{sequence_name}: {written} depth maps upsampled to the RGB resolution in {depth_path.name}/ "
                   f"(confidence >= {self.min_confidence}, depth_factor {self.depth_factor:g})")
        staging.rename(depth_path)

    def create_rgb_csv(self, sequence_name: str) -> None:
        # Depth and image are the same ARFrame (hardware-synchronized): one timestamp for both columns
        rgb_path = self.rgb_path(sequence_name)
        depth_path = self.depth_path(sequence_name)
        rows = []
        for frame in self._frames(sequence_name):
            name = Path(frame["file"]).name
            if not (rgb_path / name).is_file():
                print_warning(f"{sequence_name}: frame {name} listed in frames.jsonl is missing from {rgb_path.name}/ - dropped")
                continue
            depth_name = f"{Path(name).stem}.png"
            if not (depth_path / depth_name).is_file():
                continue
            ts = self._timestamp_ns(frame)
            rows.append([ts, f"{rgb_path.name}/{name}", ts, f"{depth_path.name}/{depth_name}"])
        rows.sort(key=lambda row: row[0])

        header = ["ts_rgb_0 (ns)", "path_rgb_0", "ts_depth_0 (ns)", "path_depth_0"]
        write_csv_rows(self.rgb_csv_path(sequence_name), header, rows)

    def create_calibration_yaml(self, sequence_name: str) -> None:
        K = self._intrinsics(sequence_name)
        rgbd0: dict[str, Any] = {
            "cam_name": "rgb_0",
            "cam_type": "rgb+depth",
            "depth_name": "depth_0",
            "cam_model": "pinhole",
            "focal_length": [float(K[0, 0]), float(K[1, 1])],
            "principal_point": [float(K[0, 2]), float(K[1, 2])],
            "depth_factor": float(self.depth_factor),
            "fps": float(self.rgb_hz),
            "T_BS": np.eye(4),
        }
        self.write_calibration_yaml(sequence_name=sequence_name, rgbd=[rgbd0])

    def _has_raw_recording(self, sequence_name: str) -> bool:
        sequence_path = self.sequence_path(sequence_name)
        has_depth = (sequence_path / _RAW_DEPTH_DIR).is_dir() or self.depth_path(sequence_name).is_dir()
        return super()._has_raw_recording(sequence_name) and has_depth
