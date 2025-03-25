import os.path
from Baselines.BaselineVSLAMLab import BaselineVSLAMLab


class COLMAP_baseline(BaselineVSLAMLab):
    def __init__(self):
        baseline_name = 'colmap'
        baseline_folder = 'colmap'
        default_parameters = {'verbose': 1, 'matcher_type': 'sequential', 'use_gpu': 1}

        # Initialize the baseline
        super().__init__(baseline_name, baseline_folder, default_parameters)

    def build_execute_command(self, exp_it, exp, dataset, sequence_name):
        vslamlab_command = super().build_execute_command_cpp(exp_it, exp, dataset, sequence_name)
        vslamlab_command = f"pixi run -e {self.baseline_name} execute " + ' '.join(vslamlab_command)

        return vslamlab_command

    def is_installed(self):
        return os.path.isfile(os.path.join(self.baseline_path, 'bin', 'colmap'))

    def info_print(self):
        super().info_print()
        print(f"Default executable: Baselines/colmap/bin/colmap")