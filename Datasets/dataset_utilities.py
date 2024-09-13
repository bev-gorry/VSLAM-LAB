# ADD your imports here
from Datasets.dataset_ariel import ARIEL_dataset
from Datasets.dataset_7scenes import SEVENSCENES_dataset
from Datasets.dataset_eth import ETH_dataset
from Datasets.dataset_euroc import EUROC_dataset
from Datasets.dataset_kitti import KITTI_dataset
from Datasets.dataset_monotum import MONOTUM_dataset
from Datasets.dataset_nuim import NUIM_dataset
from Datasets.dataset_rgbdtum import RGBDTUM_dataset
from Datasets.dataset_tartanair import TARTANAIR_dataset
from Datasets.dataset_drunkards import DRUNKARDS_dataset
from Datasets.dataset_replica import REPLICA_dataset
from Datasets.dataset_hamlyn import HAMLYN_dataset
from Datasets.dataset_caves import CAVES_dataset
from Datasets.dataset_imagefolder import IMAGEFOLDER_dataset

SCRIPT_LABEL = "[dataset_utilities.py] "


def get_dataset(dataset_name, benchmark_path):
    dataset_name = dataset_name.lower()
    switcher = {
        # ADD your datasets here
        "hamlyn": lambda: HAMLYN_dataset(benchmark_path),
        "replica": lambda: REPLICA_dataset(benchmark_path),
        "drunkards": lambda: DRUNKARDS_dataset(benchmark_path),
        "ariel": lambda: ARIEL_dataset(benchmark_path),
        "rgbdtum": lambda: RGBDTUM_dataset(benchmark_path),
        "eth": lambda: ETH_dataset(benchmark_path),
        "kitti": lambda: KITTI_dataset(benchmark_path),
        "euroc": lambda: EUROC_dataset(benchmark_path),
        "monotum": lambda: MONOTUM_dataset(benchmark_path),
        "nuim": lambda: NUIM_dataset(benchmark_path),
        "7scenes": lambda: SEVENSCENES_dataset(benchmark_path),
        "tartanair": lambda: TARTANAIR_dataset(benchmark_path),
        "caves": lambda: CAVES_dataset(benchmark_path),
        "imagefolder": lambda: IMAGEFOLDER_dataset(benchmark_path),
    }

    return switcher.get(dataset_name, lambda: "Invalid case")()
