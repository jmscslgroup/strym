<img src="https://raw.githubusercontent.com/jmscslgroup/strym/master/strym.png" alt="Strym Logo" align="center"/>


# Strym
[![Build Status](https://travis-ci.com/jmscslgroup/strym.svg?branch=master)](https://travis-ci.com/jmscslgroup/strym)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/jmscslgroup/strym/graphs/commit-activity)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![made-with-sphinx-doc](https://img.shields.io/badge/Made%20with-Sphinx-1f425f.svg)](https://www.sphinx-doc.org/)
[![PyPI version shields.io](https://img.shields.io/pypi/v/strym.svg)](https://pypi.python.org/pypi/strym/)
[![PyPI license](https://img.shields.io/pypi/l/strym.svg)](https://pypi.python.org/pypi/strym/)
[![Downloads](https://pepy.tech/badge/strym)](https://pepy.tech/project/strym)



__A python package for real-time CAN data logging, analysis and visualization to work with USB-CAN Interface.__

__Strym__ is a python package that provides APIs to interface with COMMA.AI panda for logging CAN data, analysis and visualization in real-time from supported modern vehicles such Toyota RAV4 and Honda Pilot. There are two kinds of functionality that __Strym__ provides: 

1. Real-time visualization of CAN data through comma.ai Panda and Giraffe connector.
2. Offline analysis and visualization of CAN Data from a CSV Formatted file.


## Philosophy behind Strym

Strym data is capable of handling timeseries data obtained from Comma.ai Panda and Giraffe Connector. 
Most functions and methods in `strym` expects timeseries data of following format

|   | Time               | Message |
|---|--------------------|---------|
| 1 | 1582056042.5040324 | 2.0     |
| 2 | 1582056043.5040324 | 2.1     |
| 3 | 1582056044.5040324 | 2.12    |
| 4 | 1582056045.5040324 | 1.98    |
| 5 | 1582056046.5040324 | 1.6     |

Here, data should be of type Pandas.DataFrame with two columns: Time and Message. 

However, scope of strym is not limited to timeseries data obtained from comma.ai Panda. Any timeseries data of above format is capable of harnessing methods available in `strym`.

## Quick Start for CAN Data Analysis and Visualization

You can use __Strym__ for quick visualization by importing `strymread`:
```python
import strym
from strym import strymread
from strym import ranalyze
import matplotlib.pyplot as plt
import pandas as pd
from pylab import rcParams
import strym.DBC_Read_Tools as dbc
import numpy as np
plt.rcParams["figure.figsize"] = (16,8)
rcParams.update({'font.size': 40})
dbcfile = '/home/ivory/VersionControl/Jmscslgroup/strym/examples/newToyotacode.dbc'
r =strymread(csvfile="/home/ivory/CyverseData/JmscslgroupData/PandaData/2020_02_18/2020-02-18-13-00-42-209119__CAN_Messages.csv", dbcfile=dbcfile)
```

Checkout documentation at https://jmscslgroup.github.io/strym/getting_started.html for more in-depth tutorials.

## Software Requirements
- Ubuntu 18.04 (not tested on any other version of Ubuntu, but might work)
- Python 3.x ( I recommend using python 3.7.5 so as not to get caught in dependency hell as develop is being done using python 3.7.5, and recen pip changes are not dependency-friendly). 

### Note about installation on RASPBERRY PI for CAN Data Logging
If you are going to install the package on RASPBERRY PI, I highly recommend installing Python 3.7 from the source as there is no Py3.7 release for Raspberry PI.
You will also need to install pre-compiled binaries for NumPy otherwise you may encounter huge inconvenience while building NumPy wheels for Raspberry PI.


## Hardware Requirements for CAN Logging
- comma.ai CAN-USB __Panda__ board.
- comma.ai Giraffee Connector
- A modern vehicle with CAN Bus available such as Toyota RAV4, Toyota CHR, etc. 

## Installation Instructions

[![Install Instruction](https://img.youtube.com/vi/w2p1uYmHBPA/0.jpg)](https://www.youtube.com/watch?v=w2p1uYmHBPA&t=5s)

### Install Python

Install Python 3, either through anaconda or using the Ubuntu package manager. Alternatively, you can also build Python 3.7.5 from source as explained below:

```bash
sudo apt-get update -y
sudo apt-get install build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev -y

wget https://www.python.org/ftp/python/3.7.5/Python-3.7.5.tar.xz
tar xf Python-3.7.5.tar.xz
cd Python-3.7.5
./configure
make -j 4
sudo make altinstall
```

I recommend using python's virtual environment for python package installation. For the sake of following instructions, let's assume that you are using the `virtualenv`  package to create a python virtual environment. 

```bash
sudo apt install virtualenv
```
First, create a directory where your virtual environment folder will reside.

```bash
mkdir ~/VirtualEnv
```
Now, we will create a python virtual environment using python3.7. Let's name the virtual environment *stream*.

```bash
cd ~/VirtualEnv
virtualenv --python=python3.7.5 strym
```

Activate the virtual environment by typing:

```bash
source ~/VirtualEnv/stream/bin/activate
```

Alternatively, you can use Anaconda to create a virtual evinronment and activate it:

```bash
conda create -n strym python=3.7.5
conda activate strym
```

### Install strym

`pip install strym`

This will install the strym package in your `stream` virtual environment.

Now you are ready to use __Strym__.

## Usage for Real-Time Visualization of CAN messages using Strym

Plug your Comma AI Panda device using Giraffe Connector to your CAR's OBD port for data logging and streaming. Insert one end of the USB to Panda Device and another end to your laptop.

In python, you will be required to create an object of type `Strym`:


See `strym_impl.py` for one such usage example in the [example folder](https://github.com/jmscslgroup/strym/blob/master/examples), however, I am provided details of an example below:


Create a new file. I will use the gedit to create a new file. You will be required to pass a path of the CAN Database DBC file to `strym` while instantiating its object. Once you have a `strym` object, you can call its `isoviz()` function. `isoviz()` function takes two arguments: i) the message type that you want to visualize, e.g. SPEED ii) attribute number to plot specific signal of the desired message type. `isoviz()` function will simultaneously capture CAN message in a CSV file and also plot the desired message's signal. To terminate, press CTRL-C. Upon pressing CTRL-C, a SIGINT signal handler will be called that will terminate the logging of CAN messages and also save a matplotlib figure of the desired message's signal in pdf and pickle format.

```bash
gedit viz_example.py
```

```python
from strym import strym
import cantools
import sys, math, time
import signal

db = './newToyotacode.dbc'

Viz = strym(dbcfile = db)

message_type_to_visualize = 'SPEED'
message_attribute_number_to_visualize = 1

visualize = False
options = {"log": "info" }
Viz.isolog(visualize, message_type_to_visualize, message_attribute_number_to_visualize,  **options)

signal.signal(signal.SIGINT, Viz.kill)

print('Datafile saved is {}'.format(Viz.logfile))


```

You will need a DBC file to parse can messages. Download an example DBC file [here](https://github.com/jmscslgroup/strym/blob/master/examples/newToyotacode.dbc)

To run the above program:

```bash
source ~/VirtualEnv/stream/bin/activate
python viz_example.py`
```

If you are done, press CTRL-C.

## Issues
If you run into any issues, please use the issue feature of GitHub to log your issues. I will try my best to address any issue as soon as
possible.

For an issue related to installation/use on windows, please see following filed issues:

1. [Issue #8: OSError: [WinError 126]](https://github.com/jmscslgroup/strym/issues/8)

## Contributing to this project
If you like to contribute to this project, please fork this repository to your GitHub account, create a new branch for yourself and send a pull request for the merge. After reviewing the changes, we will decide if this is a good place to add your changes.

## Authors and Contributors
- Rahul Bhadani ( rahulbhadani@email.arizona.edu)
- Jonathan Sprinkle (sprinkjm@email.arizona.edu)
- Gustavo Lee (gustavolee@email.arizona.edu)
- Matthew Nice (matthew.nice@vanderbilt.edu)
- George Gunter (gunter.gl@gmail.com)
- Safwan Elmadani (safwanelmadani@email.arizona.edu)

## Licensing

    License: MIT License 
    Copyright 2019-2020 Rahul Bhadani, Jonathan Sprinkle, Arizona Board of Regents
    Initial Date: Nov 12, 2019
    Permission is hereby granted, free of charge, to any person obtaining 
    a copy of this software and associated documentation files 
    (the "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to 
    permit persons to whom the Software is furnished to do so, subject 
    to the following conditions:

    The above copyright notice and this permission notice shall be 
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF 
    ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
    TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT 
    SHALL THE AUTHORS, COPYRIGHT HOLDERS OR ARIZONA BOARD OF REGENTS
    BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN 
    AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE 
    OR OTHER DEALINGS IN THE SOFTWARE.


