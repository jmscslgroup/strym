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
