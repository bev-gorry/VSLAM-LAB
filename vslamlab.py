"""
Module: VSLAM-LAB - vslamlab.py
- Author: Alejandro Fontan Villacampa
- Version: 1.0
- Created: 2024-07-04
- Updated: 2024-07-04
- License: GPLv3 License
- List of Known Dependencies;
    * ...
"""

import argparse
import glob
import os
import sys
import time
import shutil
import re
import yaml
from inputimeout import inputimeout, TimeoutOccurred
from tqdm import tqdm

from Compare import compare_functions
from Datasets.dataset_utilities import get_dataset
from utilities import COMPARISONS_YAML_DEFAULT
from utilities import CONFIG_DEFAULT
from utilities import EXP_YAML_DEFAULT
from utilities import Experiment
from utilities import VSLAMLAB_BENCHMARK
from utilities import VSLAMLAB_EVALUATION
from utilities import VSLAM_LAB_DIR
from utilities import check_yaml_file_integrity
from utilities import list_datasets
from utilities import ws

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "


def main():
    # Parse inputs
    parser = argparse.ArgumentParser(description=f"{__file__}")

    parser.add_argument('--exp_yaml', nargs='?', type=str,
                        const=EXP_YAML_DEFAULT, default=EXP_YAML_DEFAULT,
                        help=f"Path to the YAML file containing the list of experiments. "
                             f"Default \'vslamlab --exp_yaml {EXP_YAML_DEFAULT}\'")

    parser.add_argument('-download', action='store_true', help="If none 'download/run/evaluate/compare' are activated, "
                                                               "all work by default.")
    parser.add_argument('-run', action='store_true', help="")
    parser.add_argument('-evaluate', action='store_true', help="")
    parser.add_argument('-compare', action='store_true', help="")

    parser.add_argument('--list_datasets', action='store_true', help="List available datasets.")

    parser.add_argument('-ablation', action='store_true', help="")

    args = parser.parse_args()

    if not os.path.exists(VSLAMLAB_EVALUATION):
        os.makedirs(VSLAMLAB_EVALUATION, exist_ok=True)

    # Stuff to run demo
    if not os.path.exists(os.path.join(VSLAMLAB_EVALUATION, "exp_demo_dso")):
        shutil.copytree(os.path.join(VSLAM_LAB_DIR, "docs", "exp_demo_dso"),
                        os.path.join(VSLAMLAB_EVALUATION, "exp_demo_dso"))
    if not os.path.exists(os.path.join(VSLAMLAB_EVALUATION, "exp_demo_orbslam2")):
        shutil.copytree(os.path.join(VSLAM_LAB_DIR, "docs", "exp_demo_orbslam2"),
                        os.path.join(VSLAMLAB_EVALUATION, "exp_demo_orbslam2"))

    print(f"\n{SCRIPT_LABEL}Created folder to store data: {VSLAMLAB_BENCHMARK}")
    print(f"{SCRIPT_LABEL}Created folder to store evaluation: {VSLAMLAB_EVALUATION}")

    # Info commands
    if args.list_datasets:
        print_datasets()
        return

    # Load experiment info
    experiments, config_files = load_experiments(args.exp_yaml)
    check_config_integrity(config_files)

    # Process experiments
    filter_inputs(args)
    if args.download:
        download(config_files)

    if args.run:
        run(experiments, args.exp_yaml, args.ablation)

    if args.evaluate:
        evaluate(experiments)

    if args.compare:
        compare(experiments, args.exp_yaml)


def filter_inputs(args):
    if not args.download and not args.run and not args.evaluate and not args.compare:
        args.download = True
        args.run = True
        args.evaluate = True
        args.compare = True


def check_parameter_for_relative_path(parameter_value):
    if "VSLAM-LAB" in parameter_value:
        if ":" in parameter_value:
            return re.sub(r'(?<=:)[^:]*VSLAM-LAB', VSLAM_LAB_DIR, str(parameter_value))
        return re.sub(r'^.*VSLAM-LAB', VSLAM_LAB_DIR, str(parameter_value))
    return parameter_value


def load_experiments(exp_yaml):
    """
    Loads experiment configurations from a YAML file and initializes Experiment objects.

    Parameters
    ----------
    exp_yaml : str
        Path to the YAML file containing experiment settings (default: VSLAM-LAB/docs/experimentList.yaml).

    Returns
    ----------
    experiments : dict
        experiments<exp_name,Experiment()>
    config_files : dict
        config_files<config_yaml,False>
    """

    check_yaml_file_integrity(exp_yaml)

    with open(exp_yaml, 'r') as file:
        experiment_data = yaml.safe_load(file)

    experiments = {}
    config_files = {}
    for exp_name, settings in experiment_data.items():
        experiment = Experiment()
        active = settings.get('Active', True)
        if not active:
            continue

        experiments[exp_name] = experiment
        experiments[exp_name].config_yaml = os.path.join(VSLAM_LAB_DIR, 'configs',
                                                         settings.get('Config', CONFIG_DEFAULT))
        config_files[experiments[exp_name].config_yaml] = False
        experiments[exp_name].folder = os.path.join(VSLAMLAB_EVALUATION, exp_name)
        experiments[exp_name].num_runs = settings.get('NumRuns', 1)
        experiments[exp_name].module = settings.get('Module', "default")

        if settings['Parameters']:
            for parameter_name in settings['Parameters']:
                experiments[exp_name].parameters.append(
                    check_parameter_for_relative_path(settings['Parameters'][parameter_name]))

    print(f"\n{SCRIPT_LABEL}Experiment summary: {os.path.basename(exp_yaml)}")
    print(f"{ws(4)} Number of experiments: {len(experiments)}")
    #print(f"{ws(4)} Estimated data size: - ")
    #run_time = estimate_experiments_time(experiments)
    #if run_time > 60.0:
    #    print(f"{ws(4)} Estimated running time: {run_time/60.0} (h)")
    #else:
    #    print(f"{ws(4)} Estimated running time: {run_time} (min)")

    return experiments, config_files


def compare(experiments, exp_yaml):
    comparison_path = os.path.join(VSLAMLAB_EVALUATION, f"comp_{str(os.path.basename(exp_yaml)).replace('.yaml', '')}")
    print(f"\n{SCRIPT_LABEL}Create folder to save comparison: {comparison_path}")
    print(f"\n{SCRIPT_LABEL}Comparing (in {comparison_path}) ...")
    if os.path.exists(comparison_path):
        shutil.rmtree(comparison_path)
    os.makedirs(comparison_path)
    os.makedirs(os.path.join(comparison_path, 'figures'))
    compare_functions.full_comparison(experiments, VSLAMLAB_BENCHMARK, COMPARISONS_YAML_DEFAULT, comparison_path)


def evaluate(experiments):
    print(f"\n{SCRIPT_LABEL}Evaluating (in {VSLAMLAB_EVALUATION}) ...")
    for [_, exp] in experiments.items():
        with open(exp.config_yaml, 'r') as file:
            config_file_data = yaml.safe_load(file)
            for dataset_name, sequence_names in config_file_data.items():
                dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                for sequence_name in sequence_names:
                    dataset.evaluate_sequence(sequence_name, exp.folder)


def run(experiments, exp_yaml, ablation=False, ):
    print(f"\n{SCRIPT_LABEL}Running experiments (in {exp_yaml}) ...")
    start_time = time.time()

    while True:
        experiments_ = {}
        remaining_time = 0
        for [exp_name, exp] in experiments.items():
            remaining_iterations = 0
            with open(exp.config_yaml, 'r') as file:
                config_file_data = yaml.safe_load(file)
                for dataset_name, sequence_names in config_file_data.items():
                    dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                    for sequence_name in sequence_names:
                        sequence_folder = os.path.join(exp.folder, dataset_name.upper(), sequence_name)
                        num_system_output_files = 0
                        if os.path.exists(sequence_folder):
                            search_pattern = os.path.join(sequence_folder, f'*system_output_*')
                            num_system_output_files = len(glob.glob(search_pattern))

                        remaining_iterations_seq = exp.num_runs - num_system_output_files
                        remaining_iterations += remaining_iterations_seq
                        if num_system_output_files < exp.num_runs:
                            exp_id = num_system_output_files
                            print(
                                f"{ws(4)}Running (it: {num_system_output_files + 1}/{exp.num_runs}) '{exp.module}' "
                                f"in: '{sequence_name}'...")
                            duration_time = dataset.run_sequence(exp, sequence_name, exp_id, ablation)
                            remaining_time += (remaining_iterations_seq - 1) * duration_time

            if remaining_iterations > 0:
                experiments_[exp_name] = exp

        if len(experiments_) == 0:
            break

        experiments = experiments_
        if remaining_time > 1:
            print(f"\033[93m[Remaining time until completion: {remaining_time:.2f} seconds]\033[0m")

    run_time = (time.time() - start_time) / 60.0
    if run_time > 60.0:
         print(f"\033[93m[Experiment runtime: {run_time / 60.0} hours]\033[0m")
    else:
         print(f"\033[93m[Experiment runtime: {run_time} minutes]\033[0m")


def download(config_files):
    download_issues = find_download_issues(config_files)
    solve_download_issues(download_issues)

    print(f"\n{SCRIPT_LABEL}Downloading (to {VSLAMLAB_BENCHMARK}) ...")

    for config_file in config_files:
        with open(config_file, 'r') as file:
            config_file_data = yaml.safe_load(file)
            for dataset_name, sequence_names in config_file_data.items():
                dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                for sequence_name in sequence_names:
                    dataset.download_sequence(sequence_name)


def check_config_integrity(config_files):
    dataset_list = list_datasets()
    for config_file in config_files:
        check_yaml_file_integrity(config_file)
        with open(config_file, 'r') as file:
            config_file_data = yaml.safe_load(file)
            for dataset_name, sequence_names in config_file_data.items():
                if not (dataset_name in dataset_list):
                    print(f"\n{SCRIPT_LABEL}Error in : {config_file}")
                    print(f"{ws(4)}'{dataset_name}' dataset doesn't exist")
                    print_datasets()
                    sys.exit(1)

                dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                for sequence_name in sequence_names:
                    if not dataset.contains_sequence(sequence_name):
                        print(f"\n{SCRIPT_LABEL}Error in : {config_file}")
                        print(f"{ws(4)}'{dataset_name}' dataset doesn't contain sequence '{sequence_name}'")
                        print(f"\nAvailable sequences are: {dataset.sequence_names}")
                        print(f"")
                        sys.exit(1)


def print_datasets():
    dataset_list = list_datasets()
    print(f"\n{SCRIPT_LABEL}Accessible datasets in VSLAM-LAB:")
    for dataset in dataset_list:
        print(f" - {dataset}")
    print("")


def estimate_experiments_time(experiments):
    running_time = 0
    for [exp_name, exp] in experiments.items():
        with open(exp.config_yaml, 'r') as file:
            config_file_data = yaml.safe_load(file)
            for dataset_name, sequence_names in config_file_data.items():
                dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                for sequence_name in sequence_names:
                    num_frames = dataset.get_sequence_num_rgb(sequence_name)
                    running_time += exp.num_runs * num_frames / dataset.rgb_hz
    return 1.5 * running_time / 60


def find_download_issues(config_files):
    download_issues = {}
    for config_file in config_files:
        with open(config_file, 'r') as file:
            config_file_data = yaml.safe_load(file)
            for dataset_name, sequence_names in config_file_data.items():
                dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                download_issues[dataset.dataset_name] = {}
                for sequence_name in sequence_names:
                    sequence_availabilty = dataset.check_sequence_availability(sequence_name)
                    if sequence_availabilty != "available":
                        issues_seq = dataset.get_download_issues(sequence_name)
                        if issues_seq == {}:
                            continue
                        for issue_name, issue_topic in issues_seq.items():
                            download_issues[dataset.dataset_name][issue_name] = issue_topic

    print(f"\n{SCRIPT_LABEL}Finding download issues...")
    num_download_issues = 0
    for dataset_name, issues_dataset in download_issues.items():
        for issue_name, issue_topic in issues_dataset.items():
            print(f"{ws(4)}[{dataset_name}][{issue_name}]: {issue_topic}")
            num_download_issues += 1

    if num_download_issues > 0:
        message = (f"\n{SCRIPT_LABEL}Found download issues: your experiments have {num_download_issues} download "
                   f"issues. Would you like to continue solving them and download the datasets (Y/n):")
        try:
            user_input = inputimeout(prompt=message, timeout=120).strip().upper()
        except TimeoutOccurred:
            user_input = 'Y'
            print("        No input detected. Defaulting to 'Y'.")
        if user_input != 'Y':
            exit()
    else:
        message = (f"{ws(4)}Found download issues: your experiments have {num_download_issues} download "
                   f"issues.")
        print(message)
        download_issues = {}

    return download_issues


def solve_download_issues(download_issues):
    if download_issues == {}:
        return

    print(f"\n{SCRIPT_LABEL}Solving download issues: ")
    for dataset_name, issues_dataset in download_issues.items():
        dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
        for download_issue in issues_dataset.items():
            dataset.solve_download_issue(download_issue)


if __name__ == "__main__":
    main()
