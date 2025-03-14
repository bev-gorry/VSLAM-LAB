import os, shutil, yaml, argparse

from Evaluate import compare_functions
from utilities import filter_inputs, print_msg
from Datasets.get_dataset import get_dataset
from Evaluate.evaluate_functions import evaluate_sequence
from path_constants import VSLAMLAB_BENCHMARK, VSLAMLAB_EVALUATION
from path_constants import COMPARISONS_YAML_DEFAULT, EXP_YAML_DEFAULT
from vslamlab_utilities import load_experiments, check_config_integrity

SCRIPT_LABEL = f"\033[95m[{os.path.basename(__file__)}]\033[0m "

def main():

    parser = argparse.ArgumentParser(description=f"{__file__}")

    parser.add_argument('--exp_yaml', nargs='?', type=str,
                        const=EXP_YAML_DEFAULT, default=EXP_YAML_DEFAULT,
                        help=f"Path to the YAML file containing the list of experiments. "
                             f"Default \'vslamlab --exp_yaml {EXP_YAML_DEFAULT}\'")

    parser.add_argument('-download', action='store_true', help="")
    parser.add_argument('-run', action='store_true', help="")
    parser.add_argument('-evaluate', action='store_true', help="")
    parser.add_argument('-compare', action='store_true', help="")
    parser.add_argument('-overwrite', action='store_true', help="")

    args = parser.parse_args()

    # Load experiment info
    experiments, config_files = load_experiments(args.exp_yaml, overwrite=False)
    check_config_integrity(config_files)

    # Process experiments
    filter_inputs(args)
    if args.evaluate:
        evaluate(experiments, args.overwrite)

    if args.compare:
        compare(experiments, args.exp_yaml)

def compare(experiments, exp_yaml):
    comparison_path = os.path.join(VSLAMLAB_EVALUATION, f"comp_{str(os.path.basename(exp_yaml)).replace('.yaml', '')}")
    print_msg(f"\n{SCRIPT_LABEL}", f"Comparing (in {comparison_path}) ...")
    if os.path.exists(comparison_path):
        shutil.rmtree(comparison_path)
    os.makedirs(comparison_path)
    os.makedirs(os.path.join(comparison_path, 'figures'))
    compare_functions.full_comparison(experiments, VSLAMLAB_BENCHMARK, COMPARISONS_YAML_DEFAULT, comparison_path)


def evaluate(experiments, overwrite):
    print_msg(f"\n{SCRIPT_LABEL}", f"Evaluating (in {VSLAMLAB_EVALUATION}) ...")
    for [_, exp] in experiments.items():
        with open(exp.config_yaml, 'r') as file:
            config_file_data = yaml.safe_load(file)
            for dataset_name, sequence_names in config_file_data.items():
                dataset = get_dataset(dataset_name, VSLAMLAB_BENCHMARK)
                for sequence_name in sequence_names:
                    evaluate_sequence(exp, dataset, sequence_name, overwrite)

if __name__ == "__main__":
    main()
