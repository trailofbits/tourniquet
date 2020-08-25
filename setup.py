from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import os
import subprocess
import sys
import sysconfig

module_name = "extractor"


def get_ext_filename_without_platform_suffix(filename):
    name, ext = os.path.splitext(filename)
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")

    if ext_suffix == ext:
        return filename

    ext_suffix = ext_suffix.replace(ext, "")
    idx = name.find(ext_suffix)

    if idx == -1:
        return filename
    else:
        return name[:idx] + ext


class CMakeExtension(Extension):
    """
    This class defines a setup.py extension that stores the directory
    of the root CMake file

    """

    def __init__(self, name, cmake_lists_dir=None, **kwargs):
        Extension.__init__(self, name, sources=[], **kwargs)
        if cmake_lists_dir is None:
            self.sourcedir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.sourcedir = os.path.dirname(os.path.abspath(cmake_lists_dir))


class CMakeBuild(build_ext):
    """
    This class defines a build extension
    get_ext_filename determines the expected output name of the library
    build_extension sets the appropriate cmake flags and invokes cmake to build the extension

    """

    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        return get_ext_filename_without_platform_suffix(filename)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
        ]
        print(sys.executable)
        cmake_args += [f"-DPYTHON_MODULE_NAME={module_name}"]
        env = os.environ.copy()
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env
        )
        subprocess.check_call(["cmake", "--build", "."], cwd=self.build_temp)


setup(
    name="tourniquet",
    author="Carson Harmon",
    author_email="carson.harmon@trailofbits.com",
    packages=find_packages(),
    version="1.0",
    description="Syntax Guided Repair/Transformation Package",
    ext_modules=[CMakeExtension(module_name)],
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
    install_requires=["pytest"],
)
