#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Nov 11, 2019

from strym import strym
import cantools
import sys, math, time
import signal
import subprocess, shlex
from subprocess import call
import psutil
import glob
import numpy as np

db = './newToyotacode.dbc'

init_options = {"path": "./"}


Viz = strym(dbcfile = db, **init_options)

# What message type to visualize
message_type_to_visualize = 'SPEED'
# What message attribute of the above message type to visualize
message_attribute_number_to_visualize = 1

# Above messages will be visualized only when you pass visualize=True
visualize = False

# What message IDs to be logged into CSV File?, If you don't specify this, all messages will be logged.
# type_list = np.arange(384, 400)
# type_list = np.append(180, type_list)
type_list = None

options = {"log": "info", "match": "exact", "typelist":type_list}
Viz.isolog(visualize, message_type_to_visualize, message_attribute_number_to_visualize,  **options)

signal.signal(signal.SIGINT, Viz.kill)

print('Datafile saved is {}'.format(Viz.logfile))


