import os.path
from Baselines.BaselineVSLAMLab import BaselineVSLAMLab


class DROIDSLAM_baseline(BaselineVSLAMLab):
    def __init__(self):
        baseline_name = 'droidslam'
        baseline_folder = 'DROID-SLAM'
        default_parameters = {'verbose': 1, 'upsample': 0, 'mode': 'mono'}
        

        # Initialize the baseline
        super().__init__(baseline_name, baseline_folder, default_parameters)
        self.color = 'green'
        
    def build_execute_command(self, exp_it, exp, dataset, sequence_name):
        vslamlab_command = super().build_execute_command_python(exp_it, exp, dataset, sequence_name)

        mode = self.default_parameters['mode']
        if 'mode' in exp.parameters:
            mode = exp.parameters['mode']

        if mode == "mono":
            vslamlab_command = vslamlab_command.replace('execute', 'execute_mono')
        if mode == "rgbd":
            vslamlab_command = vslamlab_command.replace('execute', 'execute_rgbd')

        return vslamlab_command

    def is_installed(self):
        return os.path.isfile(os.path.join(self.baseline_path, 'droid.pth'))

    def info_print(self):
        super().info_print()
        print(f"Default executable: Baselines/DROID-SLAM/droidslam_vslamlab_mono.py")