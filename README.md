# Strym


__A python package for real-time CAN data logging and visualization tool to work with USB-CAN Interface.__

__Strym__ is a python package that provides APIs to interface with COMMA.AI panda to log data and visualize them in real-time. 

## Software Requirements
- Ubuntu 18.04 (not tested on any other version of Ubuntu, but might work)
- Python 3.x

### Note about installation on RASPBERRY PI
If you are going to install the package on RASPBERRY PI, I highly recommend install Python 3.7 from source as there is no Py3.7 release for Raspberry PI.
You will also need to install pre-compiled binaries for numpy otherwise you may encounter huge incovnience while building numpy wheels for Raspberry PI.


## Hardware Requirements
- comma.ai CAN-USB __Panda__ board.
- comma.ai Giraffee Connector
- A modern vehicle with CAN Bus available such as Toyota RAV4, Toyota CHR, etc. 

## Installation Instructions

1. Install Python 3, either through anaconda or using the Ubuntu package manager. For the sake of following instructions, 
let's assume that you have installed anaconda in `~/anaconda3`. I recommend using python's virtual environment for python package installation. Let's assume that you have a python virtual environment called `slocd`. Activate the virtual environment. To do, type following in your terminal:

```bash
source ~/anaconda3/bin/activate
```

```bash
conda activate slocd
```

2. Install slocdirt

`pip install git+https://github.com/jmscslgroup/slocdirt.git`

This will install the slocdirt package in your `slocd` virtual environment.

Now you are ready to use __Strym__.

## Usage

Plug your Comma AI Panda device using Giraffee Connector to your CAR's OBD port for data logging and streaming. Insert one end of the USB to Panda Device and other end to your laptop.

In python, you will be required to create an object of type `Strym`:


See `slocdirt_impl.py` for one such usage example in the [example folder](https://github.com/jmscslgroup/slocdirt/blob/master/examples), however, I am provided details of an example below:


Create a new file. I will use the gedit to create a new file. You will be required to pass a path of the CAN Database DBC file to `slocdirt` while instantiating its object. Once you have a `slocdirt` object, you can call its `isoviz()` function. `isoviz()` function takes two arguments: i) the message type that you want to visualize, e.g. SPEED ii) attribute number to plot specific signal of the desired message type. `isoviz()` function will simultaneously capture CAN messages in a CSV file and also plot the desired message's signal. To terminate, press CTRL-C. Upon pressing CTRL-C, a SIGINT signal handler will be called that will terminate the logging of CAN messages and also save a matplotlib figure of the desired message's signal in pdf and pickle format.

`gedit viz_example.py`

```python
from slocdirt import slocdirt
import cantools
import sys, math, time
import signal

db = './newToyotacode.dbc'

Viz = slocdirt(dbcfile = db)

message_type_to_visualize = 'TRACK_A'
message_attribute_number_to_visualize = 1

Viz.isoviz(message_type_to_visualize, message_attribute_number_to_visualize)

signal.signal(signal.SIGINT, Viz.kill)

print('Datafile saved is {}'.format(Viz.logfile))

```

You will need a DBC file to parse can messages. Download an example DBC file [here](https://github.com/jmscslgroup/slocdirt/blob/master/examples/newToyotacode.dbc)

To run the above program:

`source ~/anaconda3/bin/activate`

`conda activate slocd`

`python viz_example.py`

If you are done, press CTRL-C.

## Issues
If you run into any issues, please use the issue feature of GitHub to log your issues. I will try my best to address any issue as soon as
possible.

## Contributing to this project
If you like to contribute to this project, please fork this repository to your GitHub account, create a new branch for yourself and
send a pull request for the merge. After reviewing the changes, we will decide if this is a good place to add your changes.
If you like to see new data types being supported, please raise an enhancement issue and provide a relevant bag file that contains the 
ros message of desired data types.

## Authors and Contributors
- Rahul Bhadani ( rahulbhadani@email.arizona.edu)
- Jonathan Sprinkle (sprinkjm@email.arizona.edu)

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


