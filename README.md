# SLOCDIRT
*(S)treaming and (L)ogging (O)f (C)an (D)ata (I)n (R)eal (T)ime*

__A real time CAN data logging and visualization tool to work with USB-CAN Interface.__



## Requirements
- Ubuntu 18.04 (not tested on any other version of Ubuntu, but might work)
- Python 3.x
- comma.ai CAN-USB __Panda__ board.

1. Install Python 3, either through anaconda or using Ubuntu package manager. For the sake of following instructions, 
lets assume that you have installed anaconda in `~/anaconda3`

2. Next, clone this repository

`git clone https://github.com/jmscslgroup/pandaviz pandaviz`

`cd pandaviz`

3. Now we will install some required packages. It is possible that either your requirements have already been met or you need 
to install some additional packages using `pip install`.

`pip install -r requirements.tx`

4. We will install comma.ai's panda. I am using a specific forked version comma.ai panda which I have modified to 
suit my needs

`cd ~`

`git clone https://github.com/jmscslgroup/panda panda`

`cd panda`

`git checkout jmscsl`

`source ~/anaconda3/bin/activate`

`conda activate base`

`python setup.py install`

Now you are ready to use __pandaviz__.

## Usage

See pandaviz_impl.py for one such usage example.

Create an object of type *pandaviz*:

`cd ~/pandaviz`

Create a new file. I will use gedit to create a new file. You will be required to pass a path of the CAN Database dbc file
to *pandaviz* while instnatiating its object. Once you have a *pandaviz* object, you can call its *visualize()* function. *visualize()* function takes two argument: i) the message type that you want to visualize, e.g. SPEED ii) attribute number to plot specific signal of the desired message type. *visualize()* function will simultaneously capture the CAN messages in a csv file and also plot desired message's signal. To terminate, press CTRL-C. Upon pressing CTRL-C, a SIGINT signal handler will be called that will terminate the logging of the CAN messages and also save a matplotlib figure of the desired message's signal in pdf and pickle format.

`gedit viz_example.py`

```python
from pandaviz import pandaviz
import cantools
import sys, math, time
import signal

dbcFile = cantools.database.load_file('newToyotacode.dbc')

v = pandaviz(dbcfile = db)


message_type_to_visualize = 'SPEED'
message_attribute_number_to_visualize = 1

V.visualize(message_type_to_visualize, message_attribute_number_to_visualize)

signal.signal(signal.SIGINT, V.kill)

print('Datafile saved is {}'.format(V.logfile))

```

To run the above program:

`source ~/anaconda3/bin/activate`

`conda activate base`

`python viz_example.py`

Whenever, you are done, press CTRL-C.

## Issues
If you run into any issues, please use the issue feature of the GitHub to log your issues. I will try my best to address any issue as soon as
possible.

## Contributing to this project
If you like to contribute to this project, please fork this repository to your GitHub account, create a new branch for yourself and
send a pull request for the merge. After reviewing the changes, we will decide if this is a good place to add your changes.
If you like to see new data types being supported, please raise an enhancement issue and provide a relevant bag file that contains the 
ros message of desired data types.

## Authors and Contributors
- Rahul Bhadani ( rahulbhadani@email.arizona.edu) with the help from George Gunter of Vanderbilt University

## Licensing

    License: MIT License 
    Copyright 2019-2020 Rahul Bhadani
    Initial Date: Sept 12, 2019
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


