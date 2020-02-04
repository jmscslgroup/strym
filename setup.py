import setuptools

def readme():
    with open("README.md", "r") as fh:
        long_description = fh.read()
        return long_description

setuptools.setup(
    name='canviz',
    version='0.1',
    author="Rahul Bhadani",
    author_email="rahulbhadani@email.arizona.edu",
    description="A real time CAN data logging and visualization tool to work with USB-CAN Interface.",
    long_description=readme(),
    url="https://github.com/jmscslgroup/canviz",
    packages=setuptools.find_packages(),
    install_requires=[
        'numpy',
        'matplotlib',
        'cantools',
        'libusb1',
        'pyserial',
        'bitstring'
        ],
    classifiers=[
        "Programming Language :: Pythion:: 3",
        "Framework :: AsyncIO",
        "Topic :: Communications",
        "Topic :: Scientific/Engineering :: Visualization",
        "License:: OSI Approved:: MIT License",
        ],
    keywords='candata, can, autonomous vehicle, ACC, adaptive cruise control, USB, Panda',
    include_package_data=True,
    zip_safe=False
        )
