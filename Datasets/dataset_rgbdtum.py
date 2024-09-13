import os
import yaml
import shutil

from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from utilities import downloadFile
from utilities import decompressFile

from Evaluate.align_trajectories import align_trajectory_with_groundtruth
from Evaluate import metrics


class RGBDTUM_dataset(DatasetVSLAMLab):
    def __init__(self, benchmark_path):
        # Initialize the dataset
        super().__init__('rgbdtum', benchmark_path)

        # Load settings from .yaml file
        with open(self.yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        # Get download url
        self.url_download_root = data['url_download_root']

        # Create sequence_nicknames
        self.sequence_nicknames = [s.replace('rgbd_dataset_freiburg', 'fr') for s in self.sequence_names]
        self.sequence_nicknames = [s.replace('_', ' ') for s in self.sequence_nicknames]
        self.sequence_nicknames = [s.replace('validation', 'v') for s in self.sequence_nicknames]
        self.sequence_nicknames = [s.replace('structure', 'st') for s in self.sequence_nicknames]
        self.sequence_nicknames = [s.replace('texture', 'tx') for s in self.sequence_nicknames]

    def download_sequence_data(self, sequence_name):
        # Variables
        compressed_name = sequence_name
        compressed_name_ext = compressed_name + '.tgz'
        decompressed_name = sequence_name

        if "freiburg1" in sequence_name:
            camera = "freiburg1"
            decompressed_name = decompressed_name.replace('validation', 'secret')
        if "freiburg2" in sequence_name:
            camera = "freiburg2"
            decompressed_name = decompressed_name.replace('validation', 'secret')
        if "freiburg3" in sequence_name:
            camera = "freiburg3"

        download_url = os.path.join(self.url_download_root, camera, compressed_name_ext)

        # Constants
        compressed_file = os.path.join(self.dataset_path, compressed_name_ext)
        decompressed_folder = os.path.join(self.dataset_path, decompressed_name)

        # Download the compressed file
        if not os.path.exists(compressed_file):
            downloadFile(download_url, self.dataset_path)

        # Decompress the file
        if os.path.exists(decompressed_folder):
            shutil.rmtree(decompressed_folder)

        sequence_path = os.path.join(self.dataset_path, sequence_name)
        decompressFile(compressed_file, self.dataset_path)
        os.rename(decompressed_folder, sequence_path)

        # Delete the compressed file
        if os.path.exists(compressed_file):
            os.remove(compressed_file)

    def create_rgb_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_txt = os.path.join(sequence_path, 'rgb.txt')

        with open(rgb_txt, 'r') as file:
            lines = file.readlines()

        number_of_lines = len(lines)
        rgb_path = os.path.join(sequence_path, 'rgb')
        rgb_files = [f for f in os.listdir(rgb_path) if os.path.isfile(os.path.join(rgb_path, f))]

        if (len(rgb_files) + 3) == number_of_lines:
            new_lines = lines[3:]
            with open(rgb_txt, 'w') as file:
                file.writelines(new_lines)

    def create_calibration_yaml(self, sequence_name):
        if "freiburg1" in sequence_name:
            fx, fy, cx, cy, k1, k2, p1, p2, k3 = (
                517.306408, 516.469215, 318.643040, 255.313989, 0.262383, -0.953104, -0.005358, 0.002628, 1.163314)
        if "freiburg2" in sequence_name:
            fx, fy, cx, cy, k1, k2, p1, p2, k3 = (
                520.908620, 521.007327, 325.1414427, 249.701764, 0.231222, -0.784899, -0.003257, -0.000105, 0.917205)
        if "freiburg3" in sequence_name:
            fx, fy, cx, cy, k1, k2, p1, p2, k3 = 535.4, 539.2, 320.1, 247.6, 0.0, 0.0, 0.0, 0.0, 0.0

        self.write_calibration_yaml('OPENCV', fx, fy, cx, cy, k1, k2, p1, p2, k3, sequence_name)

    def create_groundtruth_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        groundtruth_txt = os.path.join(sequence_path, 'groundtruth.txt')

        if not os.path.exists(groundtruth_txt):
            return

        with open(groundtruth_txt, 'r') as file:
            lines = file.readlines()

        new_lines = lines[3:]
        with open(groundtruth_txt, 'w') as file:
            file.writelines(new_lines)

    def remove_unused_files(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        os.remove(os.path.join(sequence_path, 'accelerometer.txt'))
        os.remove(os.path.join(sequence_path, 'depth.txt'))
        shutil.rmtree(os.path.join(sequence_path, "depth"))