import setuptools
from distutils.dir_util import copy_tree
from pathlib import Path
PACKAGE_NAME='strym'
import shutil, os
shutil.copy('README.md', PACKAGE_NAME + '/README.md')

#copy_tree('./examples', PACKAGE_NAME + '/examples')
#copy_tree('./dbc', PACKAGE_NAME + '/dbc')

def readme():
    with open("README.md", "r") as fh:
        long_description = fh.read()
        return long_description

v = Path(PACKAGE_NAME + "/version").open(encoding = "utf-8").read().splitlines()

setuptools.setup(
    name='strym-lite',
    version=v[0].strip(),
    author="Rahul Bhadani",
    author_email="rahulbhadani@email.arizona.edu",
    description="A real time CAN data logging and visualization tool to work with USB-CAN Interface.",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/jmscslgroup/strym",
    packages=setuptools.find_packages(),
    install_requires=[
        l.strip() for l in Path("requirements_lite.txt").open(encoding = "utf-8").read().splitlines()
        ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: AsyncIO",
        "Topic :: Communications",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        ],
    keywords='candata, can, autonomous vehicle, ACC, adaptive cruise control, USB, Panda, Traffic, Transportation, visualization',
    include_package_data=True,
    package_data={'strym': ['README.md', 'dbc/*.*','version']},
    zip_safe=False
        )

os.remove('strym/README.md')
#shutil.rmtree(PACKAGE_NAME + '/examples')
#shutil.rmtree(PACKAGE_NAME + '/dbc')
