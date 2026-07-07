from __future__ import annotations

import os
import csv
import utm
import math
import yaml
import json
import shutil
import pandas as pd
import requests
import datetime
import numpy as np
from PIL import Image
from tqdm import tqdm
from pathlib import Path
from loguru import logger
from typing import Final, Any
from scipy.spatial.transform import Rotation
from pyproj import Transformer

from utilities import SCRIPT_LABEL, print_msg
from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from path_constants import Retention, BENCHMARK_RETENTION
from Datasets.DatasetVSLAMLab_issues import _get_dataset_issue

IMAGE_CROP: Final = {"eff15": [0,0], "eff16": [0,0], "eff18": [0,0], "eff20": [0,0]}


class EIFFEL_dataset(DatasetVSLAMLab):
    """EIFFEL dataset helper for VSLAM-LAB benchmark."""
    
    def __init__(self, benchmark_path: str | Path, dataset_name: str = "eiffel") -> None:
        super().__init__(dataset_name, Path(benchmark_path))
        
        # Load settings
        with open(self.yaml_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        # Get download url
        self.local_raw_data_path: str = cfg["local_raw_data_path"]
        
        self.rgb_hz = cfg.get("rgb_hz", 30)
        
        # Target image resolution
        self.image_resolution = cfg.get("target_resolution", [640, 480])
        
        self.subsets = cfg.get("subsets", {})
        self.combined = cfg.get("combined", {})
    
    def download_sequence_data(self, sequence_name: str) -> None:    
        sequence_path: Path = self.dataset_path / sequence_name
        rgb_path: Path = sequence_path / "rgb_0"
        if rgb_path.exists():
            return
        
        if sequence_name in self.subsets.keys():
            self.download_sequence_data(self.subsets.get(sequence_name)[0])
            self.download_subsequence(sequence_name)
            return
            
        if sequence_name in self.combined.keys():
            for subset in self.combined.get(sequence_name):
                self.download_sequence_data(subset)
            self.download_combined_subsequence(sequence_name)
            return
            
        print(f"EIFFEL dataset is local only in raw format. Please check that the sequence name {sequence_name} is correct according to dataset_eiffel.yaml")

    
    def download_subsequence(self, sequence_name: str) -> None:
        sequence_path: Path = self.dataset_path / sequence_name
        rgb_path: Path = sequence_path / "rgb_0"
        rgb_csv: Path = sequence_path / "rgb.csv"
        gt_csv: Path = sequence_path / "groundtruth.csv"
        if rgb_path.exists():
            print("rgb_path exists.")
            return
        rgb_path.mkdir(parents=True, exist_ok=True)

        parent_sequence = self.subsets.get(sequence_name)[0]
        parent_sequence_path: Path = self.dataset_path / parent_sequence
        shutil.copy2(
            parent_sequence_path / "calibration.yaml",
            sequence_path / "calibration.yaml",
        )
                
        parent_rgb_csv: Path = parent_sequence_path / "rgb.csv"
        parent_gt_csv: Path = parent_sequence_path / "groundtruth.csv"
        df_rgb = pd.read_csv(parent_rgb_csv)
        df_gt = pd.read_csv(parent_gt_csv)

        df_rgb["_ts_key"] = pd.to_numeric(df_rgb["ts_rgb_0 (ns)"]).round().astype("int64")
        df_gt["_ts_key"] = pd.to_numeric(df_gt["ts (ns)"]).round().astype("int64")
        df_pose = df_rgb.merge(
            df_gt,
            on="_ts_key",
            how="inner",
            validate="one_to_one",
            suffixes=("", "_gt"),
        )
        if len(df_pose) != len(df_rgb):
            missing = len(df_rgb) - len(df_pose)
            raise ValueError(
                f"Could not match {missing} RGB frame(s) to ground truth by timestamp "
                f"for EIFFEL sequence {parent_sequence}."
            )
        
        target_image_name = self.subsets.get(sequence_name)[1]
        radius = self.subsets.get(sequence_name)[2]
        target_idx = df_pose.index[df_pose['path_rgb_0'] == target_image_name].tolist()
        if not target_idx:
            raise ValueError(
                f"Target image {target_image_name} was not found in {parent_rgb_csv}."
            )
        ref_idx = target_idx[0]
        ref_x = df_pose.at[ref_idx, 'tx (m)']
        ref_y = df_pose.at[ref_idx, 'ty (m)']
        ref_z = df_pose.at[ref_idx, 'tz (m)']

        distances = np.sqrt(
            (df_pose['tx (m)'] - ref_x)**2 +
            (df_pose['ty (m)'] - ref_y)**2 +
            (df_pose['tz (m)'] - ref_z)**2
        )
        mask = distances <= radius
        df_rgb_sub = (
            df_pose.loc[mask, df_rgb.columns.drop("_ts_key")]
            .copy()
            .reset_index(drop=True)
        )
        df_gt_sub = (
            df_pose.loc[mask, df_gt.columns.drop("_ts_key")]
            .copy()
            .reset_index(drop=True)
        )

        for _, row in df_rgb_sub.iterrows():
            rel_path = row['path_rgb_0']
            full_src = os.path.abspath(parent_sequence_path / rel_path)
            full_dst = os.path.abspath(sequence_path / rel_path)
            if os.path.exists(full_dst) or os.path.islink(full_dst):
                os.remove(full_dst)
            os.symlink(full_src, full_dst)

        df_rgb_sub.to_csv(rgb_csv, index=False, sep=',')
        df_gt_sub.to_csv(gt_csv, index=False, sep=',')
    
    def download_combined_subsequence(self, sequence_name):
        sequence_path: Path = self.dataset_path / sequence_name
        rgb_path: Path = sequence_path / "rgb_0"
        rgb_csv: Path = sequence_path / "rgb.csv"
        gt_csv: Path = sequence_path / "groundtruth.csv"
        if rgb_path.exists():
            return
        rgb_path.mkdir(parents=True, exist_ok=True)
        
        dfs_rgb = []
        dfs_pose = []
        for subset in self.combined.get(sequence_name):
            parent_sequence_path: Path = self.dataset_path / subset
            parent_rgb_csv: Path = parent_sequence_path / "rgb.csv"
            parent_gt_csv: Path = parent_sequence_path / "groundtruth.csv"
            dfs_rgb.append(pd.read_csv(parent_rgb_csv))
            dfs_pose.append(pd.read_csv(parent_gt_csv))
            for _, row in dfs_rgb[-1].iterrows():
                rel_path = row['path_rgb_0']
                full_src = os.path.abspath(os.path.join(parent_sequence_path, rel_path))
                full_dst = os.path.abspath(os.path.join(sequence_path, rel_path))
                if os.path.exists(full_dst) or os.path.islink(full_dst):
                    os.remove(full_dst)
                os.symlink(full_src, full_dst)
            df_rgb_all = pd.concat(dfs_rgb, ignore_index=True)
            df_pose_all = pd.concat(dfs_pose, ignore_index=True)
            df_rgb_all.to_csv(rgb_csv, index=False, sep=',')
            df_pose_all.to_csv(gt_csv, index=False, sep=',')
    
    def create_rgb_folder(self, sequence_name: str) -> None:
        pass
    
    def create_rgb_csv(self, sequence_name: str) -> None:
        pass
    
    def create_calibration_yaml(self, sequence_name: str) -> None:
        fx, fy, cx, cy = 541.5, 541.5, 370, 207.5
        k1, k2, p1, p2 = -0.08, 0.10, 0.0, 0.0
        rgb0: dict[str, Any] = {"cam_name": "rgb_0", "cam_type": "rgb",
            "cam_model": "pinhole", "focal_length": [fx, fy], "principal_point": [cx, cy],
            "distortion_coefficients": [k1, k2, p1, p2],
            "distortion_type": "radtan4",
            "fps": float(self.rgb_hz),
            "T_BS": np.eye(4)}
        self.write_calibration_yaml(sequence_name=sequence_name, rgb=[rgb0])
    
    def create_groundtruth_csv(self, sequence_name: str) -> None:
        pass

    def remove_unused_files(self, sequence_name: str) -> None:
        pass
