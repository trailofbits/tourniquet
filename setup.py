from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import os
import subprocess
import sys
import sysconfig

module_name = "example"

def get_ext_filename_without_platform_suffix(filename):
    name, ext = os.path.splitext(filename)
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')

    if ext_suffix == ext:
        return filename

    ext_suffix = ext_suffix.replace(ext, '')
    idx = name.find(ext_suffix)

    if idx == -1:
        return filename
    else:
        return name[:idx] + ext


"""
Cmake has all the magic for building the actual clang tool
Locating appropriate LLVM headers/linking libraries etc 
These classes create a build_ext that uses cmake to build the tool
"""

class CMakeExtension(Extension):
    def __init__(self, name, cmake_lists_dir='.', **kwargs):
        Extension.__init__(self, name, sources=[], **kwargs)
        self.sourcedir = os.path.abspath(cmake_lists_dir)


class CMakeBuild(build_ext):
    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        name = get_ext_filename_without_platform_suffix(filename)
        print("NAME IS: ", name)
        return name

    def build_extension(self, ext):
        extdir = os.path.abspath(
            os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable]
        print("EXECUTABLE ", sys.executable)
        print(extdir)

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]
        #ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        # Strip the last two trailing characters
        # Find the .so suffix
        #ext_suffix = ext_suffix[:len(ext_suffix)-3]
        #print("MOD NAME: ", module_name + ext_suffix)
        #cmake_args += ["-DPYTHON_MODULE_NAME=" + module_name + ext_suffix]
        cmake_args += ["-DPYTHON_MODULE_NAME=" + module_name]
        cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
        build_args += ['--', '-j2']
        print("EXT NAME ", ext.name)
        print(ext.library_dirs)

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(
            env.get('CXXFLAGS', ''),
            self.distribution.get_version())
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args,
                              cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args,
                              cwd=self.build_temp)
        print()  # Add an empty line for cleaner output
        """
        try:
            subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("Error: Cannot find cmake, is it on $PATH?")

        for ext in self.extensions:
            extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
            build_type = '-DCMAKE_BUILD_TYPE=Release'
            lib_output = '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir
            args = [build_type, lib_output]

            if not os.path.exists(self.build_temp):
                os.makedirs(self.build_temp)

            # Config and build the extension
            subprocess.check_call(['cmake', ext.cmake_lists_dir] + args, cwd=self.build_temp)
            subprocess.check_call(['cmake', '--build', '.', '--config', build_type], cwd=self.build_temp)
    """



setup(name='testme',
      author="Carson Harmon",
      author_email="carson.harmon@trailofbits.com",
      packages=find_packages(),
      version='1.0',
      description='This is a demo package',
      ext_modules=[CMakeExtension(module_name)],
      cmdclass={'build_ext': CMakeBuild},
      zip_safe=False)
