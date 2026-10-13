"""
Module: VSLAM-LAB - Datasets - dataset_eiffel_tower.py
- Author: Alejandro Fontan
- Assisted by: Claude (Sonnet 5)
- Version: 1.0
- Created: 2026-07-24
- Updated: 2026-07-26
- License: GPLv3 License
"""

from __future__ import annotations

import datetime
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image
from scipy.spatial.transform import Rotation
from tqdm import tqdm

from Datasets.DatasetVSLAMLAB import DatasetVSLAMLAB
from path_constants import BENCHMARK_RETENTION, Retention
from utilities import compute_scaled_size, decompressFile, downloadFile, scale_intrinsics, write_csv_rows

# COLMAP's RADIAL camera model: f, cx, cy, k1, k2 (single focal length, purely radial distortion).
# https://colmap.github.io/cameras.html
_RADIAL_NUM_PARAMS = 5


class EiffelTowerDataset(DatasetVSLAMLAB):
    """Eiffel Tower deep-sea underwater dataset helper for VSLAM-LAB benchmark."""

    def __init__(self, dataset_name: str = "eiffel-tower") -> None:
        super().__init__(dataset_name)

        # Get download urls (one unrelated URL per campaign/sequence)
        self.url_download_root: dict[str, str] = self.cfg["url_download_root"]

        # Sequences derived from already-processed ones (see the yaml's subsets/combined)
        self.subsets: dict[str, list] = self.cfg.get("subsets", {}) or {}
        self.combined: dict[str, list[str]] = self.cfg.get("combined", {}) or {}

    def download_sequence_data(self, sequence_name: str) -> None:
        if sequence_name in self.subsets:
            self._create_subset(sequence_name)
            return
        if sequence_name in self.combined:
            self._create_combined(sequence_name)
            return

        sequence_path = self.sequence_path(sequence_name)
        url = self.url_download_root[sequence_name]
        zip_path = self.dataset_path / url.rsplit("/", 1)[-1]

        if not zip_path.exists() and not sequence_path.exists():
            downloadFile(url, str(self.dataset_path))

        if not sequence_path.exists():
            # The archive unpacks into a folder named after the campaign year (e.g. 2018/), renamed
            # here to the sequence name (eff18).
            with zipfile.ZipFile(zip_path) as zip_file:
                extracted_path = self.dataset_path / zip_file.namelist()[0].split("/", 1)[0]
            if extracted_path != sequence_path and extracted_path.exists():
                raise FileExistsError(f"{extracted_path} already exists: move it before extracting {zip_path.name}")
            decompressFile(str(zip_path), str(self.dataset_path))
            if extracted_path != sequence_path:
                extracted_path.rename(sequence_path)

    def create_rgb_folder(self, sequence_name: str) -> None:
        if self._is_derived(sequence_name):
            return
        sequence_path = self.sequence_path(sequence_name)
        rgb_path = self.rgb_path(sequence_name)
        raw_path = sequence_path / "images"

        if rgb_path.exists():
            return
        rgb_path.mkdir(parents=True, exist_ok=True)

        target_size = None
        for file_path in tqdm(sorted(raw_path.glob("*.png")), desc="    resizing images"):
            if self.target_resolution is None:
                shutil.copy2(file_path, rgb_path / file_path.name)
                continue

            with Image.open(file_path) as img:
                img.load()
                if target_size is None:
                    target_size = compute_scaled_size(img.size, self.target_resolution)
                resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                resized_img.save(rgb_path / file_path.name)

    def create_rgb_csv(self, sequence_name: str) -> None:
        if self._is_derived(sequence_name):
            return
        rgb_path = self.rgb_path(sequence_name)
        rgb_csv = self.rgb_csv_path(sequence_name)
        rgb_files = sorted(f.name for f in rgb_path.iterdir() if f.is_file())

        # sequence_name: the campaign of each frame, carried into subsets and combined sequences so
        # a multi-session sequence still knows which session each frame belongs to.
        header = ["ts_rgb_0 (ns)", "path_rgb_0", "sequence_name"]
        rows = [[self._filename_to_ts_ns(filename), f"rgb_0/{filename}", sequence_name] for filename in rgb_files]
        write_csv_rows(rgb_csv, header, rows)

    def create_calibration_yaml(self, sequence_name: str) -> None:
        if self._is_derived(sequence_name):
            return
        sequence_path = self.sequence_path(sequence_name)
        cameras_txt = sequence_path / "sfm" / "cameras.txt"

        width, height, f, cx, cy, k1, k2 = self._read_colmap_camera(cameras_txt)

        # Rescale intrinsics from the raw COLMAP reference image size to the resized rgb_0 size.
        focal_length, principal_point = scale_intrinsics((f, f), (cx, cy), (width, height), self.target_resolution)

        rgb: dict[str, Any] = {
            "cam_name": "rgb_0",
            "cam_type": "rgb",
            "cam_model": "pinhole",
            "distortion_type": "radtan4",
            "distortion_coefficients": [k1, k2, 0.0, 0.0],
            "focal_length": focal_length,
            "principal_point": principal_point,
            "fps": float(self.rgb_hz),
            "T_BS": np.eye(4),
        }
        self.write_calibration_yaml(sequence_name=sequence_name, rgb=[rgb])

    def create_groundtruth_csv(self, sequence_name: str) -> None:
        if self._is_derived(sequence_name):
            return
        sequence_path = self.sequence_path(sequence_name)
        images_txt = sequence_path / "sfm" / "images.txt"
        groundtruth_csv = self.groundtruth_csv_path(sequence_name)
        poses = self._read_colmap_images(images_txt)

        header = ["ts (ns)", "tx (m)", "ty (m)", "tz (m)", "qx", "qy", "qz", "qw"]
        rows = []
        for filename in sorted(poses.keys()):
            qvec, tvec = poses[filename]
            tx, ty, tz, qx, qy, qz, qw = self._world_to_camera_to_pose(qvec, tvec)
            ts_ns = self._filename_to_ts_ns(filename)
            rows.append([ts_ns, tx, ty, tz, qx, qy, qz, qw])
        write_csv_rows(groundtruth_csv, header, rows)

    def remove_unused_files(self, sequence_name: str) -> None:
        if self._is_derived(sequence_name):
            return
        sequence_path = self.sequence_path(sequence_name)
        if BENCHMARK_RETENTION != Retention.FULL:
            shutil.rmtree(sequence_path / "images", ignore_errors=True)
            shutil.rmtree(sequence_path / "sfm", ignore_errors=True)
            (sequence_path / "navigation.txt").unlink(missing_ok=True)

        if BENCHMARK_RETENTION == Retention.MINIMAL:
            url = self.url_download_root[sequence_name]
            (self.dataset_path / url.rsplit("/", 1)[-1]).unlink(missing_ok=True)

    ####################################################################################################################
    # Derived sequences (subsets, combined): built from already-processed sequences by symlinking their frames, so the
    # per-sequence hooks above skip them.
    def _is_derived(self, sequence_name: str) -> bool:
        return sequence_name in self.subsets or sequence_name in self.combined

    def _create_subset(self, sequence_name: str) -> None:
        """Frames of the parent sequence whose groundtruth position is within `radius` metres of the anchor image's,
        with the parent's calibration."""
        parent, anchor_image, radius = self.subsets[sequence_name]
        self.download_sequence(parent)
        if self.rgb_path(sequence_name).exists():
            return

        df_rgb = pd.read_csv(self.rgb_csv_path(parent))
        df_gt = pd.read_csv(self.groundtruth_csv_path(parent))

        # Frames are matched to their pose by timestamp; a frame without a pose can't be placed, so it is left out.
        df_pose = df_rgb.merge(df_gt, left_on="ts_rgb_0 (ns)", right_on="ts (ns)", how="inner", validate="one_to_one")
        is_anchor = (df_pose["path_rgb_0"] == anchor_image).to_numpy()
        if not is_anchor.any():
            raise ValueError(f"Anchor image {anchor_image} of {sequence_name} has no groundtruth pose in {parent}")
        positions = df_pose[["tx (m)", "ty (m)", "tz (m)"]].to_numpy()
        in_radius = np.linalg.norm(positions - positions[is_anchor][0], axis=1) <= radius
        df_subset = df_pose[in_radius]

        self.sequence_path(sequence_name).mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.calibration_yaml_path(parent), self.calibration_yaml_path(sequence_name))
        self._link_frames(parent, sequence_name, df_subset["path_rgb_0"])
        write_csv_rows(self.rgb_csv_path(sequence_name), df_rgb.columns.tolist(),
                       df_subset[df_rgb.columns].astype(object).values.tolist())
        write_csv_rows(self.groundtruth_csv_path(sequence_name), df_gt.columns.tolist(),
                       df_subset[df_gt.columns].astype(object).values.tolist())

    def _create_combined(self, sequence_name: str) -> None:
        """The listed sequences concatenated in order, with the first one's calibration (one camera for all)."""
        parts = self.combined[sequence_name]
        for part in parts:
            self.download_sequence(part)
        if self.rgb_path(sequence_name).exists():
            return

        dfs_rgb = [pd.read_csv(self.rgb_csv_path(part)) for part in parts]
        dfs_gt = [pd.read_csv(self.groundtruth_csv_path(part)) for part in parts]
        df_rgb = pd.concat(dfs_rgb, ignore_index=True)
        df_gt = pd.concat(dfs_gt, ignore_index=True)
        # All frames share one rgb_0 folder, so a file name present in two parts would be overwritten.
        if df_rgb["path_rgb_0"].duplicated().any():
            raise ValueError(f"{sequence_name}: the same frame appears in more than one of {parts}")

        self.sequence_path(sequence_name).mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.calibration_yaml_path(parts[0]), self.calibration_yaml_path(sequence_name))
        for part, df_part in zip(parts, dfs_rgb):
            self._link_frames(part, sequence_name, df_part["path_rgb_0"])
        write_csv_rows(self.rgb_csv_path(sequence_name), df_rgb.columns.tolist(),
                       df_rgb.astype(object).values.tolist())
        write_csv_rows(self.groundtruth_csv_path(sequence_name), df_gt.columns.tolist(),
                       df_gt.astype(object).values.tolist())

    def _link_frames(self, source_sequence: str, target_sequence: str, rel_paths: pd.Series) -> None:
        self.rgb_path(target_sequence).mkdir(parents=True, exist_ok=True)
        for rel_path in rel_paths:
            source = self.sequence_path(source_sequence) / rel_path
            target = self.sequence_path(target_sequence) / rel_path
            if target.is_symlink() or target.exists():
                target.unlink()
            # Relative link: keeps working if the benchmark folder is moved or the drive is mounted elsewhere.
            os.symlink(os.path.relpath(source, target.parent), target)

    @staticmethod
    def _filename_to_ts_ns(filename: str) -> int:
        # Images are named YYYYmmddTHHMMSS.fffZ.png
        stamp = filename.rsplit(".png", 1)[0]  # YYYYmmddTHHMMSS.fff Z
        date_part, rest = stamp.split("T", 1)
        time_part, ms_part = rest.rstrip("Z").split(".", 1)
        yyyy, mm, dd = int(date_part[0:4]), int(date_part[4:6]), int(date_part[6:8])
        hh, mi, ss = int(time_part[0:2]), int(time_part[2:4]), int(time_part[4:6])
        ms = int(ms_part[:3])

        dt = datetime.datetime(yyyy, mm, dd, hh, mi, ss, ms * 1000, tzinfo=datetime.timezone.utc)
        return int(dt.timestamp() * 1e9)

    @staticmethod
    def _read_colmap_camera(cameras_txt: Path) -> tuple[int, int, float, float, float, float, float]:
        with open(cameras_txt, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                model = parts[1]
                width, height = int(parts[2]), int(parts[3])
                params = [float(p) for p in parts[4:]]
                if model != "RADIAL" or len(params) != _RADIAL_NUM_PARAMS:
                    raise ValueError(f"Unexpected COLMAP camera model in {cameras_txt}: {line}")
                f_, cx, cy, k1, k2 = params
                return width, height, f_, cx, cy, k1, k2
        raise ValueError(f"No camera found in {cameras_txt}")

    @staticmethod
    def _read_colmap_images(images_txt: Path) -> dict[str, tuple[tuple[float, ...], tuple[float, ...]]]:
        poses: dict[str, tuple[tuple[float, ...], tuple[float, ...]]] = {}
        with open(images_txt, "r", encoding="utf-8") as f:
            lines = f.readlines()

        is_pose_line = True
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if is_pose_line:
                parts = line.split()
                qw, qx, qy, qz = (float(p) for p in parts[1:5])
                tx, ty, tz = (float(p) for p in parts[5:8])
                name = parts[9]
                poses[name] = ((qw, qx, qy, qz), (tx, ty, tz))
            is_pose_line = not is_pose_line
        return poses

    @staticmethod
    def _world_to_camera_to_pose(
        qvec: tuple[float, float, float, float], tvec: tuple[float, float, float]
    ) -> tuple[float, float, float, float, float, float, float]:
        # COLMAP's qvec/tvec transform world -> camera coordinates (X_cam = R * X_world + t).
        # Groundtruth trajectories are stored as the camera pose in the world frame instead.
        qw, qx, qy, qz = qvec
        rot_world_to_cam = Rotation.from_quat([qx, qy, qz, qw])
        rot_cam_to_world = rot_world_to_cam.inv()

        t_world = rot_cam_to_world.apply(-np.array(tvec))
        qx_w, qy_w, qz_w, qw_w = rot_cam_to_world.as_quat()

        return float(t_world[0]), float(t_world[1]), float(t_world[2]), float(qx_w), float(qy_w), float(qz_w), float(qw_w)
