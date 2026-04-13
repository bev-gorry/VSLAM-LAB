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

IMAGE_CROP: Final = {"feb": [0,0], "mar": [0,0], "sep": [0,0]}


class LIZARDISLAND_dataset(DatasetVSLAMLab):
    """LIZARDISLAND dataset helper for VSLAM-LAB benchmark."""
    
    def __init__(self, benchmark_path: str | Path, dataset_name: str = "lizardisland") -> None:
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
        raw_path: Path = sequence_path / "raw"
        rgb_path: Path = sequence_path / "rgb_0"
        rgb_csv: Path = sequence_path / "rgb.csv"
        gt_csv: Path = sequence_path / "groundtruth.csv"
        if rgb_path.exists():
            return
        rgb_path.mkdir(parents=True, exist_ok=True)
        raw_path.mkdir(parents=True, exist_ok=True)

        year = '25' if 'sep' in sequence_name else '24'
        local_sequence_path = Path(self.local_raw_data_path) / f"LIRS_{str(sequence_name.capitalize())}_{year}"
        
        print(f"local_sequence_path: {local_sequence_path}")
        if not local_sequence_path.exists():
            print(f"Local sequence path {local_sequence_path} does not exist.")
            return
        
        gps_lookup = self._load_gps_lookup(sequence_name)
        
        image_files = []
        for root, _, files in os.walk(local_sequence_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_files.append(Path(root) / file)
        print_msg(SCRIPT_LABEL, f"Found {len(image_files)} TOTAL images. Starting download...")
        
        origin_latlon: tuple[float, float, float] | None = None
        for f in image_files:
            key = f.name.upper()
            if key in gps_lookup:
                origin_latlon = gps_lookup[key]
                break
        if origin_latlon is None:
            print_msg(SCRIPT_LABEL, "WARNING: No GPS fixes found — groundtruth will be all zeros.")


        with open(rgb_csv, mode='a', newline='') as f_rgb, open(gt_csv, mode='a', newline='') as f_gt:
            writer_rgb = csv.writer(f_rgb, delimiter=',')
            writer_gt  = csv.writer(f_gt, delimiter=',')
            writer_rgb.writerow(["ts_rgb_0 (ns)", "path_rgb_0", "sequence_name"])
            writer_gt.writerow(['ts (ns)', 'tx (m)', 'ty (m)', 'tz (m)', 'qx', 'qy', 'qz', 'qw'])

            rgb_hz = self.rgb_hz
            timestamp_increment = 1_000_000_000 // rgb_hz  
            ts_ns = 0
        
            estimated_new_resolution = False
            new_height, new_width = 0,0
            for src_file in tqdm(image_files, desc="Copying and processing images"):
                rgb_filename = rgb_path / src_file.name
                raw_filename = raw_path / src_file.name
                
                shutil.copy(src_file, raw_filename)
                
                try:
                    with Image.open(raw_filename) as img:
                        width, height = img.size
                        left = 0
                        top = 0
                        right = width - IMAGE_CROP[sequence_name][0]
                        bottom = height - IMAGE_CROP[sequence_name][1]
                        img_cropped = img.crop((left, top, right, bottom))
                        if not estimated_new_resolution:
                            estimated_new_resolution = True
                            new_height = np.sqrt(self.image_resolution[0] * self.image_resolution[1] * img_cropped.size[1] / img_cropped.size[0])
                            new_width = self.image_resolution[0] * self.image_resolution[1] / new_height
                            new_height = int(new_height)
                            new_width = int(new_width)
                            estimated_new_resolution = True
                        img_resized = img_cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        img_resized.save(rgb_filename)
                except Exception as e:
                    print_msg(SCRIPT_LABEL, f"Error processing image {src_file}: {e}")
                    continue
                writer_rgb.writerow([ts_ns, f"rgb_0/{src_file.name}", sequence_name])
                
                key = src_file.name.upper()
                if key in gps_lookup and origin_latlon is not None:
                    lat, lon, alt = gps_lookup[key]
                    tx, ty, tz = self._latlon_to_enu(lat, lon, alt, *origin_latlon)
                else:
                    tx, ty, tz = 0.0, 0.0, 0.0   # no GPS for this frame
                writer_gt.writerow([ts_ns, tx, ty, tz, 0, 0, 0, 1])
                
                ts_ns += timestamp_increment
    
    def create_rgb_folder(self, sequence_name: str) -> None:
        pass
    
    def create_rgb_csv(self, sequence_name: str) -> None:
        pass
    
    def create_calibration_yaml(self, sequence_name: str) -> None:
        fx, fy, cx, cy = 269.31, 269.31, 198.0, 180.0
        k1, k2, p1, p2 = 0, 0, 0, 0
        rgb0: dict[str, Any] = {"cam_name": "rgb_0", "cam_type": "rgb",
            "cam_model": "pinhole", "focal_length": [fx, fy], "principal_point": [cx, cy],
            "distortion_coefficients": [k1, k2, p1, p2],
            "fps": float(self.rgb_hz),
            "T_BS": np.eye(4)}
        self.write_calibration_yaml(sequence_name=sequence_name, rgb=[rgb0])
    
    def create_groundtruth_csv(self, sequence_name: str) -> None:
        pass

    def remove_unused_files(self, sequence_name: str) -> None:
        pass


    def _load_gps_lookup(self, sequence_name: str) -> dict[str, tuple[float, float, float]]:
        """Load GPS CSV(s) and return a dict of {filename_upper: (lat, lon, alt)}."""
        gps_files = []
        
        # Resolve which CSV(s) to load based on sequence name
        year = '25' if 'sep' in sequence_name else '24'
        local_sequence_path = Path(self.local_raw_data_path) / f"LIRS_{str(sequence_name.capitalize())}_{year}"

        base = local_sequence_path / "South_Palfrey_1"
        for gopro_dir in sorted(base.iterdir()):
            for f in gopro_dir.glob("*.csv"):
                print(f"Found GPS file: {f}")
                gps_files.append(f)

        lookup: dict[str, tuple[float, float, float]] = {}
        for csv_path in gps_files:
            with open(csv_path, newline='') as f:
                for row in csv.reader(f):
                    if len(row) < 4:
                        continue
                    fname = row[0].strip().upper()
                    try:
                        lat, lon, alt = float(row[1]), float(row[2]), float(row[3])
                        lookup[fname] = (lat, lon, alt)
                    except ValueError:
                        continue
        return lookup


    def _latlon_to_enu(self, lat: float, lon: float, alt: float, lat0: float, lon0: float, alt0: float) -> tuple[float, float, float]:
        """Convert geodetic coords to local ENU metres relative to (lat0, lon0, alt0)."""
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:4978", always_xy=True)
        # Origin in ECEF
        x0, y0, z0 = transformer.transform(lon0, lat0, alt0)
        # Point in ECEF
        xp, yp, zp = transformer.transform(lon, lat, alt)
        
        import math
        # ENU rotation
        lat0_r = math.radians(lat0)
        lon0_r = math.radians(lon0)
        dx, dy, dz = xp - x0, yp - y0, zp - z0
        
        e = -math.sin(lon0_r)*dx + math.cos(lon0_r)*dy
        n = (-math.sin(lat0_r)*math.cos(lon0_r)*dx
            - math.sin(lat0_r)*math.sin(lon0_r)*dy
            + math.cos(lat0_r)*dz)
        u = (math.cos(lat0_r)*math.cos(lon0_r)*dx
            + math.cos(lat0_r)*math.sin(lon0_r)*dy
            + math.sin(lat0_r)*dz)
        return e, n, u