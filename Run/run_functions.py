# Run methods

import time
import os
import subprocess

from utilities import ws
from Baselines.baseline_utilities import log_run_sequence_time
from Baselines.baseline_utilities import append_ablation_parameters_to_csv

from Run import ablations

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "


def run_sequence(exp, baseline, exp_it, dataset, sequence_name, ablation=False):
    print(f"{SCRIPT_LABEL}Running (it {exp_it + 1}/{exp.num_runs}) {baseline.label} in {dataset.dataset_color}{sequence_name}\033[0m of {dataset.dataset_label} ...")
    run_time_start = time.time()

    sequence_path = os.path.join(dataset.dataset_path, sequence_name)

    exp_folder = os.path.join(exp.folder, dataset.dataset_folder, sequence_name)
    if not os.path.exists(exp_folder):
        os.makedirs(exp_folder, exist_ok=True)

    log_file_path = os.path.join(exp_folder, "system_output_" + str(exp_it).zfill(5) + ".txt")

    exec_command = [f"sequence_path:{sequence_path}", f"exp_folder:{exp_folder}", f"exp_id:{exp_it}"]
    i_par = 0
    for parameter in exp.parameters:
        exec_command += [str(parameter)]
        i_par += 1

    command_str = ' '.join(exec_command)

    full_command = f"pixi run -e {baseline.baseline_name} execute " + command_str

    if ablation:
        settings_yaml = prepare_ablation(sequence_name, exp, exp_it, exp_folder, dataset)
    run_executable(full_command, log_file_path)
    if ablation:
        finish_ablation(sequence_name, settings_yaml, dataset)

    duration_time = time.time() - run_time_start
    log_run_sequence_time(exp_folder, exp_it, duration_time)
    return duration_time


def run_executable(command, log_file_path):
    with open(log_file_path, 'w') as log_file:
        print(f"{ws(6)} log file: {log_file_path}")
        subprocess.run(command, stdout=log_file, stderr=log_file, shell=True)


####################################################################################################################

# Ablation methods
def prepare_ablation(sequence_name, exp, it, exp_folder, dataset):
    print(f"{ws(8)}Sequence '{sequence_name}' preparing ablation ...")
    for parameter in exp.parameters:
        if 'settings_yaml' in parameter:
            settings_yaml = parameter.replace('settings_yaml:', '')
        if 'ablation_param' in parameter:
            ablation_param = parameter.replace('ablation_param:', '')

    ablation_parameters = {}
    ablation_parameters['expId'] = str(it).zfill(5)
    ablation_parameters_csv = os.path.join(exp_folder, 'log_ablation_parameters.csv')

    # Define your ablations
    sequence_path = os.path.join(dataset.dataset_path, sequence_name)

    ablation_parameters_i = ablations.add_noise_to_images_start(sequence_path, it, exp, dataset.rgb_hz)
    ablation_parameters.update(ablation_parameters_i)

    ablation_parameters_i = ablations.parameter_ablation_start(it, ablation_param, settings_yaml)
    ablation_parameters.update(ablation_parameters_i)

    append_ablation_parameters_to_csv(ablation_parameters_csv, ablation_parameters)

    return settings_yaml


def finish_ablation(sequence_name, settings_yaml, dataset):
    print(f"{ws(8)}Sequence '{sequence_name}' finishing ablation ...")
    sequence_path = os.path.join(dataset.dataset_path, sequence_name)
    ablations.add_noise_to_images_finish(sequence_path)
    ablations.parameter_ablation_finish(settings_yaml)
