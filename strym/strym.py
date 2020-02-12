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

import struct
import signal
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

import libusb1
import usb1

# cantools import
import cantools

class strym:
    '''
   `pandaviz`  class to record data from Comm AI Panda and visualize in real time
     The constructor first gets an "USB context" by creating  `USBContext` instance.
    Then, it browses available USB devices and open the one whose manufacturer is
    COMMA.AI. One right device is identified,  `strym` creates a device handle,
    enables automatic kernel driver detachment and claim interface for I/O operation.

    Read and Write for USB devices are either done synchronosly or in isochronos mode.

    If your interest is merely in capturing data, you should perform synchronous mode.
    For (almost) real time visualization, isochronous mode is the way to go.

    Parameter
    -------------
    dbcfile: `string` Provide path of can database file in order to decode the message

    References
    -----------------
    1. https://github.com/gotmc/libusb
    2. https://pypi.org/project/libusb1/
    3. https://vovkos.github.io/doxyrest/samples/libusb/index.html
    4. https://github.com/vpelletier/python-libusb1
    5. https://www.beyondlogic.org/usbnutshell/usb4.shtml

    '''
    def __init__(self, dbcfile: str):
        # Get the USB Context
        self.context = usb1.USBContext()
        # Get all the USB device list
        deviceList =  self.context.getDeviceList()
        #commaai_device = None

        # Iterate over the list of devices
        for device in deviceList:
            try:
                device_manufacturer = device.getManufacturer()
                print('Device manufacturer is {}\n'.format(device_manufacturer))
                if device_manufacturer == 'comma.ai':
                    commaai_device = device
                    print("We found a COMMA AI Device with serial number {}".format(commaai_device.getSerialNumber()))
                    break
            except usb1.USBErrorAccess:
                # If the device is not accessible, do not do anything
                # print('USB Device Not accessible')
                pass

        if commaai_device is None:
            print("No comma.ai device was found. Aborting")
            sys.exit(-1)

        self.device = commaai_device
        # Save the serial number for future use
        self.serial = commaai_device.getSerialNumber()

        # open the comma.ai device and obtain a device handle. A handle allows you to
        # perform I/O on the device in question. Internally, this function adds a
        # reference to the device and makes it available to you through
        # `libusb_get_device()`. This reference is removed during libusb_close().
        # This is a non-blocking function; no requests are sent over the bus.
        self.handle = commaai_device.open()

        # set_auto_detach_kernel_driver to  enable/disable libusb's automatic kernel driver detachment.
        self.handle.setAutoDetachKernelDriver(True)

        # You must claim the interface you wish to use before you can perform I/O on any of its endpoints.
        self.handle.claimInterface(0)

        # define endpoint for reading
        self.ENDPOINT_READ = 1
        # buffer size
        self.BUFFER_SIZE = 16
        # dbc file from constructor
        self.dbcfile = dbcfile
        # load can database from dbc file
        self.db = cantools.database.load_file(dbcfile)

        # Set up the figure
        self.fig = plt.figure()
        self.axis = self.fig.add_subplot(1,1,1)

        # logfile name attribute, initially None, it will be given value when we are ready to log the message
        self.csvwriter = None
        # Variable to Hold Data
        self.data = []
        # Variable to Hold Time
        self.time = []
        # Boolean flag to keep recording data
        self.keep_recording = True

        # Message Type and attributes will be saved into these variables. This is only useful when you want to visualize the specific data
        self.msgType = None
        self.attribute_num = None
        self.attributeName = None
        self.newbuffer = None

    def process_received_data(self, transfer: usb1.USBTransfer):
        '''
        `process_received_data` function implements a callback that processes the reeceived data
        from USB in isochronous mode.  Once data is extracted from buffer, it is saved in the object's data variable.
        The data is used to update the plot in the real time.

        '''
        currTime = time.time() # Records time of collection

        if transfer.getStatus() != usb1.TRANSFER_COMPLETED:
            # Transfer did not complete successfully, there is no data to read.
            # This example does not resubmit transfers on errors. You may want
            # to resubmit in some cases (timeout, ...).
            return
        self.newbuffer = transfer.getBuffer()[:transfer.getActualLength()]

        if self.newbuffer is None:
            return

        # parse the can buffer into message ID, message, and bus number
        can_recv = self.parse_can_buffer(self.newbuffer)

        thisMessage = None
        thisMessageName = None
        for messageID, _, newMessage, bus  in can_recv:
            self.csvwriter.writerow(([str(currTime), str(bus), str((messageID)), str(binascii.hexlify(newMessage).decode('utf-8')), len(newMessage)]))
            if self.visualize:
                try:
                    thisMessage = self.db.get_message_by_frame_id(messageID)
                    thisMessageName = thisMessage.name

                    # if the message currently received is in the list of messageTypes to be plotted, parse it and plot it
                    if  self.msgType == thisMessageName :
                        decodedMsg = self.db.decode_message(thisMessageName, bytes(newMessage))
                        attributeNames = list(decodedMsg.keys())
                        self.attributeName = attributeNames[self.attribute_num]
                        data =decodedMsg[self.attributeName]
                        print('Time: {}, Data: {}'.format(currTime, data))
                        self.data.append(data)
                        self.time.append(currTime)

                        # Only plot 500 points at a time
                        # Check if data doesn't have 500 points then consume all of the data
                        if len(self.data) > 500:
                            data500 = self.data[-500:]
                            time500 = self.time[-500:]
                        else:
                            data500 = self.data
                            time500 = self.time

                        self.axis.clear()
                        self.axis.plot(time500, data500, linestyle='None', color='firebrick', linewidth=2, marker='.', markersize = 3)
                        self.axis.set_axisbelow(True)
                        self.axis.minorticks_on()
                        self.axis.grid(which='major', linestyle='-', linewidth='0.5', color='salmon')
                        self.axis.grid(which='minor', linestyle=':', linewidth='0.25', color='dimgray')
                        plt.title(self.msgType + ": " +  self.attributeName)
                        plt.xlabel('Time')
                        plt.ylabel(self.attributeName)
                        self.axis.plot()
                        plt.draw()
                        plt.pause(0.00000001)
                except KeyError as e:
                    # print("thisMessageName: {}".format(thisMessageName))
                    if  self.log == "debug":
                        print('Message ID not supported by current DBC files ["{}"]' .format(e))
                    continue

    def isolog(self, visualize: bool, msgType: str, attribute_num: int, **kwargs):
        '''
        LOG EVERYTHING, PLOT SOMETHING

        `isoviz()` function will log everything in isochronous manner but only visualize specific attribute of the given message.
        Upon pressing ctrl-C, the logging will terminate and SIGINT signal handler
        will create a plot and save in two formats: python's pickle format and pdf.

        `isoviz` is responsible handling data transfer in the isochronous mode and parsing through callback function `process_received_data`

        See https://vovkos.github.io/doxyrest/samples/libusb/group_libusb_asyncio.html?highlight=transfer#details-group-libusb-asyncio
        for more detail

        '''
        self.msgType = msgType
        self.attribute_num = attribute_num
        self.visualize = visualize

        try:
            self.log = kwargs["log"]
        except KeyError as e:
            print("KeyError: {}".format(str(e)))
            raise


        dt_object = datetime.datetime.fromtimestamp(time.time())
        dt = dt_object.strftime('%Y-%m-%d-%H-%M-%S-%f')
        logfile = dt + '_'   + '_CAN_Message'+'.csv'
        self.logfile = logfile
        filehandler = open(logfile, 'a')
        print('Writing data to file: '+logfile)
        print('Press Ctrl - C to terminate')
        self.csvwriter = csv.writer(filehandler)
        self.csvwriter.writerow(['Time','Bus', 'MessageID', 'Message', 'MessageLength'])

        while self.keep_recording:
            try:
                # Get an `USBTransfer` instance for asynchronous use.
                transfer = self.handle.getTransfer()
                transfer.setBulk(usb1.ENDPOINT_IN | self.ENDPOINT_READ, self.BUFFER_SIZE, callback = self.process_received_data,)
                try:
                    transfer.submit()
                except usb1.DoomedTransferError:
                    pass

                try:
                    self.context.handleEvents()
                except usb1.USBErrorInterrupted:
                    pass

            except KeyboardInterrupt as e:
                # Capture the SIGINT event and call plot function to finalize the plot and save the data
                self.kill(signal.SIGINT)

#signal.signal(signal.SIGINT, self.kill)


    # SIGINT signal handler that will terminate lself.axogging of can data and save a final plot of the desired attribute of a message type

    def kill(self, sig):
        """
        `kill` catches SIGINT or CTRL-C while recording the data
        and closes the comma ai device connection
        """
        self.handle.close()
        print('CTRL-C (SIGINT) received. Stopping log.')
        self.keep_recording = False

        if self.msgType is None:
            self.msgType = 'Message Type'

        if self.attribute_num is None:
            self.attribute_num = 'Attribute'

        if self.visualize:
            # Ctrl-C Also saves the current figure being visualized with all data plotted on it.
            self.axis.clear()
            plt.rcParams["figure.figsize"] = (16,8)
            self.axis.plot(self.time, self.data, linestyle='None', color='firebrick', linewidth=2, marker='.', markersize = 3)
            self.axis.set_axisbelow(True)
            self.axis.minorticks_on()
            self.axis.grid(which='major', linestyle='-', linewidth='0.5', color='salmon')
            self.axis.grid(which='minor', linestyle=':', linewidth='0.25', color='dimgray')
            plt.title(self.msgType + ": " + self.attributeName)
            plt.xlabel('Time')
            plt.ylabel(self.attributeName)
            current_fig = plt.gcf()
            fileNameToSave = self.logfile[0:-4]
            current_fig.savefig(fileNameToSave + ".pdf", dpi = 300)
            pickle.dump(self.fig,open(fileNameToSave + ".pickle",'wb'))


    def parse_can_buffer(self, dat):
        """
        `parse_can_buffer` parses the can data received through the USB device
        and returns list of message ID, message and bus number

        Parameter
        -------------
        dat: `bytearray` byte data to be  parsed

        Returns
        ------------
        list containing message ID, message and bus number
        """
        ret = []
        for j in range(0, len(dat), 0x10):
            ddat = dat[j:j+0x10]
            f1, f2 = struct.unpack("II", ddat[0:8])
            extended = 4
            if f1 & extended:
                address = f1 >> 3
            else:
                address = f1 >> 21
            dddat = ddat[8:8+(f2&0xF)]
            ret.append((address, f2>>16, dddat, (f2>>4)&0xFF))
        return ret
