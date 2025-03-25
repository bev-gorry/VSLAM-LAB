import os, yaml

from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from utilities import downloadFile, decompressFile

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
        for i, nickname in enumerate(self.sequence_nicknames):
            if len(nickname) > 15:
                self.sequence_nicknames[i] = nickname[:15]

    def download_sequence_data(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)

        # Variables
        compressed_name_ext = sequence_name + '_mono' + '.zip'
        decompressed_name = sequence_name

        download_url = os.path.join(self.url_download_root, 'datasets', compressed_name_ext)

        # Constants
        compressed_file = os.path.join(self.dataset_path, compressed_name_ext)
        decompressed_folder = os.path.join(self.dataset_path, decompressed_name)

        # Download the compressed file
        if not os.path.exists(compressed_file):
            downloadFile(download_url, self.dataset_path)

        # Decompress the file
        if not os.path.exists(decompressed_folder):
            decompressFile(compressed_file, self.dataset_path)
            groundtruth_txt = os.path.join(sequence_path, 'groundtruth.txt')
            os.rename(groundtruth_txt, groundtruth_txt.replace('groundtruth.txt', 'groundtruth_raw.txt'))

    def create_calibration_yaml(self, sequence_name):

        sequence_path = os.path.join(self.dataset_path, sequence_name)
        calibration_txt = os.path.join(sequence_path, 'calibration.txt')
        with open(calibration_txt, 'r') as file:
            calibration = [value for value in file.readline().split()]

        fx, fy, cx, cy = calibration[0], calibration[1], calibration[2], calibration[3]
        k1, k2, p1, p2, k3 = 0.0, 0.0, 0.0, 0.0, 0.0

        self.write_calibration_yaml('PINHOLE', fx, fy, cx, cy, k1, k2, p1, p2, k3, sequence_name)

    def create_groundtruth_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        groundtruth_txt = os.path.join(sequence_path, 'groundtruth.txt')
        groundtruth_csv = os.path.join(sequence_path, 'groundtruth.csv')
        groundtruth_raw_txt = os.path.join(sequence_path, 'groundtruth_raw.txt')
        
        with open(groundtruth_raw_txt, 'r') as file:
            lines = file.readlines()

        number_of_grountruth_header_lines = 1
        new_lines = lines[number_of_grountruth_header_lines:]
        with open(groundtruth_txt, 'w') as file:
            file.writelines(new_lines)

        header = "ts,tx,ty,tz,qx,qy,qz,qw\n"
        new_lines.insert(0, header)
        with open(groundtruth_csv, 'w') as file:
            for line in new_lines:
                values = line.split()
                file.write(','.join(values) + '\n')
        
    def remove_unused_files(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        os.remove(os.path.join(sequence_path, 'calibration.txt'))