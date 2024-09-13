import os
import yaml
import shutil
from inputimeout import inputimeout, TimeoutOccurred

from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from utilities import downloadFile
from utilities import decompressFile

from Evaluate.align_trajectories import align_trajectory_with_groundtruth
from Evaluate import metrics


class TARTANAIR_dataset(DatasetVSLAMLab):
    def __init__(self, benchmark_path):
        # Initialize the dataset
        super().__init__('tartanair', benchmark_path)

        # Load settings from .yaml file
        with open(self.yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        # Get download url
        self.url_download_root = data['url_download_root']
        self.url_download_gt_root = data['url_download_gt_root']

        # Create sequence_nicknames
        self.sequence_nicknames = self.sequence_names

    def download_sequence_data(self, sequence_name):

        # Variables
        compressed_name = 'tartanair-test-mono-release'
        compressed_name_ext = compressed_name + '.tar.gz'
        decompressed_name = compressed_name
        download_url = os.path.join(self.url_download_root, compressed_name_ext)

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

        # Decompress the file
        if not os.path.exists(decompressed_folder):
            decompressFile(compressed_file, os.path.join(self.dataset_path, compressed_name))

        # Download the gt
        if not os.path.exists(os.path.join(self.dataset_path, 'tartanair_cvpr_gt')):
            compressed_name = '3p1sf0eljfwrz4qgbpc6g95xtn2alyfk'
            compressed_name_ext = compressed_name + '.zip'
            decompressed_name = 'tartanair_cvpr_gt'

            compressed_file = os.path.join(self.dataset_path, compressed_name_ext)
            decompressed_folder = os.path.join(self.dataset_path, decompressed_name)

            download_url = self.url_download_gt_root
            if not os.path.exists(compressed_file):
                downloadFile(download_url, self.dataset_path)

            decompressFile(compressed_file, os.path.join(self.dataset_path, decompressed_name))

    def create_rgb_folder(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_path = os.path.join(sequence_path, 'rgb')
        if not os.path.exists(rgb_path):
            os.makedirs(rgb_path)

        rgb_path_0 = os.path.join(self.dataset_path, 'tartanair-test-mono-release', 'mono', sequence_name)
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

        rgb_files = [f for f in os.listdir(rgb_path) if os.path.isfile(os.path.join(rgb_path, f))]
        rgb_files.sort()
        with open(rgb_txt, 'w') as file:
            for iRGB, filename in enumerate(rgb_files, start=0):
                name, ext = os.path.splitext(filename)
                ts = float(name) / self.rgb_hz
                file.write(f"{ts:.5f} rgb/{filename}\n")

    def create_calibration_yaml(self, sequence_name):

        fx, fy, cx, cy = 320.0, 320.0, 320.0, 240.0
        k1, k2, p1, p2, k3 = 0.0, 0.0, 0.0, 0.0, 0.0

        self.write_calibration_yaml('OPENCV', fx, fy, cx, cy, k1, k2, p1, p2, k3, sequence_name)

    def create_groundtruth_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        groundtruth_txt = os.path.join(sequence_path, 'groundtruth.txt')

        gt_txt = os.path.join(self.dataset_path, 'tartanair_cvpr_gt', 'mono_gt', sequence_name + '.txt')
        with open(gt_txt, 'r') as source_file:
            with open(groundtruth_txt, 'w') as destination_file:
                for iRgb, line in enumerate(source_file):
                    values = line.strip().split()
                    ts = iRgb / self.rgb_hz
                    values.insert(0, '{:.5f}'.format(ts))
                    destination_file.write(" ".join(values) + "\n")
        os.remove(gt_txt)

    def remove_unused_files(self, sequence_name):
        dataset_folder = os.path.join(self.dataset_path, 'tartanair-test-mono-release', 'mono')
        if os.path.exists(dataset_folder):
            if not os.listdir(dataset_folder):
                shutil.rmtree(os.path.join(self.dataset_path, 'tartanair-test-mono-release'))

        gt_folder = os.path.join(self.dataset_path, 'tartanair_cvpr_gt', 'mono_gt')
        if os.path.exists(gt_folder):
            if not os.listdir(gt_folder):
                shutil.rmtree(os.path.join(self.dataset_path, 'tartanair_cvpr_gt'))