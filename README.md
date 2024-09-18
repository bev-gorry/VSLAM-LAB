<p align="center">

  <h1 align="center"> VSLAM-LAB 
  <h3 align="center"> A Comprehensive Framework for Visual SLAM Baselines and Datasets</h3> 
  </h1>
  <p align="center">
    <a href="https://scholar.google.com/citations?user=SDtnGogAAAAJ&hl=en"><strong>Alejandro Fontan</strong></a>
    ·
    <a href="https://scholar.google.com/citations?user=j_sMzokAAAAJ&hl=en"><strong>Javier Civera</strong></a>
    ·
    <a href="https://scholar.google.com/citations?user=TDSmCKgAAAAJ&hl=en"><strong>Michael Milford</strong></a>
  </p>

**VSLAM-LAB** is designed to simplify the development, evaluation, and application of Visual SLAM (VSLAM) systems. 
This framework enables users to compile and configure VSLAM systems, download and process datasets, and design, run, and
evaluate experiments — **all from a single command line**!

**Why Use VSLAM-LAB?**
- **Unified Framework:** Streamlines the management of VSLAM systems and datasets.
- **Ease of Use:** Run experiments with minimal configuration and single command executions.
- **Broad Compatibility:** Supports a wide range of VSLAM systems and datasets.
- **Reproducible Results:** Standardized methods for evaluating and analyzing results.

## Getting Started

To ensure all dependencies are installed in a reproducible manner, we use the package management tool [**pixi**](https://pixi.sh/latest/). If you haven't installed [**pixi**](https://pixi.sh/latest/) yet, please run the following command in your terminal:
```bash
curl -fsSL https://pixi.sh/install.sh | bash
```
*After installation, restart your terminal or source your shell for the changes to take effect*. For more details, refer to the [**pixi documentation**](https://pixi.sh/latest/).

Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/alejandrofontan/VSLAM-LAB.git && cd VSLAM-LAB
```

## Quick Demo
You can now execute any baseline on any sequence from any dataset within VSLAM-LAB using the following command:
```
pixi run demo <baseline> <dataset> <sequence>
```
For a full list of available systems and datasets, see the [VSLAM-LAB Supported Baselines and Datasets](#vslam-lab-supported-baselines-and-datasets).
Example commands:
```
pixi run demo monogs hamlyn rectified01
pixi run demo orbslam2 rgbdtum rgbd_dataset_freiburg1_xyz
pixi run demo dso monotum sequence_25
pixi run demo glomap eth table_3
```
*To change the paths where VSLAM-LAB-Benchmark or/and VSLAM-LAB-Evaluation data are stored (for example, to /media/${USER}/data), use the following commands:*
```
pixi run set-benchmark-path /media/${USER}/data
pixi run set-evaluation-path /media/${USER}/data
```
## Configure your own experiments
With **VSLAM-LAB**, you can easily design and configure experiments using a YAML file and run them with a single command.
To **run** the experiment demo, execute the following command:
```
pixi run vslamlab --exp_yaml configs/exp_demo.yaml
```
**Note:** *This demo will execute one run per sequence using each VSLAM system. There are 80 pre-executed runs saved in VSLAM-LAB-Evaluation to assist with visualization purposes. The demo uses modified versions of [**ORB-SLAM2**](https://github.com/alejandrofontan/ORB_SLAM2) and [**DSO**](https://github.com/alejandrofontan/dso). Please note that the comparison is between SLAM and Odometry and is intended only as an example of how to use **VSLAM-LAB**.*

Experiments in **VSLAM-LAB** as sequences of entries in a YAML file (see example **~/VSLAM-LAB/configs/exp_demo_short.yaml**):
```
exp_01:
  Module: dso                     # anyfeature/orbslam2/dso/colmap/glomap/dust3r/...
  Parameters: {}                  # Vector with parameters that will be input to the baseline executable 
  Config: config_demo_short.yaml  # YAML file containing the sequences to be run 
  NumRuns: 1                      # Maximum number of executions per sequence
```
**Config** files are YAML files containing the list of sequences to be executed in the experiment (see example **~/VSLAM-LAB/configs/config_demo_short.yaml**):
```
rgbdtum: 
  - 'rgbd_dataset_freiburg1_xyz'
eth: 
  - 'table_3'
  - 'planar_2'
kitti:
  - '04'
  - '09'
euroc:
  - 'MH_01_easy'
monotum:
  - 'sequence_01'
```
For a full list of available VSLAM systems and datasets, refer to the section [VSLAM-LAB Supported Baselines and Datasets](#vslam-lab-supported-baselines-and-datasets).

## Add a new dataset

Datasets in **VSLAM-LAB** are stored in a folder named **VSLAM-LAB-Benchmark**, which is created by default in the same parent directory as **VSLAM-LAB**. If you want to modify the location of your datasets, change the variable **VSLAMLAB_BENCHMARK** in **~/VSLAM-LAB/utilities.py**.

1. To add a new dataset, structure your dataset as follows:
```
~/VSLAM-LAB-Benchmark
└── YOUR_DATASET
    └── sequence_01
        ├── rgb
            └── img_01
            └── img_02
            └── ...
        ├── calibration.yaml
        ├── rgb.txt
        └── groundtruth
    └── sequence_02
        ├── ...
    └── ...   
```

2. Derive a new class **dataset_{your_dataset}.py** for your dataset from  **~/VSLAM-LAB/Datasets/Dataset_vslamlab.py**, and create a corresponding YAML configuration file named **dataset_{your_dataset}.yaml**.
	
3. Include the call for your dataset in function *def get_dataset(...)* in **~/VSLAM-LAB/Datasets/Dataset_utilities.py**
```
 from Datasets.dataset_{your_dataset} import {YOUR_DATASET}_dataset
    ...
 def get_dataset(dataset_name, benchmark_path)
    ...
    switcher = {
        "rgbdtum": lambda: RGBDTUM_dataset(benchmark_path),
        ...
        "dataset_{your_dataset}": lambda: {YOUR_DATASET}_dataset(benchmark_path),
    }
```

## Add a new Baseline

## License
**VSLAM-LAB** is released under a **LICENSE.txt**. For a list of code dependencies which are not property of the authors of **VSLAM-LAB**, please check **docs/Dependencies.md**.


## Citation
If you're using **VSLAM-LAB** in your research, please cite. If you're specifically using VSLAM systems or datasets that have been included, please cite those as well. We provide a [spreadsheet](https://docs.google.com/spreadsheets/d/1V8_TLqlccipJ6x_TXkgLsw9zWszHU9M-0mGgDT92TEs/edit?usp=drive_link) with citation for each dataset and VSLAM system for your convenience. 

## Acknowledgements

To [awesome-slam-datasets](https://github.com/youngguncho/awesome-slam-datasets)

# VSLAM-LAB Supported Baselines and Datasets
We provide a [spreadsheet](https://docs.google.com/spreadsheets/d/1V8_TLqlccipJ6x_TXkgLsw9zWszHU9M-0mGgDT92TEs/edit?usp=drive_link) with more detailed information for each baseline and dataset.

| Baselines                                                                   | System |     Sensors      |                                   License                                   |    Label     |
|:----------------------------------------------------------------------------|:------:|:----------------:|:---------------------------------------------------------------------------:|:------------:|
| [**AnyFeature-VSLAM**](https://github.com/alejandrofontan/AnyFeature-VSLAM) | VSLAM  |       mono       | [GPLv3](https://github.com/alejandrofontan/VSLAM-LAB/blob/main/LICENSE.txt) | `anyfeature` |
| [**DSO**](https://github.com/alejandrofontan/dso)                           |   VO   |       mono       |       [GPLv3](https://github.com/JakobEngel/dso/blob/master/LICENSE)        |    `dso`     |
| [**ORB-SLAM2**](https://github.com/alejandrofontan/ORB_SLAM2)               | VSLAM  | mono/RGBD/Stereo |    [GPLv3](https://github.com/raulmur/ORB_SLAM2/blob/master/LICENSE.txt)    |  `orbslam2`  | 
| [**COLMAP**](https://colmap.github.io/)                                     |  SfM   |       mono       |                [BSD](https://colmap.github.io/license.html)                 |   `colmap`   | 
| [**GLOMAP**](https://lpanaf.github.io/eccv24_glomap/)                       |  SfM   |       mono       |         [BSD-3](https://github.com/colmap/glomap/blob/main/LICENSE)         |   `glomap`   |
| [**DUST3R**](https://dust3r.europe.naverlabs.com)                           |  SfM   |       mono       |    [CC BY-NC-SA 4.0](https://github.com/naver/dust3r/blob/main/LICENSE)     |   `dust3r`   | 
| [**MonoGS**](https://github.com/muskie82/MonoGS)                            | VSLAM  |       mono/RGBD/Stereo       |        [License](https://github.com/muskie82/MonoGS?tab=License-1-ov-file)         |   `monogs`   | 


| Datasets                                                                                                                        |   Data    |    Mode    |    Label    |
|:--------------------------------------------------------------------------------------------------------------------------------|:---------:|:----------:|:-----------:|
| [**ETH3D SLAM Benchmarks**](https://www.eth3d.net/slam_datasets)                                                                |   real    |  handheld  |    `eth`    |
| [**RGB-D SLAM Dataset and Benchmark**](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)                                       |   real    |  handheld  |  `rgbdtum`  |
| [**ICL-NUIM RGB-D Benchmark Dataset**](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html)                                    | synthetic |  handheld  |   `nuim`    | 
| [**Monocular Visual Odometry Dataset**](https://cvg.cit.tum.de/data/datasets/mono-dataset)                                      |   real    |  handheld  |  `monotum`  |
| [**The KITTI Vision Benchmark Suite**](https://www.cvlibs.net/datasets/kitti/eval_odometry.php)                                 |   real    |  vehicle   |   `kitti`   |
| [**RGB-D Dataset 7-Scenes**](https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/)                          |   real    |  handheld  |  `7scenes`  |
| [**The EuRoC MAV Dataset**](https://projects.asl.ethz.ch/datasets/doku.php?id=kmavvisualinertialdatasets)                       |   real    |    UAV     |   `euroc`   |
| [**TartanAir: A Dataset to Push the Limits of Visual SLAM**](https://theairlab.org/tartanair-dataset/)                          | synthetic |  handheld  | `tartanair` |
| [**The Drunkard's Dataset**](https://davidrecasens.github.io/TheDrunkard%27sOdometry)                                           | synthetic |  handheld  | `drunkards` |
| [**The Replica Dataset**](https://github.com/facebookresearch/Replica-Dataset) - [**iMAP**](https://edgarsucar.github.io/iMAP/) | synthetic |  handheld  |  `replica`  |
| [**Hamlyn Rectified Dataset**](https://davidrecasens.github.io/EndoDepthAndMotion/)                                             |   real    |  handheld  |  `hamlyn`   |
| [**Underwater caves sonar and vision data set**](https://cirs.udg.edu/caves-dataset/)                                             |   real    | underwater |   `caves`   |
