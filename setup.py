from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os
import subprocess

"""
Cmake has all the magic for building the actual clang tool
Locating appropriate LLVM headers/linking libraries etc 
These classes create a build_ext that uses cmake to build the tool
"""


class CMakeExtension(Extension):
    def __init__(self, name, cmake_lists_dir='.', **kwargs):
        Extension.__init__(self, name, sources=[], **kwargs)
        self.cmake_lists_dir = os.path.abspath(cmake_lists_dir)


class CMakeBuild(build_ext):
    def build_extensions(self):
        try:
            subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("Error: Cannot find cmake, is it on $PATH?")

        for ext in self.extensions:
            if not os.path.exists(self.build_temp):
                os.makedirs(self.build_temp)

            # Config and build the extension
            subprocess.check_call(['cmake', ext.cmake_lists_dir], cwd=self.build_temp)
            subprocess.check_call(['cmake', '--build', '.', '--config'], cwd=self.build_temp)


module_name = "example"
version = '0.0.1'

setup(name='PackageName',
      version='1.0',
      description='This is a demo package',
      ext_modules=[CMakeExtension(module_name)],
      cmdclass={'build_ext': CMakeBuild})
