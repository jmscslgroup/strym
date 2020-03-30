<img src="https://raw.githubusercontent.com/jmscslgroup/strym/master/strym.png" alt="Strym Logo" align="center"/>


# Strym
[![Build Status](https://travis-ci.com/jmscslgroup/strym.svg?branch=master)](https://travis-ci.com/jmscslgroup/strym)

__A python package for real-time CAN data logging and visualization tool to work with USB-CAN Interface.__

__Strym__ is a python package that provides APIs to interface with COMMA.AI panda to log data and visualize them in real-time. There are two kinds of functionality that __Strym__ provides: 

1. Real-time visualization of CAN data through comma.ai Panda and Giraffe connector.
2. Offline analysis and visualization of CAN Data from a CSV Formatted file.

## Quick Start for CAN Data Analysis and Visualization

You can use __Strym__ quick visualization by importing `strymread`:
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

# visualiza message counts
r.count()
```

<img src="https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/count.png" alt="Count Histogram" align="center"/>


```python
# plot speed data
speed = r.speed()
strym.plt_ts(speed, title="Speed Plot")

```

<img src="https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/speed.png" alt="Count Histogram" align="center"/>

```python

# get rate statistics of every by message ID
u = r.frequency
```

```
# synchronize two timeseries messages
ts_yaw_rate = r.yaw_rate()
ts_speed = r.speed()
## integrate yaw rate to get the heading
ts_yaw = strym.integrate(ts_yaw_rate
interpolated_speed, interpolated_yaw = strym.ts_sync(ts_speed, ts_yaw)
plt.plot(interpolated_speed['Time'], interpolated_speed['Message'], ".", alpha=0.3)
plt.plot(ts_speed['Time'], ts_speed['Message'], ".", alpha=0.4)
plt.legend(['Interpolated Speed (Km/h)', 'Original Speed (Km/h)'])
plt.xlabel('Time (seconds)')
plt.ylabel('Message')
plt.plot(interpolated_yaw['Time'], interpolated_yaw['Message'], ".", alpha=0.3)
plt.plot(ts_yaw['Time'], ts_yaw['Message'], ".", alpha=0.4)
plt.legend(['Interpolated Yaw (degree/s)', 'Original Yaw (degree/s)'])
plt.xlabel('Time (seconds)')
plt.ylabel('Message')
```
<img src="https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/speed_interpolated.png" alt="Count Histogram" align="center"/>
<img src="https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/yaw_interpolated.png" alt="Count Histogram" align="center"/>
```python
# Plot the trajectory based on kinematic model, yaw rate and speed
T = r.trajectory()
plt.plot(T['X'], T['Y'])
plt.legend(['Interpolated Yaw (degree/s)', 'Original Yaw (degree/s)'])
plt.xlabel('X [m]')
plt.ylabel('Y [m]')

```
<img src="https://raw.githubusercontent.com/jmscslgroup/strym/master/docs/source/trajectory.png" alt="Count Histogram" align="center"/>



## Detailed Examples of Offline Analysis and Visualization
1. [Strymread Example 1](https://github.com/jmscslgroup/strym/blob/master/notebook/strymread_example.ipynb)
2. [Strymread Example 2](https://github.com/jmscslgroup/strym/blob/master/notebook/CAN%20Data%20Analysis%20using%20strymread.ipynb)

## Software Requirements
- Ubuntu 18.04 (not tested on any other version of Ubuntu, but might work)
- Python 3.x

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

Install Python 3, either through anaconda or using the Ubuntu package manager. Alternatively, you can also build Python 3.7 from source as explained below:

```
sudo apt-get update -y
sudo apt-get install build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev -y

wget https://www.python.org/ftp/python/3.7.2/Python-3.7.2.tar.xz
tar xf Python-3.7.2.tar.xz
cd Python-3.7.2
./configure
make -j 4
sudo make altinstall
```

I recommend using python's virtual environment for python package installation. For the sake of following instructions, let's assume that you are using the `virtualenv`  package to create a python virtual environment. 

```
sudo apt install virtualenv

```
First, create a directory where your virtual environment folder will reside.

```
mkdir ~/VirtualEnv
```
Now, we will create a python virtual environment using python3.7. Let's name the virtual environment *stream*.

```
cd VirtualEnv
virtualenv --python=python3.7 stream
```

Activate the virtual environment by typing:

```
source ~/VirtualEnv/stream/bin/activate
```

### Install strym

Install strym

`pip install git+https://github.com/jmscslgroup/strym.git`

This will install the strym package in your `stream` virtual environment.

Now you are ready to use __Strym__.

## Usage for Real-Time Visualization of CAN messages using Strym

Plug your Comma AI Panda device using Giraffe Connector to your CAR's OBD port for data logging and streaming. Insert one end of the USB to Panda Device and another end to your laptop.

In python, you will be required to create an object of type `Strym`:


See `strym_impl.py` for one such usage example in the [example folder](https://github.com/jmscslgroup/strym/blob/master/examples), however, I am provided details of an example below:


Create a new file. I will use the gedit to create a new file. You will be required to pass a path of the CAN Database DBC file to `strym` while instantiating its object. Once you have a `strym` object, you can call its `isoviz()` function. `isoviz()` function takes two arguments: i) the message type that you want to visualize, e.g. SPEED ii) attribute number to plot specific signal of the desired message type. `isoviz()` function will simultaneously capture CAN message in a CSV file and also plot the desired message's signal. To terminate, press CTRL-C. Upon pressing CTRL-C, a SIGINT signal handler will be called that will terminate the logging of CAN messages and also save a matplotlib figure of the desired message's signal in pdf and pickle format.

```
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

```
source ~/VirtualEnv/stream/bin/activate
```
```
python viz_example.py`
```

If you are done, press CTRL-C.

## Issues
If you run into any issues, please use the issue feature of GitHub to log your issues. I will try my best to address any issue as soon as
possible.

## Contributing to this project
If you like to contribute to this project, please fork this repository to your GitHub account, create a new branch for yourself and send a pull request for the merge. After reviewing the changes, we will decide if this is a good place to add your changes.

## Authors and Contributors
- Rahul Bhadani ( rahulbhadani@email.arizona.edu)
- Jonathan Sprinkle (sprinkjm@email.arizona.edu)
- Gustavo Lee (gustavolee@email.arizona.edu)
- Matthew Nice (matthew.nice@vanderbilt.edu)

With the help from George Gunter of Vanderbilt University.

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


