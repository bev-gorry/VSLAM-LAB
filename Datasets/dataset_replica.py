import os
import yaml
import shutil
import numpy as np
from scipy.spatial.transform import Rotation as R
from inputimeout import inputimeout, TimeoutOccurred

from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from utilities import downloadFile
from utilities import decompressFile
from utilities import VSLAMLAB_BENCHMARK
from utilities import ws

from Evaluate.align_trajectories import align_trajectory_with_groundtruth
from Evaluate import metrics


class REPLICA_dataset(DatasetVSLAMLab):
    def __init__(self, benchmark_path):
        # Initialize the dataset
        super().__init__('replica', benchmark_path)

        # Load settings from .yaml file
        with open(self.yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        # Get download url
        self.url_download_root = data['url_download_root']

        # Create sequence_nicknames
        self.sequence_nicknames = [s.replace('_', ' ') for s in self.sequence_names]

    def download_sequence_data(self, sequence_name):

        # Variables
        compressed_name = "Replica"
        compressed_name_ext = compressed_name + '.zip'
        decompressed_name = self.dataset_name.upper()
        download_url = self.url_download_root

        # Constants
        compressed_file = os.path.join(VSLAMLAB_BENCHMARK, compressed_name_ext)
        decompressed_folder = os.path.join(VSLAMLAB_BENCHMARK, decompressed_name)

        # Download the compressed file
        if not os.path.exists(compressed_file):
            downloadFile(download_url, VSLAMLAB_BENCHMARK)

        # Decompress the file
        if os.path.exists(self.dataset_path):
            if not os.listdir(self.dataset_path):
                shutil.rmtree(self.dataset_path)

        if not os.path.exists(decompressed_folder):
            decompressFile(compressed_file, VSLAMLAB_BENCHMARK)
            os.rename(os.path.join(VSLAMLAB_BENCHMARK, 'Replica'), decompressed_folder)

    def create_rgb_folder(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        results_path = os.path.join(sequence_path, 'results')
        rgb_path = os.path.join(sequence_path, 'rgb')

        if not os.path.exists(rgb_path):
            os.rename(results_path, rgb_path)
            for filename in os.listdir(rgb_path):
                if 'depth' in filename:
                    file_path = os.path.join(rgb_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                if 'frame' in filename:
                    old_file = os.path.join(rgb_path, filename)
                    new_file = os.path.join(rgb_path, filename.replace('frame', ''))
                    os.rename(old_file, new_file)

    def create_rgb_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_path = os.path.join(sequence_path, 'rgb')
        rgb_txt = os.path.join(sequence_path, 'rgb.txt')

        rgb_files = [f for f in os.listdir(rgb_path) if os.path.isfile(os.path.join(rgb_path, f))]
        rgb_files.sort()
        with open(rgb_txt, 'w') as file:
            for iRGB, filename in enumerate(rgb_files, start=0):
                name, ext = os.path.splitext(filename)
                ts = float(name) / self.rgb_hz
                file.write(f"{ts:.5f} rgb/{filename}\n")

    def create_calibration_yaml(self, sequence_name):

        fx, fy, cx, cy = 600.0, 600.0, 599.5, 339.5
        k1, k2, p1, p2, k3 = 0.0, 0.0, 0.0, 0.0, 0.0

        self.write_calibration_yaml('OPENCV', fx, fy, cx, cy, k1, k2, p1, p2, k3, sequence_name)

    def create_groundtruth_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        groundtruth_txt = os.path.join(sequence_path, 'groundtruth.txt')
        rgb_txt = os.path.join(sequence_path, 'rgb.txt')

        rgb_timestamps = []
        with open(rgb_txt, 'r') as file:
            for line in file:
                timestamp, path = line.strip().split(' ')
                rgb_timestamps.append(float(timestamp))

        groundtruth_txt_0 = os.path.join(sequence_path, 'traj.txt')
        with open(groundtruth_txt_0, 'r') as source_file, open(groundtruth_txt, 'w') as destination_file:
            for idx, line in enumerate(source_file, start=0):
                line = line.strip()
                values = line.split(' ')
                rotation_matrix = np.array([[values[0], values[1], values[2]],
                                            [values[4], values[5], values[6]],
                                            [values[8], values[9], values[10]]])
                rotation = R.from_matrix(rotation_matrix)
                quaternion = rotation.as_quat()
                ts = rgb_timestamps[idx]
                tx, ty, tz = values[3], values[7], values[11]
                qx, qy, qz, qw = quaternion[0], quaternion[1], quaternion[2], quaternion[3]
                line2 = f"{ts:.5f}" + " " + str(tx) + " " + str(ty) + " " + str(tz) + " " + str(qx) + " " + str(
                    qy) + " " + str(qz) + " " + str(qw) + "\n"
                destination_file.write(line2)

    def remove_unused_files(self, sequence_name):
        return

    def get_download_issues(self, sequence_name):
        issues = {'Complete dataset': f"The \'{self.dataset_name}\' dataset does not permit downloading individual sequences."}

        return issues

    def solve_download_issue(self, download_issue):
        if download_issue[0] == 'Complete dataset':
            print(f"{ws(4)}[{self.dataset_name}][{download_issue[0]}]: {download_issue[1]} ")
            message = f"{ws(8)}Would you like to continue downloading the full dataset (12 GB) (Y/n): "
            try:
                user_input = inputimeout(prompt=message, timeout=10).strip().upper()
            except TimeoutOccurred:
                user_input = 'Y'
                print(f"{ws(8)}No input detected. Defaulting to 'Y'.")
            if user_input != 'Y':
                exit()

    def download_process(self, _):
        for sequence_name in self.sequence_names:
            super().download_process(sequence_name)
