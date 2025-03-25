import os, sys, shutil

from utilities import print_msg
from vslamlab_utilities import Experiment
from Run.run_functions import run_sequence
from Datasets.get_dataset import get_dataset
from Baselines.baseline_utilities import get_baseline
from path_constants import VSLAMLAB_BENCHMARK, VSLAMLAB_EVALUATION


SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "


def main():
    baseline_name = sys.argv[1]
    dataset_name = sys.argv[2]
    sequence_name = sys.argv[3]

    exp = Experiment('demo', os.path.join(VSLAMLAB_EVALUATION, 'demo'), 1, 'default', {}, 'config_debug.yaml', None, False)
    exp.config_yaml = ""
    exp.folder = os.path.join(VSLAMLAB_EVALUATION, 'demo')
    exp.module = baseline_name

    if os.path.exists(exp.folder):
        shutil.rmtree(exp.folder)
    os.makedirs(exp.folder, exist_ok=True)

    baseline = get_baseline(baseline_name)
    exp.parameters = baseline.get_default_parameters()

    dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)

    print_msg(f"\n{SCRIPT_LABEL}", f"Running {baseline.label} in {dataset.dataset_label} / {dataset.dataset_color}{sequence_name} ...")
    dataset.download_sequence(sequence_name)
    run_sequence(0, exp, baseline, dataset, sequence_name)

if __name__ == "__main__":
    main()
