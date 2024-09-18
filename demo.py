"""
Module: VSLAM-LAB - demo.py
- Author: Alejandro Fontan Villacampa
- Version: 1.0
- Created: 2024-09-13
- Updated: 2024-09-13
- License: GPLv3 License
- List of Known Dependencies;
    * ...
"""

import os
import sys

from Datasets.dataset_utilities import get_dataset
from Baselines.baseline_utilities import get_baseline

from utilities import VSLAMLAB_BENCHMARK
from utilities import Experiment
from utilities import VSLAMLAB_EVALUATION
from utilities import VSLAMLAB_BASELINES

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "


def main():
    baseline_name = sys.argv[1]
    dataset_name = sys.argv[2]
    sequence_name = sys.argv[3]

    exp = Experiment()
    exp.config_yaml = ""
    exp.folder = os.path.join(VSLAMLAB_EVALUATION, 'demo')
    exp.module = baseline_name

    os.makedirs(exp.folder, exist_ok=True)
    baseline = get_baseline(baseline_name, VSLAMLAB_BASELINES)
    exp.parameters = baseline.get_default_parameters()

    dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
    dataset.download_sequence(sequence_name)
    print(f"\n{SCRIPT_LABEL}Running {baseline.label} in {dataset_name}/{sequence_name} ...")
    dataset.run_sequence(exp, sequence_name, 0)


if __name__ == "__main__":
    main()
