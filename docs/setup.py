from setuptools import setup

setup(name='strym',
    version='0.1',
    author="Rahul Bhadani",
    author_email="rahulbhadani@email.arizona.edu",
    description="A real time CAN data logging and visualization tool to work with USB-CAN Interface.",
    long_description=readme(),
    url="https://github.com/jmscslgroup/strym",
    packages=setuptools.find_packages(),

      install_requires=[
          'sphinx_autodoc_typehints',
          # 'Sphinx',
          # ^^^ Not sure if this is needed on readthedocs.org
          # 'something else?',
          ],
      )
