import os.path
from Baselines.BaselineVSLAMLab import BaselineVSLAMLab


class ORBSLAM2_baseline(BaselineVSLAMLab):
    def __init__(self):
        baseline_name = 'orbslam2'
        baseline_folder = 'ORB_SLAM2'
        
        # Initialize the baseline
        super().__init__(baseline_name, baseline_folder)

        self.default_parameters = {'verbose': 1,
                                   'vocabulary': os.path.join(self.baseline_path, 'Vocabulary', 'ORBvoc.txt'),
                                   'mode': 'mono'}
        self.color = 'blue'

    def build_execute_command(self, exp_it, exp, dataset, sequence_name):

        vslamlab_command = super().build_execute_command_cpp(exp_it, exp, dataset, sequence_name)

        mode = self.default_parameters['mode']
        if 'mode' in exp.parameters:
            mode = exp.parameters['mode']

        if mode == "mono":
            vslamlab_command = vslamlab_command.replace('execute', 'execute_mono')
        if mode == "rgbd":
            vslamlab_command = vslamlab_command.replace('execute', 'execute_rgbd')

        return vslamlab_command

    def is_installed(self):
        return (os.path.isfile(os.path.join(self.baseline_path, 'bin', 'mono')) and
                os.path.isfile(os.path.join(self.baseline_path, 'bin', 'rgbd')))

    def info_print(self):
        super().info_print()
        print(f"Default executable: Baselines/ORB_SLAM2/bin/mono")
        print(f"Default executable: Baselines/ORB_SLAM2/bin/rgbd")

    def modify_yaml_parameter(self,yaml_file, section_name, parameter_name, new_value):
        with open(yaml_file, 'r') as file:
            lines = file.readlines()

        modified_lines = []
        for line in lines:
            if f"{section_name}.{parameter_name}" in line:
                line = f"{section_name}.{parameter_name}: {new_value}\n"
            modified_lines.append(line)

        with open(yaml_file, 'w') as file:
            file.writelines(modified_lines)