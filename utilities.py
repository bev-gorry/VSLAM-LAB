import os
import sys
import tarfile
import urllib.request
import zipfile

import yaml
from PIL import Image

VSLAM_LAB_DIR = os.path.dirname(os.path.abspath(__file__))
VSLAM_LAB_PATH = os.path.dirname(VSLAM_LAB_DIR)

VSLAMLAB_BENCHMARK = os.path.join(VSLAM_LAB_PATH, 'VSLAM-LAB-Benchmark')
VSLAMLAB_EVALUATION = os.path.join(VSLAM_LAB_PATH, 'VSLAM-LAB-Evaluation')
VSLAMLAB_BASELINES = os.path.join(VSLAM_LAB_DIR, 'Baselines')

COMPARISONS_YAML_DEFAULT = os.path.join(VSLAM_LAB_DIR, 'configs', 'comp_complete.yaml')
EXP_YAML_DEFAULT = os.path.join(VSLAM_LAB_DIR, 'configs', 'exp_demo.yaml')
CONFIG_DEFAULT = 'config_demo.yaml'

VSLAM_LAB_EVALUATION_FOLDER = 'vslamlab_evaluation'
RGB_BASE_FOLDER = 'rgb'

class Experiment:
    def __init__(self):
        self.config_yaml = ""
        self.folder = ""
        self.num_runs = 1
        self.parameters = []
        self.module = ""


def list_datasets():
    dataset_scripts_path = os.path.join(VSLAM_LAB_DIR, 'Datasets')
    dataset_scripts = []
    for filename in os.listdir(dataset_scripts_path):
        if 'dataset_' in filename and filename.endswith('.yaml'):
            dataset_scripts.append(filename)

    dataset_scripts = [item.replace('dataset_', '').replace('.yaml', '') for item in dataset_scripts]

    return dataset_scripts


def ws(n):
    white_spaces = ""
    for i in range(0, n):
        white_spaces = white_spaces + " "
    return white_spaces


def find_files_with_string(folder_path, matching_string):
    matching_files = []
    for file_name in os.listdir(folder_path):
        if matching_string in file_name:
            file_path = os.path.join(folder_path, file_name)
            matching_files.append(file_path)
    matching_files.sort()
    return matching_files


def check_yaml_file_integrity(yaml_file):
    if not os.path.exists(yaml_file):  # Check if file exists
        print(f"Error: The file '{yaml_file}' does not exist.")
        sys.exit(1)
    if not yaml_file.lower().endswith(('.yaml', '.yml')):  # Check if the file is a yaml file
        print(f"Error: The file '{yaml_file}' is not a yaml file.")
        sys.exit(1)
    try:  # Check the integrity of the yaml file
        with open(yaml_file, 'r') as file:
            yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading the file '{yaml_file}': {e}")
        sys.exit(1)


def find_common_sequences(experiments):
    num_experiments = len(experiments)
    exp_tmp = {}
    for [_, exp] in experiments.items():
        with open(exp.config_yaml, 'r') as file:
            config_file_data = yaml.safe_load(file)
            for dataset_name, sequence_names in config_file_data.items():
                if not (dataset_name in exp_tmp):
                    exp_tmp[dataset_name] = {}
                for sequence_name in sequence_names:
                    if sequence_name in exp_tmp[dataset_name]:
                        exp_tmp[dataset_name][sequence_name] += 1
                    else:
                        exp_tmp[dataset_name][sequence_name] = 1

    dataset_sequences = {}
    for [dataset_name, sequence_names] in exp_tmp.items():
        for [sequence_name, num_sequences] in sequence_names.items():
            if num_experiments == num_sequences:
                if dataset_name not in dataset_sequences:
                    dataset_sequences[dataset_name] = []
                dataset_sequences[dataset_name].append(sequence_name)
    return dataset_sequences


# Functions to download files

# Downloads the given URL to a file in the given directory. Returns the
# path to the downloaded file.
# Taken from https://www.eth3d.net/slam_datasets/download_eth3d_slam_datasets.py.
def downloadFile(url, dest_dir_path):
    file_name = url.split('/')[-1]
    dest_file_path = os.path.join(dest_dir_path, file_name)

    url_object = urllib.request.urlopen(url)

    with open(dest_file_path, 'wb') as outfile:
        meta = url_object.info()
        if sys.version_info[0] == 2:
            file_size = int(meta.getheaders("Content-Length")[0])
        else:
            file_size = int(meta["Content-Length"])
        print("    Downloading: %s (size [bytes]: %s)" % (url, file_size))

        file_size_downloaded = 0
        block_size = 8192
        while True:
            buffer = url_object.read(block_size)
            if not buffer:
                break

            file_size_downloaded += len(buffer)
            outfile.write(buffer)

            sys.stdout.write("        %d / %d  (%3f%%)\r" % (
                file_size_downloaded, file_size, file_size_downloaded * 100. / file_size))
            sys.stdout.flush()

    return dest_file_path


def decompressFile(filepath, extract_to=None):
    """
    Decompress a .zip, .tar.gz, or .tar file and return the extraction directory.
    """
    if not extract_to:
        extract_to = os.path.dirname(filepath)

    if filepath.endswith('.zip'):
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            for file in zip_ref.namelist():
                try:
                    zip_ref.extract(file, extract_to)
                except zipfile.BadZipFile:
                    print(f"Skipping corrupted file: {file}")
    elif filepath.endswith('.tar.gz') or filepath.endswith('.tgz') or filepath.endswith('.tar'):
        mode = 'r:gz' if filepath.endswith('.gz') else 'r'
        with tarfile.open(filepath, mode) as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        print("Unsupported file format. Please provide a .zip, .tar.gz, or .tar file.")
        return None


def replace_string_in_files(directory, old_string, new_string):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.h') or file.endswith('.cpp'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = content.replace(old_string, new_string)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)


def is_image_file(file_path):
    try:
        with Image.open(file_path) as img:
            return True
    except Exception:
        return False


def list_image_files_in_folder(folder_path):
    image_files = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and is_image_file(file_path):
            image_files.append(filename)
    return image_files
    
def set_VSLAMLAB_path(new_path, file_path, target_line_start):
    new_line = f"{target_line_start} \"{new_path}\""
    print(f"Set {new_path}")
    with open(file_path, 'r') as file:
        lines = file.readlines()

    with open(file_path, 'w') as file:
        for line in lines:
            if line.strip().startswith(target_line_start):
                file.write(new_line + '\n')
            else:
                file.write(line)

def check_sequence_integrity(dataset_path, sequence_name, verbose):
    sequence_path = os.path.join(dataset_path, sequence_name)
    rgb_path = os.path.join(sequence_path, 'rgb')
    rgb_txt = os.path.join(sequence_path, 'rgb.txt')
    calibration_yaml = os.path.join(sequence_path, "calibration.yaml")

    complete_sequence = True
    if not os.path.exists(sequence_path):
        if verbose:
            print(f"        The folder {sequence_path} doesn't exist !!!!!")
        complete_sequence = False

    if not os.path.exists(rgb_path):
        if verbose:
            print(f"        The folder {rgb_path} doesn't exist !!!!!")
        complete_sequence = False

    if not os.path.exists(rgb_txt):
        if verbose:
            print(f"        The file {rgb_txt} doesn't exist !!!!!")
        complete_sequence = False

    if not os.path.exists(calibration_yaml):
        if verbose:
            print(f"        The file {calibration_yaml} doesn't exist !!!!!")
        complete_sequence = False

    return complete_sequence

if __name__ == "__main__":

    if len(sys.argv) > 2:
        function_name = sys.argv[1]
        if function_name == 'set_VSLAMLAB_BENCHMARK_path':
            set_VSLAMLAB_path(os.path.join(sys.argv[2], 'VSLAM-LAB-Benchmark'), __file__, "VSLAMLAB_BENCHMARK =")
        if function_name == 'set_VSLAMLAB_EVALUATION_path':
            set_VSLAMLAB_path(os.path.join(sys.argv[2], 'VSLAM-LAB-Evaluation'), __file__, "VSLAMLAB_EVALUATION =")    
