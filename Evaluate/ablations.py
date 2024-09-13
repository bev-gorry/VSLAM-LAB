import os
import cv2
import shutil
import numpy as np
import yaml

from utilities import VSLAM_LAB_BASELINES_DIR
from utilities import RGB_BASE_FOLDER
from snippets.downsample_rgb_frames import downsample_rgb_frames

SCRIPT_LABEL = f"\033[35m[{os.path.basename(__file__)}]\033[0m "

def modify_yaml_parameter(yaml_file, section_name, parameter_name, new_value):

    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    if section_name in data and parameter_name in data[section_name]:
        data[section_name][parameter_name] = new_value
        print(f"Parameter '{parameter_name}' in section '{section_name}' updated to '{new_value}'.")
    else:
        print(f"Parameter '{parameter_name}' or section '{section_name}' not found in the YAML file.")

    # Write the changes back to the YAML file
    with open(yaml_file, 'w') as file:
        yaml.safe_dump(data, file)

    print(f"YAML file '{yaml_file}' has been updated.")

def parameter_ablation_start(it, ablation_param, settings_yaml):
    settings_saved_yaml = settings_yaml.replace('_settings', '_settings_original')

    if os.path.exists(settings_saved_yaml):
        shutil.copy(settings_saved_yaml, settings_yaml)
    else:
        shutil.copy(settings_yaml, settings_saved_yaml)

    value = 10 ** ((it/20) - 5)
    print(f"ablation value = {value}")

    section_name, parameter_name = ablation_param.split('.', 1)
    modify_yaml_parameter(settings_yaml, section_name, parameter_name, value)

def parameter_ablation_finish(settings_yaml):
    settings_saved_yaml = settings_yaml.replace('_settings', '_settings_original')
    shutil.copy(settings_saved_yaml, settings_yaml)
    os.remove(settings_saved_yaml)

def add_noise_to_images_start(sequence_path, it, exp, fps):
    max_rgb = 50
    min_fps = fps
    for parameter in exp.parameters:
        if 'max_rgb' in parameter:
            max_rgb = float(parameter.replace('max_rgb:', ''))
        if 'min_fps' in parameter:
            min_fps = float(parameter.replace('min_fps:', ''))

    # Rename the rgb folder to rgb_saved and create a new rgb folder
    rgb_path = os.path.join(sequence_path, RGB_BASE_FOLDER)
    rgb_path_saved = os.path.join(sequence_path, f"{RGB_BASE_FOLDER}_saved")
    if not os.path.exists(rgb_path_saved):
        os.rename(rgb_path, rgb_path_saved)
    os.makedirs(os.path.join(sequence_path, RGB_BASE_FOLDER), exist_ok=True)

    # update rgb.txt
    rgb_txt = os.path.join(sequence_path, f"{RGB_BASE_FOLDER}.txt")
    rgb_txt_ds = os.path.join(sequence_path, f"{RGB_BASE_FOLDER}_ds.txt")

    downsampled_paths, downsampled_timestamps = downsample_rgb_frames(rgb_txt, max_rgb, min_fps, True)

    with open(rgb_txt_ds, 'w') as file:
        for timestamp, path in zip(downsampled_timestamps, downsampled_paths):
            file.write(f"{timestamp} {path}\n")

    # Noise policy
    std_noise = it * 1.0
    print(f"{SCRIPT_LABEL} Noise policy: std_noise = 50 + it * 1.0")
    print(f"    it = {it}")
    print(f"    std_noise = {std_noise}")

    def add_gaussian_noise(image_, mean=0, std_dev=25):
        noise = np.random.normal(mean, std_dev, image_.shape).astype(np.float32)
        noisy_image_ = image_ + noise
        noisy_image_ = np.clip(noisy_image_, 0, 255).astype(np.uint8)
        return noisy_image_

    for i, downsampled_path in enumerate(downsampled_paths):
        rgb_file = os.path.join(sequence_path, downsampled_path)
        rgb_file_saved = rgb_file.replace(f"/{RGB_BASE_FOLDER}/", f"/{RGB_BASE_FOLDER}_saved/")
        image = cv2.imread(rgb_file_saved)
        noisy_image = add_gaussian_noise(image, mean=0, std_dev=std_noise)
        cv2.imwrite(os.path.join(sequence_path, rgb_file), noisy_image)

def add_noise_to_images_finish(sequence_path):

    # Remove rgb_ds.txt
    rgb_txt_ds = os.path.join(sequence_path, f"{RGB_BASE_FOLDER}_ds.txt")
    os.remove(rgb_txt_ds)

    # Restore rgb folder
    rgb_path = os.path.join(sequence_path, 'rgb')
    rgb_path_saved = os.path.join(sequence_path, 'rgb_saved')
    shutil.rmtree(rgb_path)
    os.rename(rgb_path_saved, rgb_path)
