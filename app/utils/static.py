import os, sys


def get_static_file(*path):
    return os.path.join(sys._MEIPASS, *path)
