# ADD your imports here

from Datasets.dataset_rgbdtum import RGBDTUM_dataset
from Datasets.dataset_eth import ETH_dataset
from Datasets.dataset_nuim import NUIM_dataset
from Datasets.dataset_scannetplusplus import SCANNETPLUSPLUS_dataset

from Datasets.dataset_lizardisland import LIZARDISLAND_dataset
from Datasets.dataset_ariel import ARIEL_dataset
from Datasets.dataset_7scenes import SEVENSCENES_dataset
from Datasets.dataset_euroc import EUROC_dataset
from Datasets.dataset_kitti import KITTI_dataset
from Datasets.dataset_monotum import MONOTUM_dataset
from Datasets.dataset_tartanair import TARTANAIR_dataset
from Datasets.dataset_drunkards import DRUNKARDS_dataset
from Datasets.dataset_replica import REPLICA_dataset
from Datasets.dataset_hamlyn import HAMLYN_dataset
from Datasets.dataset_caves import CAVES_dataset
from Datasets.dataset_lamar import LAMAR_dataset
from Datasets.dataset_eth3d_mvs_dslr import ETH3D_MVS_DSLR_dataset
from Datasets.dataset_yandiwanba import YANDIWANBA_dataset
from Datasets.dataset_antarctica import ANTARCTICA_dataset
from Datasets.dataset_hilti2022 import HILTI2022_dataset
from Datasets.dataset_squidle import SQUIDLE_dataset
from Datasets.dataset_openloris import OPENLORIS_dataset
from Datasets.dataset_madmax import MADMAX_dataset

SCRIPT_LABEL = "[dataset_utilities.py] "


def get_dataset(dataset_name, benchmark_path):
    dataset_name = dataset_name.lower()
    switcher = {
        # ADD your datasets here
        "rgbdtum": lambda: RGBDTUM_dataset(benchmark_path),
        "eth": lambda: ETH_dataset(benchmark_path),
        "nuim": lambda: NUIM_dataset(benchmark_path),
        "scannetplusplus": lambda: SCANNETPLUSPLUS_dataset(benchmark_path),
        
        "lizardisland": lambda: LIZARDISLAND_dataset(benchmark_path),
        "hamlyn": lambda: HAMLYN_dataset(benchmark_path),
        "replica": lambda: REPLICA_dataset(benchmark_path),
        "drunkards": lambda: DRUNKARDS_dataset(benchmark_path),
        "ariel": lambda: ARIEL_dataset(benchmark_path),
        "kitti": lambda: KITTI_dataset(benchmark_path),
        "euroc": lambda: EUROC_dataset(benchmark_path),
        "monotum": lambda: MONOTUM_dataset(benchmark_path),
        "7scenes": lambda: SEVENSCENES_dataset(benchmark_path),
        "tartanair": lambda: TARTANAIR_dataset(benchmark_path),
        "caves": lambda: CAVES_dataset(benchmark_path),
        "lamar": lambda: LAMAR_dataset(benchmark_path),
        "eth3d_mvs_dslr": lambda: ETH3D_MVS_DSLR_dataset(benchmark_path),
        "yandiwanba": lambda: YANDIWANBA_dataset(benchmark_path),
        "antarctica": lambda: ANTARCTICA_dataset(benchmark_path),
        "hilti2022": lambda: HILTI2022_dataset(benchmark_path),
        "squidle": lambda: SQUIDLE_dataset(benchmark_path),
        "openloris": lambda: OPENLORIS_dataset(benchmark_path),
        "madmax": lambda: MADMAX_dataset(benchmark_path),
    }

    return switcher.get(dataset_name, lambda: "Invalid case")()
