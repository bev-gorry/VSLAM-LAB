import os.path
from Baselines.BaselineVSLAMLab import BaselineVSLAMLab


class GLOMAP_baseline(BaselineVSLAMLab):
    def __init__(self):
        baseline_name = 'glomap'
        baseline_folder = 'glomap'
        default_parameters = {'verbose': 1, 'matcher_type': 'sequential', 'use_gpu': 1, 'max_rgb': 100}

        # Initialize the baseline
        super().__init__(baseline_name, baseline_folder, default_parameters)

    def build_execute_command(self, exp_it, exp, dataset, sequence_name):
        return super().build_execute_command_cpp(exp_it, exp, dataset, sequence_name)

    def is_installed(self):
        return os.path.isfile(os.path.join(self.baseline_path, 'bin', 'glomap'))

    def info_print(self):
        super().info_print()
        print(f"Default executable: Baselines/glomap/bin/glomap")


