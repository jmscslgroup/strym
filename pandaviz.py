#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Nov 11, 2019
# About: pandaviz class uses comma.ai panda package to capture can data from comma.ai panda device
#   and plot in the real time. Read associated README for full description
# License: MIT License

    
#   Permission is hereby granted, free of charge, to any person obtaining 
#   a copy of this software and associated documentation files 
#   (the "Software"), to deal in the Software without restriction, including
#   without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to 
#   permit persons to whom the Software is furnished to do so, subject 
#   to the following conditions:

#   The above copyright notice and this permission notice shall be 
#   included in all copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF 
#   ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
#   TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
#   PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT 
#   SHALL THE AUTHORS, COPYRIGHT HOLDERS OR ARIZONA BOARD OF REGENTS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN 
#   AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE 
#   OR OTHER DEALINGS IN THE SOFTWARE.
    


__author__ = 'Rahul Bhadani'
__email__  = 'rahulbhadani@email.arizona.edu'


# For System and OS level task
import sys, getopt

## General Data processing and visualization Import

import binascii
import bitstring
import time
import datetime
import serial
import csv
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import pandas as pd # Note that this is not commai Panda, but Database Pandas
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import uuid
import scipy.special as sp
import pickle

# Comma AI imports
import cantools
from panda import Panda

'''
A class to record data from Panda and visualize in real time

'''
class pandaviz:
    '''
    __init__ connect to comma.ai panda
    argument: dbcfile: Provide path of can database file in order to decode the message

    '''
    def __init__(self, dbcfile):
        try:
            # Connect to Panda
            self.panda = Panda()

            self.dbcfile = dbcfile
            # load can database
            self.db = cantools.database.load_file(dbcfile)

            # Set up the figure
            self.fig = plt.figure()
            self.axis = self.fig.add_subplot(1,1,1)

            # logfile name attribute, initially None, it will be given value when we are ready to log the message
            self.logfile = None

            # Variable to Hold Data
            self.data = []

            # Variable to Hold Time
            self.time = []

            # Boolean flag to keep recording data
            self.keep_recording = True

            # Message Type and attributes will be saved into these variables
            self.msgType = None
            self.attribute_num = None

        except AssertionError as error:
            print('Connection to panda failed')

    # visualize() function will log everything but only visualize specific data,
    # upon pressing ctrl-C, the logging will terminate and SIGINT signal handler
    # will create a plot and save in two formats: python's pickle format and pdf
    def visualize(self, msgType, attribute_num):

        self.msgType = msgType
        self.attribute_num = attribute_num

        dt_object = datetime.datetime.fromtimestamp(time.time())
        dt = dt_object.strftime('%Y-%m-%d-%H-%M-%S-%f')
        logfile = dt + '_'   + '_CAN_Message_'+'.csv'
        self.logfile = logfile
        rf_PANDA = open(logfile, 'a')
        print('Writing data to file: '+logfile)
        print('Press Ctrl - C to terminate')
        csvwriter_PANDA = csv.writer(rf_PANDA)
        csvwriter_PANDA.writerow(['Time','Bus', 'MessageID', 'Message', 'MessageLength'])

        while self.keep_recording:
            num_messages = 16
            can_recv = self.panda.can_recv(num_messages) # collects packages, 256 at a time
            #print(can_recv)

            currTime = time.time() # Records time of collection
            for messageID, _, newMessage, bus  in can_recv:
                csvwriter_PANDA.writerow(([str(currTime), str(bus), str((messageID)), str(binascii.hexlify(newMessage).decode('utf-8')), len(newMessage)]))

                try:
                    thisMessage = self.db.get_message_by_frame_id(messageID)
                    thisMessageName = thisMessage.name

                    # if the message currently received is in the list of messageTypes to be plotted, parse it and plot it
                    if thisMessageName == msgType:
                        print('newmessage {}'.format(newMessage))
                        print('type {}'.format(type(newMessage)))
                        
                        decodedMsg = self.db.decode_message(thisMessageName, bytes(newMessage))
                        attributeNames = list(decodedMsg.keys())

                        data =decodedMsg[attributeNames[attribute_num]]
                        self.data.append(data)
                        self.time.append(currTime)

                        # Only plot 500 points at a time

                        data500 = self.data[-500:]
                        time500 = self.time[-500:]

                        self.axis.clear()
                        self.axis.plot(time500, data500, linestyle='--', color='firebrick', linewidth=2, marker='.', markersize = 3)
                        self.axis.set_axisbelow(True)
                        self.axis.minorticks_on()
                        self.axis.grid(which='major', linestyle='-', linewidth='0.5', color='salmon')
                        self.axis.grid(which='minor', linestyle=':', linewidth='0.25', color='dimgray')
                        plt.title(msgType + ": " + attributeNames[attribute_num])
                        plt.xlabel('Time')
                        plt.ylabel(attributeNames[attribute_num])

                        self.axis.plot()
                        plt.draw()
                        plt.pause(0.000001)
                except KeyError as e:
                    print('I got a KeyError - reason "{}"' .format(e))
                    continue

    # SIGINT signal handler that will terminate lself.axogging of can data and save a final plot of the desired attribute of a message type

    def kill(self, sig):
        print('CTRL-C (SIGINT) received. Stopping log.')
        self.keep_recording = False
        plt.close()

        if self.msgType is None:
            self.msgType = 'Message Type'

        if self.attribute_num is None:
            self.attribute_num = 'Attribute'

        # Ctrl-C Also saves the current figure being visualized with all data plotted on it.
        self.axis.clear()
        plt.rcParams["figure.figsize"] = (16,8)
        self.axis.plot(self.time, self.data, linestyle='--', color='firebrick', linewidth=2, marker='.', markersize = 3)
        self.axis.set_axisbelow(True)
        self.axis.minorticks_on()
        self.axis.grid(which='major', linestyle='-', linewidth='0.5', color='salmon')
        self.axis.grid(which='minor', linestyle=':', linewidth='0.25', color='dimgray')
        plt.title(msgType + ": " + attributeName)
        plt.xlabel('Time')
        plt.ylabel(attributeName)

        fileNameToSave = self.logfile[0:-4]

        pickle.dump(self.fig,file(fileNameToSave + ".pickle",'w'))
        current_fig.savefig(fileNameToSave + ".pdf", dpi = 300)

        # Close the connection to Panda
        self.panda.close()