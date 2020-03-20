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

__maintainer__ = 'Rahul Bhadani'
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

# cantools import
import cantools
import strym.DBC_Read_Tools as dbc

class strymread:
    '''
    `strymread` reads the logged CAN data from the given CSV file.
    This class provides several utilities functions

    Parameters
    ----------------
    csvfie: `str`
        The CSV file to be read
    
    dbcfile: `str`
        The DBC file which will provide codec for decoding CAN messages

    Attributes
    ---------------
    dbcfile: `string` **optional**
        The filepath of DBC file 

        Default Value = ''
    
    csvfile:`string`
        The filepath of CSV Data file

    dataframe: `pandas.Dataframe`
        Pandas dataframe that stores content of csvfile as dataframe

    candb: `cantools.db`
        CAN database fetched from DBC file

    Returns
    ---------------
    `strymread`
        Returns an object of type `strymread`

    Example
    ----------------
    >>> import strym
    >>> from strym import strymread
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> dbcfile = 'newToyotacode.dbc'
    >>> csvdata = '2020-03-20.csv'
    >>> r0 = strymread(csvfile=csvlist[0], dbcfile=dbcfile)
    '''

    def __init__(self, csvfile, dbcfile = '', **kwargs):
        plt.style.use('ggplot')
        plt.rcParams["font.family"] = "Times New Roman"
        # CSV File
        self.csvfile = csvfile

        # All CAN messages will be saved as pandas dataframe
        self.dataframe = pd.read_csv(self.csvfile)

        # DBC file that has CAN message codec
        self.dbcfile = dbcfile
        # save the CAN database for later use
        if self.dbcfile:
            self.candb = cantools.db.load_file(self.dbcfile)

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

    def _get_ts(self, msg_name, msg_id):
        '''
        
        '''
        if not self.dbcfile:
            self._set_dbc()
        return dbc.convertData(msg_name, msg_id,  self.dataframe, self.candb)

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
        plt.style.use('ggplot')
        plt.rcParams["figure.figsize"] = (16,8)
        fig, axes = plt.subplots(ncols=2, nrows=4)
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
        `triptime` retrieves total duration of the recording for given CSV-formatted log file.

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
        return self._get_ts('SPEED', 1)

    def accely(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for acceleration in y-direction from the CSV file
        
        '''
        signal_id = dbc.getSignalID('KINEMATICS', 'ACCEL_Y', self.candb)
        return self._get_ts('KINEMATICS', signal_id)

    def steer_torque(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for steering torque from the CSV file
        
        '''
        signal_id = dbc.getSignalID('KINEMATICS', 'STEERING_TORQUE', self.candb)
        return self._get_ts('KINEMATICS', signal_id)
    
    def yaw_rate(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for yaw rate from the CSV file
        
        '''
        signal_id = dbc.getSignalID('KINEMATICS', 'YAW_RATE', self.candb)
        return self._get_ts('KINEMATICS', signal_id)
    
    def steer_rate(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for steering  rate from the CSV file
        
        '''
        signal_id = dbc.getSignalID('STEER_ANGLE_SENSOR', 'STEER_RATE', self.candb)
        return self._get_ts('STEER_ANGLE_SENSOR', signal_id)

    def steer_angle(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for steering  angle from the CSV file
        
        '''
        signal_id = dbc.getSignalID('STEER_ANGLE_SENSOR', 'STEER_ANGLE', self.candb)
        return self._get_ts('STEER_ANGLE_SENSOR', signal_id)

    def steer_fraction(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for steering  fraction from the CSV file
        
        '''
        signal_id = dbc.getSignalID('STEER_ANGLE_SENSOR', 'STEER_FRACTION', self.candb)
        return self._get_ts('STEER_ANGLE_SENSOR', signal_id)

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
        return self._get_ts(message, signal_id)

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
        return self._get_ts(message, signal_id)

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
        return self._get_ts(message, signal_id)
   
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
        return self._get_ts(message, signal_id)


    def rel_accel(self, track_id):
        '''
        utility function to return timeseries relative acceleration of detected object from radar traces of particular track id

        Parameters
        --------------
        track_id: `numpy array`

        Returns 
        -----------
        `pandas.DataFrame`
            Timeseries longitduinal distance data from the CSV file
        '''
        df_obj = pd.DataFrame()

        for id in track_id:
            if id < 0 or id > 15:
                print("Invalid track id:{}".format(track_id))
                raise
            df_obj1 =self._get_ts('TRACK_B_'+str(id), 1)
            if df_obj1.empty:
                continue
            df_obj = [df_obj, df_obj1]
            df_obj = pd.concat(df_obj)

        return df_obj

    def long_dist(self, track_id):
        '''
        utility function to return timeseries longitudinal distance from radar traces of particular track id

        Parameters
        -------------
        track_id: `numpy array`

        Returns 
        -----------
        `pandas.DataFrame`
            Timeseries longitduinal distance data from the CSV file
        '''
        df_obj = pd.DataFrame()

        for id in track_id:
            if id < 0 or id > 15:
                print("Invalid track id:{}".format(track_id))
                raise
            df_obj1 =self._get_ts('TRACK_A_'+str(id), 1)
            if df_obj1.empty:
                continue
            df_obj = [df_obj, df_obj1]
            df_obj = pd.concat(df_obj)

        return df_obj

    def lat_dist(self, track_id):
        '''
        utility function to return timeseries lateral distance from radar traces of particular track id

        Parameters
        -------------
        track_id: `numpy array`
        Returns 
        -----------
        `pandas.DataFrame`
            Timeseries lateral distance data from the CSV file
        '''
        df_obj = pd.DataFrame()

        for id in track_id:
            if id < 0 or id > 15:
                print("Invalid track id:{}".format(track_id))
                raise
            df_obj1 =self._get_ts('TRACK_A_'+str(id), 2)
            if df_obj1.empty:
                continue
            df_obj = [df_obj, df_obj1]
            df_obj = pd.concat(df_obj)

        return df_obj

    
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
            r = self.dataframe[self.dataframe['MessageID'] == 36]
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
        
    rate: `double`
        New uniform sampling rate
        
    
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
    plt.style.use('ggplot')
    plt.rcParams["figure.figsize"] = (12,8)
    params = {'legend.fontsize': 15,
        'legend.handlelength': 2}
    plt.rcParams.update(params)
    plt.rcParams["font.family"] = "Times New Roman"
    fig, axes = plt.subplots(ncols=2, nrows=2)
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

    fig =plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.minorticks_on()
    df.plot(x='Time', y='Message', ax = ax, linewidth=2, grid=True, linestyle='-', marker ='.', markersize=2 )
    ax.tick_params(axis="x", labelsize=15)
    ax.tick_params(axis="y", labelsize=15)
    #ax.grid(which='major', linestyle='-', linewidth='0.5', color='skyblue')
    #ax.grid(which='minor', linestyle=':', linewidth='0.25', color='dimgray')
    ax.set_xlabel('Time')
    ax.set_ylabel('Message', fontsize=15)
    ax.set_title("Timeseries plot: "+title)
    
    plt.show()

def violinplot(df, title='Violin Plot'):
    '''
    A violin plot to show the data distribution
    '''
    fig, axes = plt.subplots(ncols=2, nrows=1)
    ax = axes.ravel()
    sea.violinplot( ax = ax[0], y =df )
    ax[0].set_title("Violin Plot: " + title)

    sea.boxplot(y = df, ax=ax[1])
    ax[1].set_title("Box Plot: " + title)

    plt.show()
