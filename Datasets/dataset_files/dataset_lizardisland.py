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

from utilities import print_msg
from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from path_constants import Retention, BENCHMARK_RETENTION
from Datasets.DatasetVSLAMLab_issues import _get_dataset_issue

class LIZARDISLAND_dataset(DatasetVSLAMLab):
    """LIZARDISLAND dataset helper for VSLAM-LAB benchmark."""
    
    def __init__(self, benchmark_path: str | Path, dataset_name: str = "lizardisland") -> None:
        pass
    
    def download_sequence_data(self, sequence_name: str) -> None:
        pass
    
    def create_rgb_folder(self, sequence_name: str) -> None:
        pass
    
    def create_rgb_csv(self, sequence_name: str) -> None:
        pass
    
    def create_calibration_yaml(self, sequence_name: str) -> None:
        pass
    
    def create_groundtruth_csv(self, sequence_name: str) -> None:
        pass

    def remove_unused_files(self, sequence_name: str) -> None:
        pass

    def get_download_issues(self, _):
        if self.api_token != "not_set":
            return {}
        return [_get_dataset_issue(issue_id="api_token", dataset_name=self.dataset_name, website=self.url_download_root, yaml_file=self.yaml_file)]
    
    