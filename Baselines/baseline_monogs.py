import os.path
from Baselines.BaselineVSLAMLab import BaselineVSLAMLab


class MONOGS_baseline(BaselineVSLAMLab):
    def __init__(self):
        baseline_name = 'monogs'
        baseline_folder = 'MonoGS_VSLAMLAB'

        # Initialize the baseline
        super().__init__(baseline_name, baseline_folder)

        self.default_parameters = {'verbose': 1,
                                   'config_yaml': f'{os.path.join(self.baseline_path, 'configs', 'vslamlab', 'vslamlab.yaml')}',
                                   'mode': 'mono'}

    def build_execute_command(self, exp_it, exp, dataset, sequence_name):
        vslamlab_command = super().build_execute_command_python(exp_it, exp, dataset, sequence_name)

        mode = self.default_parameters['mode']
        if 'mode' in exp.parameters:
            mode = exp.parameters['mode']

        if mode == "mono":
            vslamlab_command = vslamlab_command.replace('vslamlab.yaml', 'vslamlab_mono.yaml')
        if mode == "rgbd":
            vslamlab_command = vslamlab_command.replace('vslamlab.yaml', 'vslamlab_rgbd.yaml')

        return vslamlab_command

    def is_installed(self):
        return (os.path.isdir(os.path.join(self.baseline_path, 'submodules', 'simple-knn', 'build')) and
                os.path.isdir(os.path.join(self.baseline_path, 'submodules', 'diff-gaussian-rasterization', 'build')))

    def info_print(self):
        super().info_print()
        print(f"Default executable: Baselines/MonoGS_VSLAMLAB/slam.py")
