import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='canviz',
    version='0.1',
    scripts=['canviz'],
    author="Rahul Bhadani",
    author_email="rahulbhadani@email.arizona.edu",
    description="A real time CAN data logging and visualization tool to work with USB-CAN Interface."
    url="https://github.com/jmscslgroup/canviz",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Pythion:: 3",
        "Framework :: AsyncIO",
        "Topic :: Communications",
        "Topic :: Scientific/Engineering :: Visualization",
        "License:: OSI Approved:: MIT License",
        ],
        )
