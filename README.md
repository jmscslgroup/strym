# Commaai PandaVIZ
__This python class uses a fork of comma.ai's panda package and a CAN-bus capture tool called Panda to capture CAN data from
modern vehicles through its OBD port and visualize data of choice in the real-time.__


## Requirements
- Ubuntu 18.04 (not tested on any other version of Ubuntu, but might work)
- Python 3.x
- comma.ai's panda tool.

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

## Usages

See pandaviz_impl.py for one such usage example.

Create an object of type *pandaviz*:

`cd ~/pandaviz`

Create a new file. I will use gedit to create a new file. You will be required to pass a path of the CAN Database dbc file
to *pandaviz* while instnatiating its object. Once you have a *pandaviz* object, you can call its *visualize()* function. *visualize()* function takes two argument: i) the message type that you want to visualize, e.g. SPEED ii) attribute number to plot specific signal of the desired message type. *visualize()* function will simultaneously capture the CAN messages in a csv file and also plot desired message's signal. To terminate, press CTRL-C. Upon pressing CTRL-C, a SIGINT signal handler will be called that will terminate the logging of the CAN messages and also save a matplotlib figure of the desired message's signal in pdf and pickle format.

`gedit viz_example.py`

```
from pandaviz import pandaviz
import cantools
import sys, math, time
import signal

dbcFile = cantools.database.load_file('newToyotacode.dbc')

v = pandaviz(dcfile = db)


message_type_to_visualize = 'SPEED'
message_attribute_number_to_visualize = 1

V.visualize(message_type_to_visualize, message_attribute_number_to_visualize)

signal.signal(signal.SIGINT, V.kill)

print('Datafile saved is {}'.format(V.logfile))

```

