import os, yaml
import csv
import subprocess
import json
import numpy as np
from scipy.spatial.transform import Rotation as R

from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from utilities import downloadFile, decompressFile

class SCANNETPLUSPLUS_dataset(DatasetVSLAMLab):
    def __init__(self, benchmark_path):
        # Initialize the dataset
        super().__init__('scannetplusplus', benchmark_path)

        # Load settings from .yaml file
        with open(self.yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        # Get download url
        self.url_download_root = data['url_download_root']

        # Create sequence_nicknames
        self.sequence_nicknames = [f"scannet_{s[:2]}" for s in self.sequence_names]

    def download_sequence_data(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        if os.path.exists(sequence_path):
            return
        
        data_path = os.path.join(self.dataset_path, 'data', sequence_name)
        if not os.path.exists(data_path):
            SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "
            print(f"\n{SCRIPT_LABEL}\033[91m Data is not available: {data_path}\033[0m")
            print(f"    \033[91m Download from: https://kaldir.vc.in.tum.de/scannetpp/documentation\033[0m")
            exit(0)


    def create_rgb_folder(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_path = os.path.join(sequence_path, 'rgb')
        if not os.path.exists(rgb_path):
            os.makedirs(rgb_path)
            video_path = os.path.join(self.dataset_path, 'data', sequence_name, 'iphone','rgb.mkv')
            command = f"ffmpeg -i {video_path} -start_number 0 -q:v 1 {rgb_path}/frame_%06d.jpg"
            subprocess.run(command, shell=True)

    def create_rgb_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_txt = os.path.join(sequence_path, 'rgb.txt')
        pose_intrinsic_imu_json =  os.path.join(self.dataset_path, 'data', sequence_name, 'iphone', 'pose_intrinsic_imu.json')

        with open(pose_intrinsic_imu_json, "r") as file:
            data = json.load(file)
            with open(rgb_txt, 'w') as file:
                for name, value in data.items():
                    ts = data[name]['timestamp']
                    file.write(f"{ts:.5f} rgb/{name}.jpg\n")
        
        
    def create_calibration_yaml(self, sequence_name):
        pose_intrinsic_imu_json =  os.path.join(self.dataset_path, 'data', sequence_name, 'iphone', 'pose_intrinsic_imu.json')

        fx, fy, cx, cy = 0.0, 0.0, 0.0, 0.0
        with open(pose_intrinsic_imu_json, "r") as file:
            data = json.load(file)
            for name, value in data.items():
                fx += data[name]['intrinsic'][0][0]
                fy += data[name]['intrinsic'][1][1]
                cx += data[name]['intrinsic'][0][2]
                cy += data[name]['intrinsic'][1][2]
        
        fx = fx / len(data)
        fy = fy / len(data)
        cx = cx / len(data)
        cy = cy / len(data)
   
        self.write_calibration_yaml('PINHOLE', fx, fy, cx, cy, 0.0, 0.0, 0.0, 0.0, 0.0, sequence_name)

    def create_groundtruth_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        groundtruth_txt = os.path.join(sequence_path, 'groundtruth.txt')
        groundtruth_csv = os.path.join(sequence_path, 'groundtruth.csv')
        pose_intrinsic_imu_json =  os.path.join(self.dataset_path, 'data', sequence_name, 'iphone', 'pose_intrinsic_imu.json')

        with open(pose_intrinsic_imu_json, "r") as file:
            data = json.load(file)
            with open(groundtruth_txt, 'w') as destination_txt_file:
                for name, value in data.items():
                    ts = data[name]['timestamp']
                    tx = data[name]['aligned_pose'][0][3]
                    ty = data[name]['aligned_pose'][1][3]
                    tz = data[name]['aligned_pose'][2][3]

                    rotation_matrix = np.array([[data[name]['aligned_pose'][0][0], data[name]['aligned_pose'][0][1], data[name]['aligned_pose'][0][2]],
                                                [data[name]['aligned_pose'][1][0], data[name]['aligned_pose'][1][1], data[name]['aligned_pose'][1][2]],
                                                [data[name]['aligned_pose'][2][0], data[name]['aligned_pose'][2][1], data[name]['aligned_pose'][2][2]]])
                    
                    rotation = R.from_matrix(rotation_matrix)
                    quaternion = rotation.as_quat()
                    qx, qy, qz, qw = quaternion[0], quaternion[1], quaternion[2], quaternion[3]
                    line = "{ts}, {tx}, {ty}, {tz}, {qx}, {qy}, {qz}, {qw}\n".format(ts=ts, tx=tx, ty=ty, tz=tz, qx=qx, qy=qy, qz=qz, qw=qw)
                    
                    destination_txt_file.write(f"{ts:.5f} {tx:.5f} {ty:.5f} {tz:.5f} {qx:.5f} {qy:.5f} {qz:.5f} {qw:.5f}\n")
                    #csv_writer.writerow(line)

        # freiburg_txt = [file for file in os.listdir(sequence_path) if 'freiburg' in file.lower()]
        # with open(os.path.join(sequence_path, freiburg_txt[0]), 'r') as source_file:
        #     with open(groundtruth_txt, 'w') as destination_txt_file, \
        #         open(groundtruth_csv, 'w', newline='') as destination_csv_file:

        #         csv_writer = csv.writer(destination_csv_file)
        #         header = ["ts", "tx", "ty", "tz", "qx", "qy", "qz", "qw"]
        #         csv_writer.writerow(header)
        #         for line in source_file:
        #             values = line.strip().split()
        #             values[0] = '{:.8f}'.format(float(values[0]) / self.rgb_hz)
                    
        #             destination_txt_file.write(" ".join(values) + "\n")
        #             csv_writer.writerow(values)

    # def remove_unused_files(self, sequence_name):
    #     sequence_path = os.path.join(self.dataset_path, sequence_name)

    #     os.remove(os.path.join(sequence_path, 'associations.txt'))
    #     shutil.rmtree(os.path.join(sequence_path, "depth"))
