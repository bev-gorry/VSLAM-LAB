import os
import yaml
import shutil
from inputimeout import inputimeout, TimeoutOccurred
import numpy as np
from scipy.spatial.transform import Rotation as R

from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from utilities import downloadFile
from utilities import decompressFile

from Evaluate.align_trajectories import align_trajectory_with_groundtruth
from Evaluate import metrics


class KITTI_dataset(DatasetVSLAMLab):
    def __init__(self, benchmark_path):

        # Initialize the dataset
        super().__init__('kitti', benchmark_path)

        # Load settings from .yaml file
        with open(self.yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        # Get download url
        self.url_download_root = data['url_download_root']
        self.url_download_root_gt = data['url_download_root_gt']

        # Create sequence_nicknames
        self.sequence_nicknames = self.sequence_names

    def download_sequence_data(self, sequence_name):

        # Variables
        compressed_name = 'data_odometry_gray'
        compressed_name_ext = compressed_name + '.zip'
        decompressed_name = 'dataset'
        download_url = self.url_download_root

        # Constants
        compressed_file = os.path.join(self.dataset_path, compressed_name_ext)
        decompressed_folder = os.path.join(self.dataset_path, decompressed_name)

        # Download the compressed file
        if not os.path.exists(compressed_file):
            message = f"[dataset_{self.dataset_name}.py] The \'{self.dataset_name}\' dataset does not permit downloading individual sequences. Would you like to continue downloading the full dataset (?? GB) (Y/n): "
            try:
                user_input = inputimeout(prompt=message, timeout=10).strip().upper()
            except TimeoutOccurred:
                user_input = 'Y'
                print("        No input detected. Defaulting to 'Y'.")
            if user_input != 'Y':
                exit()
            downloadFile(download_url, self.dataset_path)
            downloadFile(self.url_download_root_gt, self.dataset_path)

        # Decompress the file
        if not os.path.exists(decompressed_folder):
            decompressFile(compressed_file, self.dataset_path)
            decompressFile(os.path.join(self.dataset_path, 'data_odometry_poses.zip'), self.dataset_path)

    def create_rgb_folder(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_path = os.path.join(sequence_path, 'rgb')
        if not os.path.exists(rgb_path):
            os.makedirs(rgb_path)

        rgb_path_0 = os.path.join(self.dataset_path, 'dataset', 'sequences', sequence_name, 'image_0')
        if not os.path.exists(rgb_path_0):
            return

        for png_file in os.listdir(rgb_path_0):
            if png_file.endswith(".png"):
                shutil.move(os.path.join(rgb_path_0, png_file), os.path.join(rgb_path, png_file))

        shutil.rmtree(rgb_path_0)

    def create_rgb_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_path = os.path.join(sequence_path, 'rgb')
        rgb_txt = os.path.join(sequence_path, 'rgb.txt')

        times_txt = os.path.join(self.dataset_path, 'dataset', 'sequences', sequence_name, 'times.txt')
        times = []
        with open(times_txt, 'r') as file:
            lines = file.readlines()
            for line in lines:
                time = line.strip()
                times.append(float(time))

        rgb_files = [f for f in os.listdir(rgb_path) if os.path.isfile(os.path.join(rgb_path, f))]
        rgb_files.sort()
        with open(rgb_txt, 'w') as file:
            for idx, time in enumerate(times, start=0):
                file.write(f"{time} rgb/{rgb_files[idx]}\n")

    def create_calibration_yaml(self, sequence_name):

        calibration_txt = os.path.join(self.dataset_path, 'dataset', 'sequences', sequence_name, 'calib.txt')
        if not os.path.exists(calibration_txt):
            return

        with open(calibration_txt, 'r') as file:
            calibration = [value for value in file.readline().split()]

        fx, fy, cx, cy, k1, k2, p1, p2, k3 = calibration[1], calibration[6], calibration[3], calibration[
            7], 0.0, 0.0, 0.0, 0.0, 0.0

        self.write_calibration_yaml('OPENCV', fx, fy, cx, cy, k1, k2, p1, p2, k3, sequence_name)

    def create_groundtruth_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        groundtruth_txt = os.path.join(sequence_path, 'groundtruth.txt')

        sequence_name_int = int(sequence_name)
        if sequence_name_int > 10:
            return

        times_txt = os.path.join(self.dataset_path, 'dataset', 'sequences', sequence_name, 'times.txt')
        times = []
        with open(times_txt, 'r') as file:
            lines = file.readlines()
            for line in lines:
                time = line.strip()
                times.append(float(time))

        groundtruth_txt_0 = os.path.join(self.dataset_path, 'dataset', 'poses', sequence_name + '.txt')
        with open(groundtruth_txt_0, 'r') as source_file, open(groundtruth_txt, 'w') as destination_file:
            for idx, line in enumerate(source_file, start=0):
                line = line.strip()
                values = line.split(' ')
                rotation_matrix = np.array([[values[0], values[1], values[2]],
                                            [values[4], values[5], values[6]],
                                            [values[8], values[9], values[10]]])
                rotation = R.from_matrix(rotation_matrix)
                quaternion = rotation.as_quat()
                ts = times[idx]
                tx, ty, tz = values[3], values[7], values[11]
                qx, qy, qz, qw = quaternion[0], quaternion[1], quaternion[2], quaternion[3]
                line2 = str(ts) + " " + str(tx) + " " + str(ty) + " " + str(tz) + " " + str(qx) + " " + str(
                    qy) + " " + str(qz) + " " + str(qw) + "\n"
                destination_file.write(line2)

    def remove_unused_files(self, sequence_name):
        sequence_folder = os.path.join(self.dataset_path, 'dataset', 'sequences', sequence_name)
        if os.path.exists(sequence_folder):
            shutil.rmtree(sequence_folder)

        sequences_folder = os.path.join(self.dataset_path, 'dataset', 'sequences')
        if os.path.exists(sequences_folder):
            if not os.listdir(sequences_folder):
                shutil.rmtree(sequences_folder)

        sequence_name_int = int(sequence_name)
        if sequence_name_int < 11:
            groundtruth_txt_0 = os.path.join(self.dataset_path, 'dataset', 'poses', sequence_name + '.txt')
            if os.path.exists(groundtruth_txt_0):
                os.remove(groundtruth_txt_0)

        poses_folder = os.path.join(self.dataset_path, 'dataset', 'poses')
        if os.path.exists(poses_folder):
            if not os.listdir(poses_folder):
                shutil.rmtree(poses_folder)

        dataset_folder = os.path.join(self.dataset_path, 'dataset')
        if os.path.exists(dataset_folder):
            if not os.listdir(dataset_folder):
                shutil.rmtree(dataset_folder)
