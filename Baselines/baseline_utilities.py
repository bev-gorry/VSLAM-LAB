import csv
import os

SCRIPT_LABEL = "[baseline_utilities.py] "

# ADD your imports here
from Baselines.baseline_anyfeature import ANYFEATURE_baseline
from Baselines.baseline_dso import DSO_baseline
from Baselines.baseline_orbslam2 import ORBSLAM2_baseline
from Baselines.baseline_dust3r import DUST3R_baseline
from Baselines.baseline_monogs import MONOGS_baseline
from Baselines.baseline_colmap import COLMAP_baseline
from Baselines.baseline_glomap import GLOMAP_baseline


def get_baseline(baseline_name, baselines_path):
    baseline_name = baseline_name.lower()
    switcher = {
        # ADD your baselines here
        "anyfeature": lambda: ANYFEATURE_baseline(baselines_path),
        "dso": lambda: DSO_baseline(baselines_path),
        "orbslam2": lambda: ORBSLAM2_baseline(baselines_path),
        "dust3r": lambda: DUST3R_baseline(baselines_path),
        "monogs": lambda: MONOGS_baseline(baselines_path),
        "colmap": lambda: COLMAP_baseline(baselines_path),
        "glomap": lambda: GLOMAP_baseline(baselines_path),
    }

    return switcher.get(baseline_name, lambda: "Invalid case")()


def initialize_log_run_sequence_time(csv_path):
    if not os.path.exists(csv_path):
        with open(csv_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['experiment_id', 'runtime'])  # Write the header


def append_to_log_run_sequence_time(csv_path, experiment_id, run_time):
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([experiment_id, run_time])


def log_run_sequence_time(exp_folder, experiment_id, run_time):
    csv_path = os.path.join(exp_folder, 'log_run_sequence_time.csv')
    initialize_log_run_sequence_time(csv_path)
    append_to_log_run_sequence_time(csv_path, experiment_id, run_time)


def append_ablation_parameters_to_csv(file_path, parameter_dict):
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='') as csvfile:
        fieldnames = parameter_dict.keys()

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(parameter_dict)
