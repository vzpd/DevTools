import os
import sys

from settings import APP_PATH


def get_static_file(*path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = APP_PATH
    return os.path.join(base_path, *path)
