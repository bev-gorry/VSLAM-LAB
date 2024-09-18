"""
Module: VSLAM-LAB - Datasets - DatasetVSLAMLab.py
- Author: Alejandro Fontan Villacampa
- Version: 1.0
- Created: 2024-07-12
- Updated: 2024-07-12
- License: GPLv3 License
- List of Known Dependencies;
    * ...

DatasetVSLAMLab: A class to handle Visual SLAM dataset-related operations.
Specifically downloading sequences, running experiments, and evaluating results.

"""

import os
import sys
from tqdm import tqdm

import cv2
import yaml

from utilities import VSLAM_LAB_DIR
from utilities import find_files_with_string
from utilities import ws
from utilities import check_sequence_integrity
from Evaluate.evo import evo_ape_zip
from Evaluate.evo import evo_get_accuracy

SCRIPT_LABEL = f"[{os.path.basename(__file__)}] "


class DatasetVSLAMLab:

    def __init__(self, dataset_name, benchmark_path):

        # Init dataset paths
        self.dataset_name = dataset_name
        self.dataset_color = "\033[38;2;255;165;0m"
        self.dataset_label = f"{self.dataset_color}{dataset_name}\033[0m"
        self.dataset_folder = dataset_name.upper()
        self.benchmark_path = benchmark_path
        self.dataset_path = os.path.join(self.benchmark_path, self.dataset_folder)

        self.yaml_file = os.path.join(VSLAM_LAB_DIR, 'Datasets', 'dataset_' + self.dataset_name + '.yaml')

        with open(self.yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        self.sequence_names = data['sequence_names']
        self.rgb_hz = data['rgb_hz']
        self.sequence_nicknames = []

    ####################################################################################################################
    # Download methods
    def download_sequence(self, sequence_name):

        # Check if sequence is already available
        sequence_availability = self.check_sequence_availability(sequence_name)
        if sequence_availability == "available":
            print(f"{ws(4)}Sequence '{sequence_name}' is already downloaded.")
            return
        if sequence_availability == "corrupted":
            print(f"{ws(8)}Some files in sequence {sequence_name} are corrupted.")
            print(f"{ws(8)}Removing and downloading again sequence {sequence_name} ")
            print(f"{ws(8)}THIS PART OF THE CODE IS NOT YET IMPLEMENTED. REMOVE THE FILES MANUALLY")
            sys.exit(1)

        # Download process
        if not os.path.exists(self.dataset_path):
            os.makedirs(self.dataset_path, exist_ok=True)

        self.download_process(sequence_name)

    def download_process(self, sequence_name):
        msg = f"Downloading sequence '{sequence_name}' from dataset '{self.dataset_name}' ..."
        print(SCRIPT_LABEL + msg)
        self.download_sequence_data(sequence_name)
        self.create_rgb_folder(sequence_name)
        self.create_rgb_txt(sequence_name)
        self.create_calibration_yaml(sequence_name)
        self.create_groundtruth_txt(sequence_name)
        self.remove_unused_files(sequence_name)

    def download_sequence_data(self, sequence_name):
        return

    def create_rgb_folder(self, sequence_name):
        return

    def create_rgb_txt(self, sequence_name):
        return

    def create_calibration_yaml(self, sequence_name):
        return

    def create_groundtruth_txt(self, sequence_name):
        return

    def remove_unused_files(self, sequence_name):
        return

    def get_download_issues(self, sequence_name):
        return {}

    def solve_download_issue(self, download_issue):
        return

    def write_calibration_yaml(self, camera_model, fx, fy, cx, cy, k1, k2, p1, p2, k3, sequence_name):

        sequence_path = os.path.join(self.dataset_path, sequence_name)
        calibration_yaml = os.path.join(sequence_path, 'calibration.yaml')

        rgb_path = os.path.join(sequence_path, 'rgb')
        rgb_files = [f for f in os.listdir(rgb_path) if os.path.isfile(os.path.join(rgb_path, f))]
        image_0 = cv2.imread(os.path.join(rgb_path, rgb_files[0]))
        h, w, channels = image_0.shape

        yaml_content_lines = [
            "%YAML:1.0",
            "",
            "# Camera calibration and distortion parameters",
            "Camera.model: " + camera_model,
            "",
            "Camera.fx: " + str(fx),
            "Camera.fy: " + str(fy),
            "Camera.cx: " + str(cx),
            "Camera.cy: " + str(cy),
            "",
            "Camera.k1: " + str(k1),
            "Camera.k2: " + str(k2),
            "Camera.p1: " + str(p1),
            "Camera.p2: " + str(p2),
            "Camera.k3: " + str(k3),
            "",
            "Camera.w: " + str(w),
            "Camera.h: " + str(h),
            "",
            "# Camera frames per second",
            "Camera.fps: " + str(self.rgb_hz)
        ]

        with open(calibration_yaml, 'w') as file:
            for line in yaml_content_lines:
                file.write(f"{line}\n")

    def check_sequence_availability(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        if os.path.exists(sequence_path):
            sequence_complete = check_sequence_integrity(self.dataset_path, sequence_name, True)
            if sequence_complete:
                return "available"
            else:
                return "corrupted"
        return "non-available"

    ####################################################################################################################
    # Evaluation methods

    def evaluate_sequence(self, sequence_name, experiment_folder):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        groundtruth_file = os.path.join(sequence_path, 'groundtruth.txt')

        trajectories_path = os.path.join(experiment_folder, self.dataset_folder, sequence_name)
        evaluation_folder = os.path.join(trajectories_path, 'vslamlab_evaluation')

        os.makedirs(evaluation_folder, exist_ok=True)
        trajectory_files = find_files_with_string(trajectories_path, "_KeyFrameTrajectory.txt")
        print(f"{ws(4)}Evaluation of '{os.path.basename(experiment_folder)}"
              f"' in '{sequence_name}': {len(trajectory_files)} trajectories")

        for trajectory_file in tqdm(trajectory_files):
            self.evaluate_trajectory_accuracy(groundtruth_file, trajectory_file, evaluation_folder)

        self.get_accuracy(evaluation_folder)

    def evaluate_trajectory_accuracy(self, groundtruth_file, trajectory_file, evaluation_folder):
        evo_ape_zip(groundtruth_file, trajectory_file, evaluation_folder, 1.0 / self.rgb_hz)

    def get_accuracy(self, evaluation_folder):
        evo_get_accuracy(evaluation_folder)

    ####################################################################################################################
    # Utils

    def contains_sequence(self, sequence_name_ref):
        for sequence_name in self.sequence_names:
            if sequence_name == sequence_name_ref:
                return True
        return False

    def print_sequence_names(self):
        print(self.sequence_names)

    def print_sequence_nicknames(self):
        print(self.sequence_nicknames)

    def get_sequence_names(self):
        return self.sequence_names

    def get_sequence_nicknames(self):
        return self.sequence_nicknames

    def get_sequence_nickname(self, sequence_name_ref):
        for i, sequence_name in enumerate(self.sequence_names):
            if sequence_name == sequence_name_ref:
                return self.sequence_nicknames[i]

    def get_sequence_num_rgb(self, sequence_name):
        rgb_txt = os.path.join(self.dataset_path, sequence_name, 'rgb.txt')
        if os.path.exists(rgb_txt):
            with open(rgb_txt, 'r') as file:
                line_count = 0
                for line in file:
                    line_count += 1
            return line_count
        return 0
