import os
import subprocess
from typing import List, Tuple


class Target:
    """
    This class represents the candidate program to repair
    The path to the program, the tests (as a list of tuples for now)
    and the build/test commands are required

    We might be able to automatically get some info from blight
    """

    def __init__(self, filepath: str, tests: List[Tuple[str, int]], build_cmd: List[str], executable_path: str):
        self.file_path = filepath
        if not os.path.exists(self.file_path):
            raise FileNotFoundError
        self.tests = tests
        self.build_cmd = build_cmd
        self.bin_path = executable_path

    def build(self) -> bool:
        ret_code = subprocess.call(self.build_cmd)
        return ret_code == 0

    # This runs the bin specified by bin path with the tests as arguments
    def run_tests(self) -> bool:
        return False
