import os, yaml, shutil
import numpy as np
from Datasets.DatasetVSLAMLab import DatasetVSLAMLab
from Datasets.dataset_utilities import undistort_rgb_rad_tan, resize_rgb_images


SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "

class ANTARCTICA_dataset(DatasetVSLAMLab):
    def __init__(self, benchmark_path):
        # Initialize the dataset
        super().__init__('antarctica', benchmark_path)

        # Load settings from .yaml file
        with open(self.yaml_file, 'r') as file:
            data = yaml.safe_load(file)

        # Get download url
        self.url_download_root = data['url_download_root']

        # Create sequence_nicknames
        self.sequence_nicknames = [s.replace('_', ' ') for s in self.sequence_names]

    def download_sequence_data(self, sequence_name):
        
        # # Variables
        # sequence_path_0 = os.path.join(self.dataset_folder_raw, sequence_name)
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        # rgb_path = os.path.join(sequence_path, 'rgb')
        #
        # if not os.path.exists(os.path.normpath(sequence_path_0)):
        #     print(f'The dataset root cannot be found, please correct the root filepath or place the images in the directory: {sequence_path_0}')
        #     exit(0)
        #
        if not os.path.exists(sequence_path):
             os.makedirs(sequence_path)
        #
        # for file in os.listdir(sequence_path_0):
        #     if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
        #         with Image.open(os.path.join(sequence_path_0, file)) as img:
        #             scaled_width = int(img.size[0] * self.resolution_scale)
        #
        #             # Ensure new_width is even
        #             if scaled_width % 2 != 0:
        #                 scaled_width -= 1
        #             scaled_height = int(scaled_width * img.size[1] / img.size[0])
        #
        #             # Resize image
        #             resized_img = img.resize((scaled_width, scaled_height), Image.LANCZOS)
        #             resized_img.save(os.path.join(rgb_path, file))

    def create_rgb_folder(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_path = os.path.join(sequence_path, 'rgb')
        source_rgb_path  = os.path.join(self.dataset_path,'ROI_01','Q3_2024-01-11_P1', sequence_name)
        if os.path.exists(rgb_path):
            return

        os.makedirs(rgb_path, exist_ok=True)       
        for file_name in os.listdir(source_rgb_path):
            if file_name.lower().endswith('.jpg'):
                source_file = os.path.join(source_rgb_path, file_name)
                destination_file = os.path.join(rgb_path, file_name)
                shutil.copy2(source_file, destination_file)
    

    def create_rgb_txt(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_path = os.path.join(sequence_path, 'rgb')
        rgb_txt = os.path.join(sequence_path, 'rgb.txt')
        
        frame_duration = 1.0 / self.rgb_hz
        
        rgb_files = [f for f in os.listdir(rgb_path) 
             if os.path.isfile(os.path.join(rgb_path, f)) and f.lower().endswith('.jpg')]

        rgb_files.sort()
        with open(rgb_txt, 'w') as file:
            for iRGB, filename in enumerate(rgb_files, start=0):
                ts = iRGB * frame_duration
                file.write(f"{ts:.5f} rgb/{filename}\n")

    def create_calibration_yaml(self, sequence_name):
        sequence_path = os.path.join(self.dataset_path, sequence_name)
        rgb_txt = os.path.join(sequence_path, 'rgb.txt')
        fx, fy, cx, cy, k1, k2, p1, p2, k3 = (
            8154.29, 8154.29, 4076.2906, 2787.575 , -0.0331103, 0.0312571, -0.00133488, 0.00277011, -0.109366)
        
        camera_matrix = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        distortion_coeffs = np.array([k1, k2, p1, p2, k3])
        
        fx, fy, cx, cy = resize_rgb_images(rgb_txt, sequence_path, 640, 480, camera_matrix)
        camera_matrix = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]])
        fx, fy, cx, cy = undistort_rgb_rad_tan(rgb_txt, sequence_path, camera_matrix, distortion_coeffs)

        self.write_calibration_yaml('OPENCV', fx, fy, cx, cy, 0.0, 0.0, 0.0, 0.0, 0.0, sequence_name)

    def create_groundtruth_txt(self, sequence_name):
        return

    def remove_unused_files(self, sequence_name):
        return
        # sequence_path = os.path.join(self.dataset_path, sequence_name)
        # glomap_results = os.path.join(sequence_path, 'colmap_00000')
        # glomap_keyframe_trajectory = os.path.join(sequence_path, '00000_KeyFrameTrajectory.txt')
        # glomap_calibration_log_file = os.path.join(sequence_path, 'calibration_log_file.txt')
        # glomap_build_log_file = os.path.join(sequence_path, 'glomap_build_log_file.txt')
        #
        # if os.path.exists(glomap_results):
        #     shutil.rmtree(glomap_results)
        #
        # if os.path.exists(glomap_keyframe_trajectory):
        #     os.remove(glomap_keyframe_trajectory)
        # if os.path.exists(glomap_calibration_log_file):
        #     os.remove(glomap_calibration_log_file)
        # if os.path.exists(glomap_build_log_file):
        #     os.remove(glomap_build_log_file)

    def evaluate_trajectory_accuracy(self, trajectory_txt, groundtruth_txt):
        return
