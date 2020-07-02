#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani, Gustavo Lee
# Initial Date: Feb 17, 2020
# About: strymread class to read CAN data from CSV file recorded from `strym` class. Read associated README for full description
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
import math
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["figure.figsize"] = (16,8)
from scipy.interpolate import interp1d

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import pandas as pd # Note that this is not commai Panda, but Database Pandas
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import uuid
import scipy.special as sp
from scipy import integrate
import pickle
import os
from os.path import expanduser
import seaborn as sea

import libusb1
import usb1
import copy

# cantools import
import cantools
import strym.DBC_Read_Tools as dbc

class strymread:
    '''
    `strymread` reads the logged CAN data from the given CSV file.
    This class provides several utilities functions

    Parameters
    ----------------
    csvfile: `str`, `pandas.DataFrame`,  default = None
        The CSV file to be read. If `pandas.DataFrame` is supplied, then csvfile is set to None
        PandasDataFrame, if provided, must have  columns ["Time", "Message", "MessageID", "Bus"]
    
    dbcfile: `str`,  default = ""
        The DBC file which will provide codec for decoding CAN messages

    kwargs: variable list of argument in the dictionary format


    Attributes
    ---------------
    dbcfile: `str`, default = ""
        The filepath of DBC file 

    csvfile:`str`, default=None
        The filepath of CSV Data file.

    dataframe: `pandas.Dataframe`
        Pandas dataframe that stores content of csvfile as dataframe

    candb: `cantools.db`
        CAN database fetched from DBC file

    burst: `bool`
        A boolean flag that checks if CAN data came in burst. If `True`, then CAN Data was captured in burst, else
        `False`. If CAN Data came in burst (as in say 64 messages at a time or so)
        then any further analysis might not be reliable. Always check that. 

    success: `bool`
        A boolean flag, if `True`, tells that reading of CSV file was successful.



    Returns
    ---------------
    `strymread`
        Returns an object of type `strymread` upon successful reading or else return None

    Example
    ----------------
    >>> import strym
    >>> from strym import strymread
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> dbcfile = 'newToyotacode.dbc'
    >>> csvdata = '2020-03-20.csv'
    >>> r0 = strymread(csvfile=csvdata, dbcfile=dbcfile)
    '''

    def __init__(self, csvfile=None, dbcfile = "", **kwargs):
        plt.style.use('ggplot')
        plt.rcParams["font.family"] = "Times New Roman"
        # CSV File

        self.success = False

        if csvfile is None:
            print("csvfile is None. Unable to proceed with further analysis. See https://jmscslgroup.github.io/strym/api_docs.html#module-strym for further details.")
            return

        if isinstance(csvfile, pd.DataFrame):
            self.dataframe = csvfile
            self.csvfile = None
        elif isinstance(csvfile, str):
            self.csvfile = csvfile
        else:
            print("Unsupported type for csvfile. Please see https://jmscslgroup.github.io/strym/api_docs.html#module-strym for further details.")
            
            return

        if self.csvfile is not None:
            # All CAN messages will be saved as pandas dataframe
            try:
                self.dataframe = pd.read_csv(self.csvfile)
            except pd.errors.ParserError:
                print("Ill-formated CSV File. A properly formatted CAN-data CSV file must have at least following columns:  ['Time', 'Bus', 'MessageID', 'Message']")
                print("No data was written the csvfile. Unable to perform further operation")
                return
            except UnicodeDecodeError:
                print("Ill-formated CSV File. A properly formatted CAN-data  CSV file must have at least following columns:  ['Time', 'Bus', 'MessageID', 'Message']")
                print("No data was written the csvfile. Unable to perform further operation")
                return
            except pd.errors.EmptyDataError:
                print("CSVfile is empty.")
                return

        if self.dataframe.shape[0] == 0:
            print("No data was present in the csvfile or pandas dataframe supplied is empty. Unable to perform further operation")
            return
        
        self.dataframe  = self.dataframe.dropna()

        if set(['Time', 'MessageID', 'Message', 'Bus']).issubset(self.dataframe.columns) == False:
            print("Ill-formated CSV File or pandas dataframe. A properly formatted CAN-data CSV file/dataframe must have at least following columns:  ['Time', 'Bus', 'MessageID', 'Message']")
            print("Unable to perform further operation")
            return
        
        if np.any(np.diff(self.dataframe['Time'].values) < 0.0):
            print("Warning: Timestamps are not monotonically increasing. Further analysis is not recommended.")
            return

        # if control comes to the point, then the reading of CSV file was successful

        self.success = True
        self.dataframe['MessageID'] = self.dataframe['MessageID'].astype(int)
        self.dataframe =  timeindex(self.dataframe, inplace=True)

        self.burst = False

        # Check if data came in burst
        T = self.dataframe['Time'].diff()
        T_head = T[1:64]
        if np.mean(T_head) == 0.0:
            self.burst = True

        # DBC file that has CAN message codec
        self.dbcfile = dbcfile
        # save the CAN database for later use
        if self.dbcfile:
            self.candb = cantools.db.load_file(self.dbcfile)
        else:
            self.candb = None

    def _set_dbc(self):
        '''
        `_set_dbc` sets the DBC file

        '''
        self.dbcfile = input('DBC file unspecified. Enter the filepath of the DBC file: ')
        if self.dbcfile:
            try:
                self.dbcfile = str(self.dbcfile)
                print("The new DBC file entered is: {}".format(self.dbcfile))
            except ValueError:
                print('DBC file entered is not a string')
                raise
        self.candb = cantools.db.load_file(self.dbcfile)

    def get_ts(self, msg, signal, verbose=False):
        '''
        `get_ts`  returns Timeseries data by given `msg_name` and `signal_name`

        Parameters
        -------------
        msg: `string`| `int` A valid message that can be found in the given DBC file. Can be specified as message name or message ID
        
        signal: `string` | `int` A valid signal in string format corresponding to `msg_name` that can be found in the given DBC file.  Can be specified as signal name or signal ID

        verbose: `bool`, default = False
            If True, print some information
        
        '''
        if not self.dbcfile:
            self._set_dbc()

        assert(isinstance(msg, int) or isinstance(msg, str)), ("Only Integer message ID or string name is supported for msg_name")
        
        assert(isinstance(signal, int) or isinstance(signal, str)), ("Only Integer signal ID or string name is supported for signal_name")
        
        if isinstance(msg, int):
            msg = dbc.getMessageName(msg, self.candb)
            if verbose:
                print("Message Name: {}".format(msg))
        
        if isinstance(signal, int):
            signal = dbc.getSignalName(msg, signal, self.candb)
            if verbose:
                print("Signal Name: {}\n".format(signal))
            
        return dbc.convertData(msg, signal,  self.dataframe, self.candb)

    def messageIDs(self):
        '''

        Retreives list of all messages IDs available in the given CSV-formatted CAN data file.

        Returns
        ---------
        `list`
            A python list of all available message IDs  in the given CSV-formatted CAN data file.

        '''
        msgIDs = self.dataframe['MessageID'].unique()
        msgIDs.sort()
        return msgIDs

    def count(self):
        '''
        A utility function to plot counts for each Message ID as bar graph

        Example
        ---------
        >>> import strym
        >>> from strym import strymread
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> dbcfile = 'newToyotacode.dbc'
        >>> csvdata = '2020-03-20.csv'
        >>> r0 = strymread(csvfile=csvlist[0], dbcfile=dbcfile)
        >>> ro.count()    
        '''
        dataframe = self.dataframe
        r1 = dataframe[dataframe['MessageID'] <=200]
        r2 = dataframe[(dataframe['MessageID'] >200) & (dataframe['MessageID'] <= 400)]
        r3 = dataframe[(dataframe['MessageID'] >400) & (dataframe['MessageID'] <= 600)]
        r4 = dataframe[(dataframe['MessageID'] >600) & (dataframe['MessageID'] <= 800)]
        r5 = dataframe[(dataframe['MessageID'] >800) & (dataframe['MessageID'] <= 1000)]
        r6 = dataframe[(dataframe['MessageID'] >1000) & (dataframe['MessageID'] <= 1200)]
        r7 = dataframe[(dataframe['MessageID'] >1200) & (dataframe['MessageID'] <= 1400)]
        r8 = dataframe[(dataframe['MessageID'] >1400) ]

        r_df = [r1, r2, r3, r4, r5, r6, r7, r8]
        _setplots(ncols=2, nrows=4)
        fig, axes = create_fig(ncols=2, nrows=4)
        plt.rcParams['figure.figsize'] = (16, 8)
        fig.tight_layout(pad=5.0)
        ax = axes.ravel()

        for i in range(0, 8):
            cnt = r_df[i]['MessageID'].value_counts()
            cnt = cnt.sort_index(ascending=True)
            if cnt.empty:
                continue
            cnt.plot(kind='bar', ax=ax[i])
            ax[i].tick_params(axis="x")
            ax[i].tick_params(axis="y")
        fig.suptitle("Message ID counts: "+ self.csvfile, y=0.98)
        plt.show()

    def start_time(self):
        '''
        `start_time` retrieves the the human-readable  time when logging of the data started

        Returns
        ---------
        `str`
            Human-readable string-formatted time.
        '''
        return time.ctime(self.dataframe["Time"].iloc[0])

    def end_time(self):
        '''
        `end_time` retrieves the the human-readable  time  when logging of the data was stopped.

        Returns
        ---------
        `str`
            Human-readable string-formatted time.
        '''
        return time.ctime(self.dataframe["Time"].iloc[-1])

    def triptime(self):
        '''
        `triptime` retrieves total duration of the recording for given CSV-formatted log file in seconds.

        Returns
        ---------
        `double`
            Duration in seconds.

        '''
        duration = self.dataframe["Time"].iloc[-1] - self.dataframe["Time"].iloc[0]

        return duration

    def triplength(self, time=-1):
        '''
        `triplength` returns  total distance travelled while logging CAN data.

        Alternative, one can provide a second argument `time` to query how much distance was traveled in, say 50 seconds from start.

        Parameters
        -----------
        time: `double`
            Provide a valid elapsed time in seconds to query how much distance was traveled `time` seconds since the logging of data was started.

        '''
        # first convert speed in km/h to m/s
        speed  = self.speed()
        speed_in_ms =pd.DataFrame()
        speed_in_ms['Time'] = speed['Time']
        speed_in_ms['Message'] = speed['Message']*1000.0/3600.0

        dist = integrate(speed_in_ms)

        required_distance = 0.0
        if time == -1:
            required_distance =  dist['Message'].iloc[-1]
        else:
            if time <= self.triptime():
                desired_time = dist['Time'].iloc[0] + time
                data = dist[dist['Time'] > desired_time]
                required_distance =  data['Message'].iloc[0]
        return required_distance

    def driving_characteristics(self):
        '''
        `driving_characteristics` provides driving characteristics for the given driving data  in the form of python dictionary.

        Currently, the dictionary contains following metadata from the driving data
        
        - File name of CSV-formatedd CAN data file
        - Associated DBC file used
        - Start time of the trip in human-readable date format
        - End time of the trip in human-readable date format
        - Total duration of the trip
        - Total distance traveled in meters
        - Total distance traveled in kilometers
        - Total distance traveled in miles


        Returns
        ---------
        `dictionary`
            A python dictionary containing driving metadata
        '''

        start_time = self.start_time()
        end_time = self.end_time()
        trip_time = self.triptime()
        trip_length_in_meters = self.triplength()

        trip_length_in_km = trip_length_in_meters/1000.0
        trip_length_in_miles = trip_length_in_meters/1609.34

        drive = { 'filename': self.csvfile, 'dbcfile': self.dbcfile, 'distance_meters':trip_length_in_meters, 'distance_km': trip_length_in_km,  'distance_miles': trip_length_in_miles, 'start_time': start_time, 'end_time': end_time, 'trip_time': trip_time}

        return drive

    def speed(self):
        '''
        Returns
        ---------
        `pandas.DataFrame`
            Timeseries speed data from the CSV file

        Example
        ----------
        >>> import strym
        >>> from strym import strymread
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> dbcfile = 'newToyotacode.dbc'
        >>> csvdata = '2020-03-20.csv'
        >>> r0 = strymread(csvfile=csvlist[0], dbcfile=dbcfile)
        >>> speed = r0.ts_speed()
        
        '''
        return self.get_ts('SPEED', 1)

    def accely(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for acceleration in y-direction from the CSV file
        
        '''
        signal_id = dbc.getSignalID('KINEMATICS', 'ACCEL_Y', self.candb)
        return self.get_ts('KINEMATICS', signal_id)

    def accelx(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for acceleration in x-direction  (i.e. longitudinal acceleration) from the CSV file
        
        '''
        ts = self.get_ts('ACCELEROMETER', 'ACCEL_X')

        return ts

    def accelz(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for acceleration in z-direction  from the CSV file
        
        '''
        ts = self.get_ts('ACCELEROMETER', 'ACCEL_Z')

        return ts

    def steer_torque(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for steering torque from the CSV file
        
        '''
        signal_id = dbc.getSignalID('KINEMATICS', 'STEERING_TORQUE', self.candb)
        return self.get_ts('KINEMATICS', signal_id)
    
    def yaw_rate(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for yaw rate from the CSV file
        
        '''
        signal_id = dbc.getSignalID('KINEMATICS', 'YAW_RATE', self.candb)
        return self.get_ts('KINEMATICS', signal_id)
    
    def steer_rate(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for steering  rate from the CSV file
        
        '''
        signal_id = dbc.getSignalID('STEER_ANGLE_SENSOR', 'STEER_RATE', self.candb)
        return self.get_ts('STEER_ANGLE_SENSOR', signal_id)

    def steer_angle(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for steering  angle from the CSV file
        
        '''
        signal_id = dbc.getSignalID('STEER_ANGLE_SENSOR', 'STEER_ANGLE', self.candb)
        return self.get_ts('STEER_ANGLE_SENSOR', signal_id)

    def steer_fraction(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for steering  fraction from the CSV file
        
        '''
        signal_id = dbc.getSignalID('STEER_ANGLE_SENSOR', 'STEER_FRACTION', self.candb)
        return self.get_ts('STEER_ANGLE_SENSOR', signal_id)

    def wheel_speed_fl(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseeries data for wheel speed of front left tire from the CSV file
        
        '''
        message = 'WHEEL_SPEEDS'
        signal = 'WHEEL_SPEED_FL'
        signal_id = dbc.getSignalID(message,signal, self.candb)
        return self.get_ts(message, signal_id)

    def wheel_speed_fr(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseeries data for wheel speed of front right tire from the CSV file
        
        '''
        message = 'WHEEL_SPEEDS'
        signal = 'WHEEL_SPEED_FR'
        signal_id = dbc.getSignalID(message,signal, self.candb)
        return self.get_ts(message, signal_id)

    def wheel_speed_rr(self):
        '''
        Returns
        ---------
        `pandas.DataFrame`
            Timeseeries data for wheel speed of rear right tire from the CSV file
        
        '''
        message = 'WHEEL_SPEEDS'
        signal = 'WHEEL_SPEED_RR'
        signal_id = dbc.getSignalID(message,signal, self.candb)
        return self.get_ts(message, signal_id)
   
    def wheel_speed_rl(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseeries data for wheel speed of rear left tire from the CSV file
        
        '''
        message = 'WHEEL_SPEEDS'
        signal = 'WHEEL_SPEED_RL'
        signal_id = dbc.getSignalID(message,signal, self.candb)
        return self.get_ts(message, signal_id)

    def rel_accel(self, track_id):
        '''
        utility function to return timeseries relative acceleration of detected object from radar traces of particular track id

        Parameters
        --------------
        track_id: int | `numpy array` | list

        Returns 
        -----------
        `pandas.DataFrame` | `list<pandas.DataFrame>`
            Timeseries relative acceleration data from the CSV file
            
        '''
        df_obj = []
        if isinstance(track_id, int):
            if track_id < 0 or track_id > 15:
                print("Invalid track id:{}".format(track_id))
                raise
            df_obj =self.get_ts('TRACK_B_'+str(track_id), 1)
        elif isinstance(track_id, np.ndarray) or isinstance(track_id, list):
            for id in track_id:
                if id < 0 or id > 15:
                    print("Invalid track id:{}".format(track_id))
                    raise
                df_obj1 =self.get_ts('TRACK_B_'+str(id), 1)
                if df_obj1.empty:
                    continue
                df_obj.append(df_obj1)

        return df_obj

    def long_dist(self, track_id):
        '''
        utility function to return timeseries longitudinal distance from radar traces of particular track id

        Parameters
        -------------
        track_id: `int` | `numpy array` | `list`

        Returns 
        -----------
        `pandas.DataFrame` | `list<pandas.DataFrame>`
            Timeseries longitduinal distance data from the CSV file

        '''
        df_obj = []
        if isinstance(track_id, int):
            if track_id < 0 or track_id > 15:
                print("Invalid track id:{}".format(track_id))
                raise
            df_obj =self.get_ts('TRACK_A_'+str(track_id), 1)
        elif isinstance(track_id, np.ndarray) or isinstance(track_id, list):
            for id in track_id:
                if id < 0 or id > 15:
                    print("Invalid track id:{}".format(track_id))
                    raise
                df_obj1 =self.get_ts('TRACK_A_'+str(id), 1)
                if df_obj1.empty:
                    continue
                df_obj.append(df_obj1)

        return df_obj

    def lat_dist(self, track_id):
        '''
        utility function to return timeseries lateral distance from radar traces of particular track id

        Parameters
        -------------
        track_id: int | `numpy array` | list
         
        Returns 
        -----------
        `pandas.DataFrame` | `list<pandas.DataFrame>`
            Timeseries lateral distance data from the CSV file
        '''
        df_obj = []
        if isinstance(track_id, int):
            if track_id < 0 or track_id > 15:
                print("Invalid track id:{}".format(track_id))
                raise
            df_obj =self.get_ts('TRACK_A_'+str(track_id), 2)
        elif isinstance(track_id, np.ndarray) or isinstance(track_id, list):
            for id in track_id:
                if id < 0 or id > 15:
                    print("Invalid track id:{}".format(track_id))
                    raise
                df_obj1 =self.get_ts('TRACK_A_'+str(id), 2)
                if df_obj1.empty:
                    continue
                df_obj.append(df_obj1)

        return df_obj

    def acc_state(self):
        '''
        Get the cruise control state of the vehicle

        Returns
        ---------
        `pandas.DataFrame`
            Timeseries data with different levels corresponding to different cruise control state

            "disabled": 2, "hold": 11, "hold_waiting_user_cmd": 10, "enabled": 6,  "faulted": 5;

        '''
        message = 'PCM_CRUISE_SM'
        signal = 'CRUISE_CONTROL_STATE'
        signal_id = dbc.getSignalID(message,signal, self.candb)
        df = self.get_ts(message, signal_id)
        df.loc[(df.Message == 'disabled'),'Message']=2
        df.loc[(df.Message == 'hold'),'Message'] = 11
        df.loc[(df.Message == 'hold_waiting_user_cmd'),'Message'] = 10
        df.loc[(df.Message == 'enabled'),'Message'] = 6
        df.loc[(df.Message == 'faulted'),'Message'] = 5

        # plt.rcParams["figure.figsize"] = (16,5)
        # sea.scatterplot(x='Time', y='Message', data=df)
        # plt.yticks([0, 2, 5, 6, 10, 11], ['0', 'disabled (2)', 'faulted (5)', 'enabled (6)', 'hold_waiting_user_cmd (10)', 'hold (11)'])
        # plt.title(message + ": " + signal,  fontsize=18)
        # plt.xlabel('Time', fontsize=16)
        # plt.ylabel('Cruise Control State', fontsize=16)
        # plt.show()

        return df
        
    def plt_speed(self):
        '''
        Utility function to plot speed data
        '''
        dbc.plotDBC('SPEED',1,  self.dataframe, self.candb)

    def frequency(self):
        '''
        Retrieves the frequency of each message in a pandas.Dataframe()


        +-----------+----------+------------+---------+---------+---------+---------+
        | MessageID | MeanRate | MedianRate | RateStd | MaxRate | MinRate | RateIQR |
        +-----------+----------+------------+---------+---------+---------+---------+
        |           |          |            |         |         |         |         |
        +-----------+----------+------------+---------+---------+---------+---------+
        |           |          |            |         |         |         |         |
        +-----------+----------+------------+---------+---------+---------+---------+
        |           |          |            |         |         |         |         |
        +-----------+----------+------------+---------+---------+---------+---------+

        Returns
        ----------
        `pandas.DataFrame`
            Returns the a data frame containing mean rate, std rate, max rate, min rate, rate iqr

        '''

        messageIDs = self.messageIDs()

        f = pd.DataFrame()

        means = []
        medians = []
        maxs = []
        mins = []
        stds = []
        iqrs = []
        for ID in messageIDs:
            r = self.dataframe[self.dataframe['MessageID'] == ID]
            tdiff = 1./r['Time'].diff()
            tdiff = tdiff[1:]
            means.append(np.mean(tdiff.values))
            medians.append(np.median(tdiff.values))
            maxs.append(np.max(tdiff.values))
            mins.append(np.min(tdiff.values))
            stds.append(np.std(tdiff.values))

            first_quartile = np.percentile(tdiff.values, 25)
            third_quartile = np.percentile(tdiff.values, 75)
            iqrs.append(third_quartile- first_quartile) #interquartile range

        f['MessageID'] = messageIDs
        f['MeanRate'] = means
        f['MedianRate'] = medians
        f['RateStd'] = stds
        f['MaxRate'] = maxs
        f['MinRate'] = mins
        f['RateIQR'] = iqrs

        return f

    # Based on MATLAB Code provided by Gustavo Lee
    def trajectory(self, x_init  = 0.0, y_init= 0.0, data_rate = 50.0):
        '''
        A simple trajectory tracing function based on CAN data

        Parameters
        --------------
        x_init: `double`
            Initial X-coordinate of the vehicle
        
        y_init: `double`
            Initial Y-coordinate of the vehicle

        data_rate: `double`
            Rate at which message are sampled.

        Returns
        ----------

        `pandas.DataFrame`
            A pandas Dataframe with three columns: Time, X, Y, Vx, Vy
        '''

        ts_yaw_rate = self.yaw_rate()
        ts_speed = self.speed()

        # integrate yaw rate to get the heading
        ts_yaw = integrate(ts_yaw_rate)

        ts_resampled_yaw, ts_resampled_speed = ts_sync(ts_yaw, ts_speed)

        yaw = ts_resampled_yaw['Message'].values
        speed = ts_resampled_speed['Message'].values

        '''
        X_Pos = Initial_Position(1);
        Y_Pos = Initial_Position(2);
        kph_to_mps = 1000/3600;
        for i = 1:length(Complete_Speed)        
            Vx(i) = cosd(Complete_Heading(i))*kph_to_mps*Complete_Speed(i);
            Vy(i) = sind(Complete_Heading(i))*kph_to_mps*Complete_Speed(i);
            X_Pos(i) = X_Pos(end) + Vx(i)*dt;
            Y_Pos(i) = Y_Pos(end) + Vy(i)*dt;
        end
        '''
        dt = 1./data_rate
        X = []
        Y = []
        Vx = []
        Vy = []
        X.append(x_init)
        Y.append(y_init)
        Vx.append(0.0)
        Vy.append(0.0)
        kph_to_mps = 1000.0/3600.0 # kph to meter per second
        for i in range(0, ts_resampled_speed.shape[0]):
            vx = speed[i]*np.cos(np.deg2rad(yaw[i]))*kph_to_mps
            vy = speed[i]*np.sin(np.deg2rad(yaw[i]))*kph_to_mps
            x =  X[-1] + vx*dt
            y =  Y[-1] + vy*dt
            Vx.append(vx)
            Vy.append(vy)
            X.append(x)
            Y.append(y)
        traj = pd.DataFrame()
        
        Time = ts_resampled_yaw['Time']

        ExtendedTime = [Time[0] - dt]
        ExtendedTime[1:] = Time
        ExtendedTime= pd.Series(ExtendedTime)

        traj['Time'] = ExtendedTime
        traj['X'] = X
        traj['Y'] = Y
        traj['Vx'] = Vx
        traj['Vy'] = Vy

        return traj

    def msg_subset(self, **kwargs):
        '''
        Get the subset of message dataframe  based on a condition.

        Parameters
        -------------

        kwargs: variable list of argument in the dictionary format

            conditions: `str` | `list<str>`
            
                Human readable condition for subsetting of message dataframe.
                Following conditions are available:
                
                - *lead vehicle present*: Extracts only those messages for which there was lead vehicle present.
                - *cruise control on*: Extracts only those messages for which cruise control is on.
                - *operand op x*: Extracts those messages for which operator `op` is operated on operand to fulfil `x`. 
                
                Available operators `op` are `[>,<,==, !=, >=,<=]`

                Available operand `operand` are `[speed, acceleration, lead_distance, steering_angle, steering_rate, yaw_rate ]`.
                Details of operands are as follows:

                - speed: timeseries longitudinal speed of the vehicle
                - acceleration: timeseries longitudinal acceleration of the vehicle
                - lead_distance: timeseries distance of lead vehicle from the vehicle
                - steering_angle: timeseries steering angle of the vehicle
                - steering_rate: timeseries steering rate of the vehicle
                - yaw_rate: timeseries yaw rate of the vehicle

                For example, "speed < 2.3"
            
            time: (t0, t1)
            
                `t0` start elapsed-time
                `t1` end elapsed-time
                
                Extracts messages from time `t0` to `t1`. `t0` and `t1` denotes elapsed-time and not the actual time.
                
            ids: `list`

                Get message dataframe containing messages given the list `id`

          
        Returns
        -----------
        `strymread`
            Returns strymread object with a modified dataframe attribute
            
        '''
        df = None

        # Whole time by default
        time = (0, self.dataframe['Time'].iloc[-1] - self.dataframe['Time'].iloc[0])

        try:
            if isinstance(kwargs["time"], tuple):
                time = kwargs["time"]
            else:
                print('Time should be specified as a tuple with first value beginning time, and second value as end time. E.g . time=(10.0, 20.0)')
                raise
        except KeyError as e:
            pass

        # All message IDs by default
        ids  = self.messageIDs()

        try:
            if isinstance(kwargs["ids"], list):
                ids = kwargs["ids"]
            elif isinstance(kwargs["ids"], int):
                ids = []
                ids.append(kwargs["ids"])
            else:
                print('ids should be specified as an integer or a  list of integers.')
                raise
        except KeyError as e:
            pass

        df = self.dataframe[(self.dataframe['Time'] - self.dataframe['Time'].iloc[0] >= time[0]) & (self.dataframe['Time'] - self.dataframe['Time'].iloc[0] <= time[1])]
        df = df[df.MessageID.isin(ids)]

        conditions = None
        

        try:
            if isinstance(kwargs["conditions"], list):
                conditions = kwargs["conditions"]

            elif isinstance(kwargs["conditions"], str):
                conditions = []
                conditions.append(kwargs["conditions"])
            else:
                print('conditions should be specified as a string or a  list of strings with valid conditions. See documentation for more detail..')
                raise
        except KeyError as e:
            pass

        if conditions is None:
            return df

        subset_frames = []
        if conditions is not None:
            for con in conditions:
                slices = []
                index = None
                con = con.strip()
                con = " ".join(con.split()) # removee whitespace characters - even multiple of them and replaces them with a single whitespace
                
                # get all the meassages for which lead vehicle is present.
                if con.lower() == "lead vehicle present":
                    msg_DSU_CRUISE = self.get_ts('DSU_CRUISE', 6)
                    # 252m is read in the front when radar doesn't see any vehicle in the front.
                    index = msg_DSU_CRUISE['Message'] < 252

                elif con.lower() == "cruise control on":
                    acc_state = self.acc_state()
                    # acc state of 6 denotes that cruise control was enabled.
                    index = acc_state['Message'] == 6

                else:
                    conlower = con.lower()
                    constrip = conlower.split()
                    if len(constrip) < 3:
                        print("Unsupported conditions provided. See documentation for more details.")
                        raise ValueError("Unsupported conditions provided. See documentation for more details.")
                        return None

                    operators = ['<', '>', '>=','<=','==','!=']
                    operand = ['speed', 'acceleration', 'lead_distance', 'steering_angle', 'steering_rate', 'yaw_rate' ]

                    valuecheck = False
                    value = None
                    try:
                        value = float(constrip[2])
                        valuecheck = True
                    except ValueError:
                        valuecheck = False

                    # This is equivalent to pattern: `operator op value`
                    if (constrip[0] in operand) & (constrip[1] in operators) & (valuecheck):
                        if constrip[0] == 'speed':
                            speed = self.speed()
                            bool_result = eval(conlower)
                            index = bool_result['Message']
                        
                        elif constrip[0] == 'acceleration':
                            acceleration = self.accelx()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                        elif constrip[0] == 'steering_angle':
                            steering_angle = self.steer_angle()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                        elif constrip[0] == 'steering_rate':
                            steering_rate = self.steer_rate()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                        elif constrip[0] == 'steering_rate':
                            steering_rate = self.steer_rate()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                        elif constrip[0] == 'yaw_rate':
                            yaw_rate = self.yaw_rate()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                    elif (constrip[0].split('.')[0].isdigit()) &  (constrip[0].split('.')[2].lower()  == 'message') & (constrip[1] in operators) & (valuecheck):
                        # above condition check something like 386.LONG_DIST.Message > 34.0 where 345 is a valid message id.
                        required_id =  int(constrip[0].split('.')[0])

                        if constrip[0].split('.')[1].isdigit():
                            required_signal = int(constrip[0].split('.')[1])
                        else:
                            required_signal = constrip[0].split('.')[1].upper()

                        if required_id not in self.messageIDs():
                            print('Request Message ID {} was unavailable in the data file {}'.format(required_id,  self.csvfile))
                            raise

                        ts = self.get_ts(required_id, required_signal)

                        bool_result = eval("ts " + constrip[1] + constrip[2])
                        index = bool_result['Message']

                # Get the list of time slices satisfying the given condition
                if (index is None):
                    continue
                slices = timeslices(index)
                for time_frame in slices:
                    sliced_frame = df.loc[time_frame[0]: time_frame[1]]
                    subset_frames.append(sliced_frame)

        if len(subset_frames) > 0:
            set_frames = pd.concat(subset_frames)
            r_new = copy.deepcopy(self)
            r_new.dataframe = set_frames
            return r_new
        else:
            print("No data was extracted based on the given condition(s).")
            return None

    def time_subset(self, **kwargs):
        '''
        Get the time slices satsifying a particular condition for the dataframe.

        Parameters
        -------------
        
        kwargs: variable list of argument in the dictionary format

            conditions: `str` | `list<str>`
            
                Human readable condition for subsetting of message dataframe.
                Following conditions are available:
            
            - "lead vehicle present": Extracts only those message for which there was lead vehicle present.
            
        Returns
        --------
        `list`
            A list of tuples with start and end time of slices. E.g. [(t0, t1), (t2, t3), ...] satisfying the given conditions

        '''

        try:
            if isinstance(kwargs["conditions"], list):
                conditions = kwargs["conditions"]

            elif isinstance(kwargs["conditions"], str):
                conditions = []
                conditions.append(kwargs["conditions"])
            else:
                print('conditions should be specified as a string or a  list of strings with valid conditions. See documentation for more detail..')
                raise
        except KeyError as e:
            pass

        slices_set = []
        if conditions is not None:
            for con in conditions:
                slices = []
                index = None
                con = con.strip()
                con = " ".join(con.split()) # removee whitespace characters - even multiple of them and replaces them with a single whitespace
                # get all the meassages for which lead vehicle is present.
                if con.lower() == "lead vehicle present":
                    msg_DSU_CRUISE = self.get_ts('DSU_CRUISE', 6)
                    # 252m is read in the front when radar doesn't see any vehicle in the front.
                    index = msg_DSU_CRUISE['Message'] < 252
            
                elif con.lower() == "cruise control on":
                    acc_state = self.acc_state()
                    # acc state of 6 denotes that cruise control was enabled.
                    index = acc_state['Message'] == 6
                    
                else:
                    conlower = con.lower()
                    constrip = conlower.split()
                    if len(constrip) < 3:
                        print("Unsupported conditions provided. See documentation for more details.")
                        raise ValueError("Unsupported conditions provided. See documentation for more details.")
                        return None

                    operators = ['<', '>', '>=','<=','==','!=']
                    operand = ['speed', 'acceleration', 'lead_distance', 'steering_angle', 'steering_rate', 'yaw_rate' ]

                    valuecheck = False
                    value = None
                    try:
                        value = float(constrip[2])
                        valuecheck = True
                    except ValueError:
                        valuecheck = False

                    # This is equivalent to pattern: `operator op value`
                    if (constrip[0] in operand) & (constrip[1] in operators) & (valuecheck):
                        if constrip[0] == 'speed':
                            speed = self.speed()
                            bool_result = eval(conlower)
                            index = bool_result['Message']
                        
                        elif constrip[0] == 'acceleration':
                            acceleration = self.accelx()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                        elif constrip[0] == 'steering_angle':
                            steering_angle = self.steer_angle()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                        elif constrip[0] == 'steering_rate':
                            steering_rate = self.steer_rate()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                        elif constrip[0] == 'steering_rate':
                            steering_rate = self.steer_rate()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                        elif constrip[0] == 'yaw_rate':
                            yaw_rate = self.yaw_rate()
                            bool_result = eval(conlower)
                            index = bool_result['Message']

                    elif (constrip[0].split('.')[0].isdigit()) &  (constrip[0].split('.')[2].lower()  == 'message') & (constrip[1] in operators) & (valuecheck):
                        # above condition check something like 386.LONG_DIST.Message > 34.0 where 345 is a valid message id.
                        required_id =  int(constrip[0].split('.')[0])

                        if constrip[0].split('.')[1].isdigit():
                            required_signal = int(constrip[0].split('.')[1])
                        else:
                            required_signal = constrip[0].split('.')[1].upper()

                        if required_id not in self.messageIDs():
                            print('Request Message ID {} was unavailable in the data file {}'.format(required_id,  self.csvfile))
                            raise

                        ts = self.get_ts(required_id, required_signal)

                        bool_result = eval("ts " + constrip[1] + constrip[2])
                        index = bool_result['Message']

                # Get the list of time slices satisfying the given condition
                if (index is None):
                    continue
                slices = timeslices(index)
                slices_set.append(slices)

        return slices_set

    def extract(self, force_rewrite=False):
        '''
        Extract the known messages in HDF5 and MAT file for further downstream analysis

        Parameters
        -------------

        force_rewrite: `bool`, default: False
            If the mat file exists then `force_rewrite=True` regenerates the file and overwrite the existing one.
            If the mat file doesn't exist, then this parameter will be ignored.
 
        Returns
        -----------
        `list`: 
            A list of  strings that is file names of extracted data files
        '''

        matfile = self.csvfile[0:-4]+".mat"

        checkfile = os.path.exists(matfile)

        if checkfile:
            print("Data file {} already exists".format(matfile))

        if force_rewrite:
            print("Overwriting ...\n")
        else:
            print("No overwriting. Pass 'force_rewrite=True' to overwrite the extracted data file.")
            return

        if self.dbcfile == '':
            self._set_dbc()

        import scipy.io as sio

        db = self.candb

        if db is None:
            print("No CAN Database found. Unable to extract data")
            raise

        speed = self.speed()
        accely = self.accely()
        accelx = self.accelx()
        accelz = self.accelz()
        steer_torque = self.steer_torque()
        yaw_rate = self.yaw_rate()
        steer_rate = self.steer_rate()
        steer_angle = self.steer_angle()
        steer_fraction = self.steer_fraction()
        wheel_speed_fl = self.wheel_speed_fl()
        wheel_speed_fr = self.wheel_speed_fr()
        wheel_speed_rr = self.wheel_speed_rr()
        wheel_speed_rl = self.wheel_speed_rl()
        

        track_ids = np.arange(0,16)
        long_dist = self.long_dist(track_ids)
        lat_dist = self.lat_dist(track_ids)
        rel_accel = self.rel_accel(track_ids)
        acc_state = self.acc_state()

        dt_object = datetime.datetime.fromtimestamp(time.time())
        creation_date = dt_object.strftime('%Y-%m-%d-%H-%M-%S-%f')

        import socket
        system_name = socket.gethostname()
        variable_dictionary = {}
        variable_dictionary = { 'speed': speed.to_numpy(), 'accely': accely.to_numpy(), 'accelx': accelx.to_numpy(), 'accelz': accelz.to_numpy(), 
            'steer_torque': steer_torque.to_numpy(),  'yaw_rate': yaw_rate.to_numpy(), 'steer_rate': steer_rate.to_numpy(),
            'steer_angle': steer_angle.to_numpy(), 'steer_fraction': steer_fraction.to_numpy(), 'wheel_speed_fl': wheel_speed_fl.to_numpy(),
            'wheel_speed_fr': wheel_speed_fr.to_numpy(), 'wheel_speed_rr': wheel_speed_rr.to_numpy(),
            'wheel_speed_rl': wheel_speed_rl.to_numpy(), 'acc_state': acc_state, 'creation_date': creation_date,
            'system_name': system_name }

        for i in range(0, 16):
            variable_dictionary['long_dist_' + str(i)] = long_dist[0].to_numpy()
            variable_dictionary['lat_dist_' + str(i)] = lat_dist[0].to_numpy()
            variable_dictionary['rel_accel_' + str(i)] = rel_accel[0].to_numpy()

        for message in db.messages:
            print("Extracting {}".format(message.name))
            for signal in message.signal_tree:
                print("\t{}".format(signal))
                df = self.get_ts(msg=message.name, signal=signal)
                variable_dictionary[message.name+'_'+signal] = df.to_numpy()

        sio.savemat(matfile, variable_dictionary)

        files_written = []
        files_written.append(matfile)

        return files_written

def integrate(df, init = 0.0, integrator=integrate.cumtrapz):

    '''
    Integrate a timeseries data using scipy.integrate.cumtrapz

    Parameters
    -------------
    df: `pandas.Datframe`
        A two column Pandas data frame. First Column should have name 'Time' and Second Column Should be named 'Message'

    init: `double`
        Initial conditions for integration. Default Value: 0.0.

    integrator: `function`
        Integrator method. By default, it is `scipy.integrate.cumptrapz`

    Returns
    ----------
    df: `pandas.Datframe`
        A two column Pandas data frame with first column named 'Time' and second column named 'Message'

    '''
    if 'Time' not in df.columns:
        print("Data frame provided is not a timeseries data.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be 'Message' ")
        raise
    
    if 'Message' not in df.columns:
        print("Column naming convention violated.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be 'Message' ")
        raise

    result = integrator(df['Message'],df['Time'].values, initial=init)

    newdf = pd.DataFrame()
    newdf['Time'] = df['Time']
    newdf['Message'] = result
    return newdf

def differentiate(df, method='S', **kwargs):
    '''
    Differentiate the given timeseries datafrom using spline derivative
    
    Parameters
    -------------
    df:  `pandas.DataFrame`
        Original Dataframe to be differentiated

    Returns
    ------------
    `pandas.DataFrame`
        Differentiated Timeseries Data

    method: `string`, "S"
        Specifies method used for differentiation

        S: spline, spline based differentiation

    kwargs
        variable keyword arguments
        
    '''
    dfnew1 = pd.DataFrame()

    # find the time values that are same and drop the latter entry. It is essential for spline
    # interpolation to work 
    collect_indices = []
    for i in range(0, len(df['Time'].values)-1):
        if df['Time'].values[i] == df['Time'].values[i+1]:
            collect_indices.append(df.index.values[i+1])
    df = df.drop(collect_indices)
    assert(np.all(np.diff(df['Time'].values) > 0.0)), ('Timestamps are not unique')

    if method == "S":
        from scipy.interpolate import UnivariateSpline
        spl = UnivariateSpline(df['Time'], df['Message'], k=4, s=0)
        d = spl.derivative()
        
        dfnew1['Time'] = df['Time']
        dfnew1['Message'] = d(df['Time']) 

    return dfnew1

def denoise(df, method="MA", **kwargs):
    '''
    Denoise the time-series dataframe `df` using `method`. By default moving-average is used.

    Parameters
    --------------
    df:  `pandas.DataFrame`
        Original Dataframe to denoise

    method: `string`, "MA"
        Specifies method used for denoising

        MA: moving average (default)   

    kwargs
        variable keyword arguments

            window_size: `int`
                window size used in moving-average based denoising method

                Default value: 10

    Returns
    ------------
    `pandas.DataFrame`
        Denoised Timeseries Data

    '''
    window_size = 10

    try:
        window_size = kwargs["window_size"]
    except KeyError as e:
        pass
    
    
    df_temp = pd.DataFrame()
    df_temp['Time'] = df['Time']
    df_temp['Message'] = df['Message']
    
    if method == "MA":
        if window_size >=  df.shape[0]:
            print("Specified window size for moving-average method is larger than the length of time-series data")
            raise

        for index in range(window_size - 1, df.shape[0]):
            df_temp['Message'].iloc[index] = np.mean(df['Message'].iloc[index-window_size+1:index])
    
    return df_temp

def resample(df, rate=50):
    '''
    Resample the time-series dataframe `df` of varying, non-uniform sampling.

    Resampling is done using cubic interpolation and spline method.

    Parameters
    -------------
    df: `pandas.DataFrame`
        Original Dataframe to be resampled

    rate: `double`
        Desired sampling rate

    Returns
    ------------
    dfnew1: `pandas.DataFrame`
        New resampled timseries DataFrame

    '''
     # divide time-axis equal as per given rate
    dft0 = df['Time'].iloc[0]
    dftend = df['Time'].iloc[-1]
    n = (dftend - dft0)*rate
    n = int(n)
    t_newdf1 = np.linspace(dft0, dftend, num=n)
    
    # Interpolate function using cubic method
    f1 = interp1d(df['Time'].values,df['Message'], kind = 'cubic')
    newvalue1 = f1(t_newdf1)

    dfnew1 = pd.DataFrame()
    dfnew1['Time'] = t_newdf1
    dfnew1['Message'] = newvalue1    
    return dfnew1

def ts_sync(df1, df2, rate=50):
    '''
    Time-synchronize and resample two time-series dataframes of varying, non-uniform sampling.
    
    In a non-ideal condition, the first time of `df1` timeseries dataframe will not be same as
    the first time of `df2` dataframe.
    
    In that case, we will calculate the value of message at the latest of two first times of `df1`
    and `df2` using linear interpolation method. Call the latest of two first time as `latest_first_time`.
    
    Similarly, we will calculate the value of message at the earliest of two end times of `df1`
    and `df2` using linear interpolation method. Call the latest of two first time as `earliest_last_time`.
    
    Linear interpolation formula is 

    .. math::
        X_i = \cfrac{X_A - X_B}{a-b}(i-b) + X_B


    Next, we will truncate anything beyond [`latest_first_time`, `earliest_last_time`]
    
    Once we have common first and last time in both timeseries dataframes, we will use cubic interpolation 
    to do uniform sampling and interpolation of both time-series dataframe.
    
    Parameters
    -----------
    df1: `pandas.DataFrame`
        First timeseries datframe. First column name must be named 'Time' and second column must be 'Message'
    
    df2: `pandas.DataFrame`
        Second timeseries datframe. First column name must be named 'Time' and second column must be 'Message'
        
    rate: `double` | `str`
        `double`: New uniform sampling rate

        `str`: Inherting sampling rate from. If rate="first", then df2 will be sampled by inheriting time points from df1. 
        If rate="second" , then df1 will be sampled by inheriting time points from df2
    
    Returns
    -------
    
    dfnew1: `pandas.DataFrame`
        First new resampled timseries DataFrame
    
    dfnew2: `pandas.DataFrame`
        Second new resampled timseries DataFrame
    
    
    '''
    if df1['Time'].iloc[0] < df2['Time'].iloc[0]:
        # It means first time of df1 is earlier than df2 in time-series data
        # so we have to interpolate speed value at df2's first time.
        # we will use linear interpolation
        # find a next time on df1's axis that is greater than df2's first time
        tempdf = df1[df1['Time'] > df2['Time'].iloc[0]]
        timenext = tempdf['Time'].iloc[0]
        valuenext = tempdf['Message'].iloc[0]
        interpol = (df1['Message'].iloc[0] - valuenext)/(df1['Time'].iloc[0] - timenext )*(df2['Time'].iloc[0] - timenext) + valuenext
        df1 = df1.append({'Time' : df2['Time'].iloc[0] , 'Message' : interpol} , ignore_index=True)
    elif df1['Time'].iloc[0] > df2['Time'].iloc[0]:
        # It means first time of df2 is earlier than df1 in time-truncated data
        # so we have to interpolate message value at df1's first time.
        # we will use linear interpolation
        # find a next time on df2's axis that is greater thandf1's first time
        tempdf = df2[df2['Time'] > df1['Time'].iloc[0]]
        timenext = tempdf['Time'].iloc[0]
        valuenext = tempdf['Message'].iloc[0]
        interpol = (df2['Message'].iloc[0] - valuenext)/(df2['Time'].iloc[0] - timenext )*(df1['Time'].iloc[0] - timenext) + valuenext
        df2 = df2.append({'Time' : df1['Time'].iloc[0] , 'Message' : interpol} , ignore_index=True)
    
    df1= df1.sort_values(by=['Time'])
    df2= df2.sort_values(by=['Time'])
    
        ## Truncate.
    if df1['Time'].iloc[0] < df2['Time'].iloc[0]:
        df1 = df1[df1['Time'] >= df2['Time'].iloc[0]]
    elif df1['Time'].iloc[0] > df2['Time'].iloc[0]:
        df2 = df2[df2['Time'] >= df1['Time'].iloc[0]] 
    
    
    assert (df1.Time.iloc[0] == df2.Time.iloc[0]), ("First time of two timeseries dataframe is nor equal. First time of df1: {0}, First time of df2: {1}".format(df1.Time.iloc[0], df2.Time.iloc[0]))
    
    
    if df1['Time'].iloc[-1] < df2['Time'].iloc[-1]:
        # It means last time of df1 is earlier than df2 in time-series data
        # so we have to interpolate df2 value at df1's last time.
        # we will use linear interpolation
        # find a time before on df2's axis that is less than df1's last time
        tempdf = df2[df2['Time'] < df1['Time'].iloc[-1]]
        timefirst = tempdf['Time'].iloc[-1]
        valuefirst = tempdf['Message'].iloc[-1]
        interpol = (valuefirst - df2['Message'].iloc[-1])/(timefirst - df2['Time'].iloc[-1])*(timefirst - df1['Time'].iloc[-1]) + df2['Message'].iloc[-1]
        df2 = df2.append({'Time' : df1['Time'].iloc[-1] , 'Message' : interpol} , ignore_index=True)
    elif df1['Time'].iloc[-1] > df2['Time'].iloc[-1]:
        # It means last time of df2 is earlier than df1 in time-series data
        # so we have to interpolate df1 value at df2's last time.
        # we will use linear interpolation
        # find a next time on df1's axis that is less than df2's last time
        tempdf = df1[df1['Time'] < df2['Time'].iloc[-1]]
        timefirst = tempdf['Time'].iloc[-1]
        valuefirst = tempdf['Message'].iloc[-1]
        interpol = (valuefirst- df1['Message'].iloc[-1] )/(timefirst - df1['Time'].iloc[-1])*(timefirst - df2['Time'].iloc[-1]) + df1['Message'].iloc[-1]
        df1 = df1.append({'Time' : df2['Time'].iloc[-1] , 'Message' : interpol} , ignore_index=True)
        
    df1= df1.sort_values(by=['Time'])
    df2= df2.sort_values(by=['Time'])
    # truncate
    if df1['Time'].iloc[-1] < df2['Time'].iloc[-1]:
        df2 = df2[df2['Time'] <= df1['Time'].iloc[-1]]
    elif df1['Time'].iloc[-1] > df2['Time'].iloc[-1]:
        df1 = df1[df1['Time'] <= df2['Time'].iloc[-1]]


    assert (df1.Time.iloc[-1] == df2.Time.iloc[-1]), ("The last time of two timeseries dataframe is not equal. Last time of df1: {0}, Last time of df2: {1}".format(df1.Time.iloc[-1], df2.Time.iloc[-1]))

    # If rate is a string, then time points of one dataframe will be inherited from the other dataframe
    if isinstance(rate, str):
        if rate not in ["first", "second"]:
            print("Invalid value for rate.")
            raise

        # if rate == "first", then second dataframe will inherit time points from first dataframe for interpolation
        
        dfnew1 = pd.DataFrame()
        dfnew2 = pd.DataFrame()
        if rate == "first":
            
            is_sorted = lambda a: np.all(a[:-1] < a[1:])

            if(is_sorted(df2['Time'].values)) is not True:
                # At this some values on time axis are same (because we have sorted it the time above):
                # find the time values that are same and drop the latter entry. It is essential for cubic
                # interpolation to work 
                collect_indices = []
                for i in range(0,len(df2['Time'].values)-1):
                    if df2['Time'].iloc[i] == df2['Time'].iloc[i+1]:
                        collect_indices.append(i+1)
                df2 = df2.drop(df2.index[collect_indices])

            assert(is_sorted(df2['Time'].values)), "Time array is not sorrted for dataframe 2"
            
            # Interpolate function using cubic method
            f2 = interp1d(df2['Time'].values,df2['Message'], kind = 'cubic')
            newvalue2 = f2(df1['Time'].values)
            
            dfnew1['Time'] = df1['Time'].values
            dfnew1['Message'] = df1['Message'].values

            dfnew2['Time'] = df1['Time'].values
            dfnew2['Message'] = newvalue2


        elif rate=="second":

            is_sorted = lambda a: np.all(a[:-1] < a[1:])

            if(is_sorted(df1['Time'].values)) is not True:
                # At this some values on time axis are same (because we have sorted it the time above):
                # find the time values that are same and drop the latter entry. It is essential for cubic
                # interpolation to work 
                collect_indices = []
                for i in range(0,len(df1['Time'].values)-1):
                    if df1['Time'].iloc[i] == df1['Time'].iloc[i+1]:
                        collect_indices.append(i+1)
                df1 = df1.drop(df1.index[collect_indices])
            
            assert(is_sorted(df1['Time'].values)), "Time array is not sorrted for dataframe 1"


            f1 = interp1d(df1['Time'].values,df1['Message'], kind = 'cubic')
            newvalue1 = f1(df2['Time'].values)
            dfnew1['Time'] = df2['Time'].values
            dfnew1['Message'] = newvalue1

            dfnew2['Time'] = df2['Time'].values
            dfnew2['Message'] = df2['Message'].values

        return dfnew1, dfnew2
        
    # Control will go here only if rate is not "first" or "second"
    
    # divide time-axis equal as per given rate
    df1t0 = df1['Time'].iloc[0]
    df1tend = df1['Time'].iloc[-1]
    n = (df1tend - df1t0)*rate
    n = int(n)
    t_newdf1 = np.linspace(df1t0, df1tend, num=n)
    
    # divide time-axis equal as per given rate
    df2t0 = df2['Time'].iloc[0]
    df2tend = df2['Time'].iloc[-1]
    n = (df2tend - df2t0)*rate
    
    n = int(n)
    t_newdf2 = np.linspace(df2t0, df2tend, num=n)
    
    assert (t_newdf1.shape == t_newdf2.shape), "Total numbers of samples are not same in resamples timeseries."
            
    is_sorted = lambda a: np.all(a[:-1] < a[1:])

    if(is_sorted(df1['Time'].values)) is not True:
        # At this some values on time axis are same (because we have sorted it the time above):
        # find the time values that are same and drop the latter entry. It is essential for cubic
        # interpolation to work 
        collect_indices = []
        for i in range(0,len(df1['Time'].values)-1):
            if df1['Time'].iloc[i] == df1['Time'].iloc[i+1]:
                collect_indices.append(i+1)
        df1 = df1.drop(df1.index[collect_indices])
    
    assert(is_sorted(df1['Time'].values)), "Time array is not sorrted for dataframe 1"
    
    # Interpolate function using cubic method
    
    f1 = interp1d(df1['Time'].values,df1['Message'], kind = 'cubic')
    newvalue1 = f1(t_newdf1)

    if(is_sorted(df2['Time'].values)) is not True:
        # At this some values on time axis are same (because we have sorted it the time above):
        # find the time values that are same and drop the latter entry. It is essential for cubic
        # interpolation to work 
        collect_indices = []
        for i in range(0,len(df2['Time'].values)-1):
            if df2['Time'].iloc[i] == df2['Time'].iloc[i+1]:
                collect_indices.append(i+1)
        df2 = df2.drop(df2.index[collect_indices])

    assert(is_sorted(df2['Time'].values)), "Time array is not sorrted for dataframe 2"
    
    # Interpolate function using cubic method
    f2 = interp1d(df2['Time'].values,df2['Message'], kind = 'cubic')
    newvalue2 = f2(t_newdf2)
    
    dfnew1 = pd.DataFrame()
    dfnew1['Time'] = t_newdf1
    dfnew1['Message'] = newvalue1
    
    dfnew2 = pd.DataFrame()
    dfnew2['Time'] = t_newdf2
    dfnew2['Message'] = newvalue2
    
    return dfnew1, dfnew2

def split_ts(df, by=30.0):
    '''
    Split the timeseries data by `by` seconds
    
    Parameters
    ----------
    
    df: `pandas.DataFrame`
        dataframe to split
        
    by: `double`
        Specify the interval in seconds by which the timseries dataframe needs to split

    Returns
    -------
    
    `pandas.DataFrame`
        `dataframe` with an extra column *Second* denoting splits specified by interval
        
    `pandas.DataFrame` Array
        An array of splitted pandas Dataframe by Seconds


    '''
    dataframe = pd.DataFrame()
    dataframe['Time'] = df['Time']
    dataframe['Message'] = df['Message']
    initial_time = dataframe['Time'].iloc[0]
    second_elapsed = by
    dataframe['Second'] = 0.0
    for r, row in  dataframe.iterrows():
        next_time = initial_time + by
        if ((dataframe['Time'][r] >= initial_time) and (dataframe['Time'][r] <= next_time)):
            dataframe.loc[r, 'Second'] = second_elapsed
        if (dataframe['Time'][r] > next_time):
            initial_time = dataframe['Time'][r]
            second_elapsed = second_elapsed + by
            dataframe.loc[r, 'Second'] = second_elapsed
    
    df_split = []
    for second, df in dataframe.groupby('Second'):
        df_split.append(df)
    
    return dataframe, df_split

def centroid(X, Y):
    '''
    Calculates the centroid of a phase-space cluster specified by `X` and `Y` Vectors
    
    Parameters
    ----------
    X: `pandas.core.series.Series`
        X-coordinate on phase-space 
    Y: `pandas.core.series.Series`
        Y-coordinate on phase-space
        
    Returns
    --------
    `float, float`
        Centroid of the phase space cluster specified by `X` and `Y` Vectors
    '''
    
    C_x = np.sum(X)/len(X)
    C_y = np.sum(Y)/len(Y)
    
    return C_x, C_y

def AWCSS(X, Y):
    '''
    Calculates the average distance of phase-space cluster specified by `X` and `Y` Vectors from its centroid
    
    Parameters
    ----------
    X: `pandas.core.series.Series`
        X-coordinate on phase-space 
    Y: `pandas.core.series.Series`
        Y-coordinate on phase-space
        
    Returns
    --------
    `float`
        Average within the cluster distance from centroid
    '''
    
    assert (len(X) == len(Y)), ("length of X-vector and Y-vector are not same")
    C_x, C_y = centroid(X, Y)
    sum = 0.0
    for index in range(0, len(X)):
        if math.isnan(X.iloc[index]) or math.isnan(Y.iloc[index]):
            continue
        dist = np.square((C_x - X.iloc[index])**2.0 + (C_y - Y.iloc[index])**2.0)
        sum = sum + dist
    avg = sum/len(X)
    return avg

def ranalyze(df, title='Timeseries'):
    '''
    A utility  function to analyse rate of a timeseries data

    Parameters
    -------------
    title: `str`
        A descriptive string for this particular analysis

    '''
    if 'Time' not in df.columns:
        print("Data frame provided is not a timeseries data.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be 'Message' ")
        raise

    print('Analyzing Timestamp and Data Rate of ' + title)
    # Calculate instaneous rate
    diffs = df['Time'].diff()
    diffs = diffs.to_frame()
    diffs = diffs.rename(columns={'Time': 'Time Diff'})
    inst_rate = 1.0/(diffs)
    inst_rate = inst_rate.rename(columns={'Time Diff': 'Inst Rate'})
    df_toconcate = [df, diffs, inst_rate]
    df = pd.concat(df_toconcate, axis=1)
        
    inst_rate = inst_rate[1:] # drop the first row
    diffs = diffs[1:] # drop the first row
    # Calculate few parameters
    mean_rate = np.mean(inst_rate.to_numpy() )
    median_rate = np.median(inst_rate.to_numpy())
    max_rate = np.max(inst_rate.to_numpy())
    min_rate = np.min(inst_rate.to_numpy())
    std_rate = np.std(inst_rate.to_numpy())
    first_quartile = np.percentile(inst_rate.to_numpy(), 25)
    third_quartile = np.percentile(inst_rate.to_numpy(), 75)
    iqr = third_quartile- first_quartile #interquartile range


    print('Interquartile Range of Rate for {} is {} '.format(title, iqr))
    # plot the histogram of rate
    
    fig, axes = create_fig(ncols=2, nrows=2)
    # fig, axes = plt.subplots(ncols=2, nrows=2)
    ax1, ax2, ax3, ax4 = axes.ravel()
    inst_rate.hist(ax=ax1)
    ax1.minorticks_on()
    ax1.set_title(title+'\n'+'Rate Histogram')

    inst_rate.boxplot(ax=ax2)
    ax2.set_title(title+'\n' + 'Rate Box Plot' + '\n' + 'Mean: ' + str(round(mean_rate,2)) + ', Median:' + str(round(median_rate,2)) + ', Max:' + str(round(max_rate, 2)) + ', Min:' + str(round(min_rate,2)) + ', STD:' + str(round(std_rate,2)) + ', IQR:'+ str(round(iqr,2)))
    
    # plot the time diffs as a function of time.
    ax3.plot(df.iloc[1:]['Time'], diffs['Time Diff'], '.')
    ax3.minorticks_on()
    ax3.set_title(title+'\n'+'Timeseries of Time diffs')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Time Diffs')

    # plot frequency as a function of time
    ax4.plot(df.iloc[1:]['Time'],df.iloc[1:]['Inst Rate'], '.')
    ax4.minorticks_on()
    ax4.set_title(title+'\n'+'Timeseries of Instantaneous Frequency')
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Frequency')

    fig.suptitle("Message Rate Analysis: "+ title, y=0.98)
    plt.show()

def plt_ts(df, title=""):
    '''
    A utility function to plot a timeseries
    ''' 
    if 'Time' not in df.columns:
        print("Data frame provided is not a timeseries data.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be 'Message' ")
        raise

    fig, ax = create_fig(1)
    ax = ax[0]
    im = ax.scatter(df["Time"], df["Message"], c=df["Time"], alpha=0.8, cmap="magma", s=8)
    ax.set_title(title)
    ax.set_xlabel('Time')
    ax.set_ylabel('Message', fontsize=15)
    ax.set_title("Timeseries plot: "+title)
    plt.show()

def violinplot(df, title='Violin Plot'):
    '''
    A violin plot to show the data distribution
    '''
    _setplots(ncols=2, nrows=1)
    plt.rcParams['figure.figsize'] = [18, 12]
    fig, axes = plt.subplots(ncols=2, nrows=1)
    ax = axes.ravel()

    sea.violinplot( ax = ax[0], y =df , orient="h")
    ax[0].set_title("Violin Plot: " + title)

    sea.boxplot(y = df, ax=ax[1])
    ax[1].set_title("Box Plot: " + title)

    plt.show()

def temporalviolinplot(dataframe, by=30, title='Timeseries'):
    '''
    A temporal plot showing evolution of distribution as a function by time

    '''
    speed_split, split = split_ts(dataframe, by = by)
    import seaborn as sea
    fig, ax = create_fig(ncols=1, nrows=1)
    sea.violinplot(x="Second", y="Message", data=speed_split, ax = ax)
    ax.set_title("Temporal Violin Plot: " + title)
    plt.show()

def timeindex(df, inplace=False):
    '''
    Convert multi Dataframe of which on column must be 'Time'  to pandas-compatible timeseries where timestamp is used to replace indices

    Parameters
    --------------

    df: `pandas.DataFrame`
        A pandas dataframe with two columns with the column names "Time" and "Message"

    inplace: `bool`
        Modifies the actual dataframe, if true, otherwise doesn't.

    Returns
    -----------
    `pandas.DataFrame`
        Pandas compatible timeseries with a single column having column name "Message" where indices are timestamp in hum  an readable format.
    '''
    
    if inplace:
        newdf = df
    else:
        newdf =df.copy()

    newdf['Time'] = df['Time']
    newdf['ClockTime'] = newdf['Time'].apply(dateparse)
    Time = pd.to_datetime(newdf['Time'], unit='s')
    newdf['Clock'] = pd.DatetimeIndex(Time)
    
    if inplace:
        newdf.set_index('Clock', inplace=inplace)
        newdf.drop(['ClockTime'], axis = 1, inplace=inplace)
    else:
        newdf = newdf.set_index('Clock')
        newdf = newdf.drop(['ClockTime'], axis = 1)
    return newdf

def dateparse(ts):
    '''
    Converts POSIX timestamp to human readable Datformat as per local timezone

    Parameters
    -------------
    ts: `float`
        POSIX formatted timestamp 

    Returns
    ----------
    `str`
        Human-readable timestamp as per local timezone
    '''
    from datetime import datetime, timezone
    # if you encounter a "year is out of range" error the timestamp
    # may be in milliseconds, try `ts /= 1000` in that case
    ts = float(ts)
    d = datetime.fromtimestamp(ts).astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S:%f')
    return d

def timeslices(ts):
    """
    `timeslices` return a set of timeslices in the form of `[(t0, t1), (t2, t3), ...]`
    from `ts` where ts is a square pulse (or a timeseries) representing two levels 0 and 1
    or True and False where True for when a certain condition was satisfied and False for
    when condition was not satisfied. For example: ts should be a pandas Series (index with timestamp)
    with values  `[True, True, True, ...., False, False, ..., True, True, True ]` which represents 
    square pulses. In that case, `t0, t2, ...` are times for edge rising, and `t1, t2, ...` for edge falling.
    
    Parameters
    --------
    ts: `pandas.core.series.Series`
        A valid pandas time series with timestamp as index for the series
        
    Returns
    --------
    `list`
        A list of tuples with start and end time of slices. E.g. `[(t0, t1), (t2, t3), ...]`
     """
    
    if ts.dtypes == bool:
        ts = ts.astype(int)
        
    tsdiff = ts.diff()

    # diff creates a NaN in the first row, so that can affect the calculation.
    # In that case, we NaN can be replaced with 1 if there was True
    tsdiff[0] = ts[0]

    slices = []
    time_tuple = (None,  None)
    for index, row in tsdiff.iteritems():
        if row == 1:
            # Rising Edge Detected. We will get index to rising edge
            location_of_index = tsdiff.index.indexer_at_time(index)
            if time_tuple == (None, None):
                required_index = tsdiff.index[location_of_index+1].tolist()
                # time_tuple = (required_index[0], None)
                time_tuple = (index, None)
                
        elif row == -1:
            # Falling Edge Detected. We will get index before falling edge
            location_of_index = tsdiff.index.indexer_at_time(index)
            if time_tuple[1] == None and time_tuple[0] != None:
                required_index = tsdiff.index[location_of_index-1].tolist()
                time_tuple = (time_tuple[0], required_index[0] )
                #time_tuple = (time_tuple[0], index)
                slices.append(time_tuple)
                time_tuple = (None,  None)
            
    return slices


def _setplots(**kwargs):
    import IPython 
    
    shell_type = IPython.get_ipython().__class__.__name__

    ncols = 1
    nrows= 1
    if kwargs.get('ncols'):
        ncols = kwargs['ncols']
    
    if kwargs.get('nrows'):
        nrows = kwargs['nrows']

    if shell_type in ['ZMQInteractiveShell', 'TerminalInteractiveShell']:

        plt.style.use('default')
        plt.rcParams['figure.figsize'] = [18*ncols, 8*nrows]
        plt.rcParams['font.size'] = 16.0
        plt.rcParams['figure.facecolor'] = '#ffffff'
        plt.rcParams[ 'font.family'] = 'Roboto'
        plt.rcParams['font.weight'] = 'bold'
        plt.rcParams['xtick.color'] = '#828282'
        plt.rcParams['xtick.minor.visible'] = True
        plt.rcParams['ytick.minor.visible'] = True
        plt.rcParams['xtick.labelsize'] = 14
        plt.rcParams['ytick.labelsize'] = 14
        plt.rcParams['ytick.color'] = '#828282'
        plt.rcParams['axes.labelcolor'] = '#000000'
        plt.rcParams['text.color'] = '#000000'
        plt.rcParams['axes.labelcolor'] = '#000000'
        plt.rcParams['grid.color'] = '#cfcfcf'
        plt.rcParams['axes.labelsize'] = 15
        plt.rcParams['axes.titlesize'] = 16
        plt.rcParams['axes.labelweight'] = 'bold'
        plt.rcParams['axes.titleweight'] = 'bold'
        plt.rcParams["figure.titlesize"] = 24.0
        plt.rcParams["figure.titleweight"] = 'bold'

        plt.rcParams['legend.markerscale']  = 2.0
        plt.rcParams['legend.fontsize'] = 10.0
        plt.rcParams["legend.framealpha"] = 0.5

    else:
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = [18*ncols, 6*nrows]
        plt.rcParams['font.size'] = 12.0
        plt.rcParams['figure.facecolor'] = '#ffffff'
        plt.rcParams[ 'font.family'] = 'Roboto'
        plt.rcParams['font.weight'] = 'bold'
        plt.rcParams['xtick.color'] = '#828282'
        plt.rcParams['xtick.minor.visible'] = True
        plt.rcParams['ytick.minor.visible'] = True
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['ytick.color'] = '#828282'
        plt.rcParams['axes.labelcolor'] = '#000000'
        plt.rcParams['text.color'] = '#000000'
        plt.rcParams['axes.labelcolor'] = '#000000'
        plt.rcParams['grid.color'] = '#cfcfcf'
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['axes.titlesize'] = 10
        plt.rcParams['axes.labelweight'] = 'bold'
        plt.rcParams['axes.titleweight'] = 'bold'
        plt.rcParams["figure.titlesize"] = 24.0
        plt.rcParams["figure.titleweight"] = 'bold'
        plt.rcParams['legend.markerscale']  = 1.0
        plt.rcParams['legend.fontsize'] = 8.0
        plt.rcParams["legend.framealpha"] = 0.5
        

def create_fig(num_of_subplots=1, **kwargs):

    import IPython 
    shell_type = IPython.get_ipython().__class__.__name__


    nrows = num_of_subplots
    ncols = 1
    
    if kwargs.get('ncols'):
        ncols = kwargs['ncols']
    
    if kwargs.get('nrows'):
        nrows = kwargs['nrows']
    
    _setplots(ncols=ncols, nrows=nrows)
    fig, ax = plt.subplots(ncols=ncols, nrows=nrows)
    

    if nrows == 1:
        ax_ = []
        ax_.append(ax)
        ax = ax_
    else:
        ax = ax.ravel()

    if sys.hexversion >= 0x3000000:
        for a in ax:
            a.minorticks_on()
            a.grid(which='major', linestyle='-', linewidth='0.25', color='dimgray')
            a.grid(which='minor', linestyle=':', linewidth='0.25', color='dimgray')
            a.patch.set_facecolor('#efefef')
            a.spines['bottom'].set_color('#828282')
            a.spines['top'].set_color('#828282')
            a.spines['right'].set_color('#828282')
            a.spines['left'].set_color('#828282')
    else:
        for a in ax:
            a.minorticks_on()
            a.grid(True, which='both')
            
    return fig, ax