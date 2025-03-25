import os.path
from Baselines.BaselineVSLAMLab import BaselineVSLAMLab


class DPVO_baseline(BaselineVSLAMLab):
    def __init__(self):
        baseline_name = 'dpvo'
        baseline_folder = 'DPVO'
        default_parameters = {'verbose': 1}
        

        # Initialize the baseline
        super().__init__(baseline_name, baseline_folder, default_parameters)
        self.color = 'red'

    def build_execute_command(self, exp_it, exp, dataset, sequence_name):
        vslamlab_command = super().build_execute_command_python(exp_it, exp, dataset, sequence_name)
        return vslamlab_command

    def is_installed(self):
        return os.path.isfile(os.path.join(self.baseline_path, 'dpvo.pth'))

    def info_print(self):
        super().info_print()
        print(f"Default executable: {self.baseline_path}/vslamlab_{self.baseline_name}_mono.py")