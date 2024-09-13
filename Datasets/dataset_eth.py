import os
import yaml
import shutil

from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from utilities import downloadFile
from utilities import decompressFile

from Evaluate.align_trajectories import align_trajectory_with_groundtruth
from Evaluate import metrics

from Evaluate.evo import evo_ape_zip

class ETH_dataset(DatasetVSLAMLab):
    def __init__(self, benchmark_path):
        # Initialize the dataset
        super().__init__('eth', benchmark_path)

        # Load settings from .yaml file
        with open(self.yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        # Get download url
        self.url_download_root = data['url_download_root']

        # Create sequence_nicknames
        self.sequence_nicknames = [s.replace('_', ' ') for s in self.sequence_names]

    def download_sequence_data(self, sequence_name):
        # Variables
        compressed_name = sequence_name + '_mono'
        compressed_name_ext = compressed_name + '.zip'
        decompressed_name = sequence_name
        download_url = os.path.join(self.url_download_root, 'datasets', compressed_name_ext)

        # Constants
        compressed_file = os.path.join(self.dataset_path, compressed_name_ext)
        decompressed_folder = os.path.join(self.dataset_path, decompressed_name)

        # Download the compressed file
        if not os.path.exists(compressed_file):
            downloadFile(download_url, self.dataset_path)

        # Decompress the file
        if os.path.exists(decompressed_folder):
            shutil.rmtree(decompressed_folder)
        decompressFile(compressed_file, self.dataset_path)

        # Delete the compressed file
        if os.path.exists(compressed_file):
            os.remove(compressed_file)

    def create_calibration_yaml(self, sequence_name):

        sequence_path = os.path.join(self.dataset_path, sequence_name)
        calibration_txt = os.path.join(sequence_path, 'calibration.txt')
        with open(calibration_txt, 'r') as file:
            calibration = [value for value in file.readline().split()]

        fx, fy, cx, cy = calibration[0], calibration[1], calibration[2], calibration[3]
        k1, k2, p1, p2, k3 = 0.0, 0.0, 0.0, 0.0, 0.0

        self.write_calibration_yaml('OPENCV', fx, fy, cx, cy, k1, k2, p1, p2, k3, sequence_name)

    def create_groundtruth_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        groundtruth_txt = os.path.join(sequence_path, 'groundtruth.txt')
        if not os.path.exists(groundtruth_txt):
            return

        number_of_grountruth_header_lines = 1
        with open(groundtruth_txt, 'r') as file:
            lines = file.readlines()

        with open(groundtruth_txt, 'w') as file:
            file.writelines(lines[number_of_grountruth_header_lines:])

    def remove_unused_files(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        os.remove(os.path.join(sequence_path, 'calibration.txt'))