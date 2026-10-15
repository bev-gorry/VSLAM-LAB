"""
Module: VSLAM-LAB - Datasets - extra-files - arstream_tools.py
- Author: Alejandro Fontan Villacampa
- Assisted by: Claude (Fable 5.1)
- Version: 1.0
- Created: 2026-10-12
- Updated: 2026-10-12
- License: GPLv3 License

Shared by record_iphone.py and stream_iphone.py: the arstream repository (github.com/VSLAM-LAB/arstream,
cloned to Datasets/sources/arstream and installed on first use through CapabilityVSLAMLAB), the phone
connection arguments both scripts forward to its tasks, and the USB foreground launch of the app.
"""

import argparse
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from Capabilities.CapabilityVSLAMLAB import CapabilityVSLAMLAB  # noqa: E402
from utilities import make_printers  # noqa: E402

SCRIPT_LABEL = f"\033[95m[{Path(__file__).name}]\033[0m "
print_info, print_warning = make_printers(SCRIPT_LABEL)

ARSTREAM_PATH = REPO_ROOT / "Datasets" / "sources" / "arstream"


def arstream_task(task: str) -> CapabilityVSLAMLAB:
    """A runner for one task of the arstream repository's pixi.toml (`record`, `publish`, `ios-launch`, ...);
    CapabilityVSLAMLAB runs a single task, so each task gets its own runner."""
    return CapabilityVSLAMLAB("arstream", "VSLAM-LAB/arstream", path=ARSTREAM_PATH, inference_task=task)


def add_phone_args(parser: argparse.ArgumentParser) -> None:
    """The phone connection flags of the arstream commands, plus --no-launch."""
    parser.add_argument("--wifi", action="store_true", help="find the phone on Wi-Fi via Bonjour (default: USB)")
    parser.add_argument("--host", help="phone IP for Wi-Fi (shown in the app)")
    parser.add_argument("--port", type=int, help="port the app listens on (default: arstream's 5555)")
    parser.add_argument("--serial", help="device serial/UDID if several phones are plugged in")
    parser.add_argument("--no-launch", action="store_true",
                        help="do not bring the app to the foreground on the phone before connecting over USB (macOS)")


def phone_args(args: argparse.Namespace) -> list[str]:
    """The connection flags to forward to an arstream command."""
    forwarded = []
    if args.wifi:
        forwarded.append("--wifi")
    if args.host:
        forwarded += ["--host", args.host]
    if args.port is not None:
        forwarded += ["--port", str(args.port)]
    if args.serial:
        forwarded += ["--serial", args.serial]
    return forwarded


def launch_app(args: argparse.Namespace) -> None:
    """Brings ARStream to the foreground on the USB phone before connecting (macOS with Xcode's devicectl
    only): iOS suspends the app's listener otherwise and the connection is refused. A failure (no phone, app
    not installed) is a warning: the connection attempt that follows reports the actual problem."""
    if args.no_launch or args.wifi or args.host:
        return
    if platform.system() != "Darwin" or shutil.which("xcrun") is None:
        return
    print_info("Bringing the ARStream app to the foreground on the phone ...")
    try:
        arstream_task("ios-launch").run_args([])
    except subprocess.CalledProcessError:
        print_warning("Could not launch the ARStream app (see above) - open it on the phone yourself")
        return
    time.sleep(1.0)  # the listener comes up right after launch; a moment's margin before connecting
