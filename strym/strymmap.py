#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Apr 2, 2020
# About: strymmap class to visualize and analyze GPS data from CSV file recorded using Grey Panda device and libpanda software. 
# Read associated README for full description
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

## General Data processing and visualization Import

import numpy as np
import math
from scipy.interpolate import interp1d

from .strymread import strymread

from .utils import configure_logworker
LOGGER = configure_logworker()

import pandas as pd # Note that this is not commai Panda, but Database Pandas
import os
import sys
from subprocess import Popen, PIPE
from dotenv import load_dotenv
load_dotenv()

import IPython 
shell_type = IPython.get_ipython().__class__.__name__

class strymmap:
    '''
    `strymmap` reads the GPS data from the given CSV file.
    This class provides several utilities functions to work with GPS Data

    Parameters
    ----------------
    csvfie: `str`
        The CSV file to be read
    
    Attributes
    ---------------

    csvfile:`string`
        The filepath of CSV Data file

    dataframe: `pandas.Dataframe`
        Pandas dataframe that stores content of csvfile as dataframe

    aq_time: `string`
        Acquisition Time of GPS Signal with valid Lattitude and Longitude in the form of human-readable date string as per local timezone

    latitude: `pandas.DataFrame`
        Latitude Timeseries

    longitude: `pandas.DataFrame`
        Longitude Timeseries

    altitude: `pandas.DataFrame`
        Altitude Timeseries

    success: `bool`
        If file reading was successful, then set to success to True

    Returns
    ---------------
    `strymmap`
        Returns an object of type `strymmap`

    Example
    ----------------
    
    >>> import strym
    >>> from strym import strymmap
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> csvdata = '2020-03-20.csv'
    >>> r0 = strymmap(csvfile=csvdata)
    '''

    def __init__(self, csvfile, **kwargs):

        self.success = False
        # if file size is less than 60 bytes, return without processing
        if os.path.getsize(csvfile) < 60:
            print("Nothing significant to read in {}. No further analysis is warranted.".format(csvfile))
            return

        if shell_type not in ['ZMQInteractiveShell', 'TerminalInteractiveShell']:
            raise ValueError("strymmap can only be used within Jupyter Notebook.")
        
        # CSV File
        self.csvfile = csvfile
        LOGGER.info("Reading GPS file {}".format(csvfile))        

        # All CAN messages will be saved as pandas dataframe
        try:
            status_category = pd.CategoricalDtype(categories=['A', 'V'], ordered=False)
            is_windows = sys.platform.startswith('win')

            if not is_windows:
                word_counts = Popen(['wc', '-l', self.csvfile], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                output, err = word_counts.communicate()
                output = output.decode("utf-8")
                output = output.strip()
                output = output.split(' ')
                n_lines = int(output[0])

                if n_lines < 4:
                    LOGGER.error("Not enough lines to read in {}".format(csvfile))
                    return
                    
                self.dataframe = pd.read_csv(self.csvfile, dtype={'Gpstime': np.float64,'Status':status_category, 'Long': np.float32, 'Lat': np.float32, 'Alt': np.float32, 'HDOP': np.float16, 'PDOP': np.float16, 'VDOP': np.float16}, nrows=n_lines - 2)
            else:
                self.dataframe = pd.read_csv(self.csvfile, dtype={'Gpstime': np.float64,'Status':status_category, 'Long': np.float32, 'Lat': np.float32, 'Alt': np.float32, 'HDOP': np.float16, 'PDOP': np.float16, 'VDOP': np.float16}, skipfooter=2)

        except pd.errors.ParserError:
            print("PraseError: Ill-formated CSV File {}. A properly formatted CSV file must have column names as ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']".format(self.csvfile))
            print("Not generating map for the drive route.")
            return
        except UnicodeDecodeError:
            print("Unicode Decode Error: Ill-formated CSV File {}. A properly formatted CSV file must have column names as ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']".format(self.csvfile))
            print("Not generating map for the drive route.")
            return
        except pd.errors.EmptyDataError:
            print("CSVfile is empty.")
            return

        if self.dataframe.shape[0] == 0:
            print("No data was present in the csvfile. Not generating map for the drive.")
            return
        self.dataframe  = self.dataframe.dropna()

        if not set(['Gpstime' ,'Status' ,'Long', 'Lat' ,'Alt' ,'HDOP' ,'PDOP', 'VDOP']).issubset(set(self.dataframe.columns)):
            print("Ill-formated CSV File. A properly formatted CSV file must have column names as ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']")
            print("Column Names found are {}".format(self.dataframe.columns.values))
            print("Not generating map for drive route.")
            return 

        status = self.dataframe['Status'] == 'A'
        self.dataframe = self.dataframe[status]

        if self.dataframe.shape[0] == 0:
            print("GPS failed to acquire satellite signal  during this drive. Not generating map for the drive.")
            return


        # At this point, GPS data file reading is successful, set `success` to `True`
        self.success = True
        self.aq_time = strymread.dateparse(self.dataframe['Gpstime'].values[0])
        print('GPS signal first acquired at {}'.format(self.aq_time))

        self.dataframe =  strymmap.timeindex(self.dataframe, inplace=True)

        self.latitude = self.dataframe['Lat']
        self.longitude = self.dataframe['Long']
        self.altitude = self.dataframe['Alt']

        coordinates = pd.DataFrame()
        coordinates['latitude'] = self.latitude
        coordinates['longitude'] = self.longitude

    def gpsdistance(self):
        """
        Calculate the distance covered based on the Lat, Long coordinates traversed

        Returns
        ---------
        Distance covered in meters

        """

        dist =  strymmap._calcgpsdist(self.dataframe)
        return dist

    @staticmethod
    def _calcgpsdist(df, sample_time = 0.1):

        distance = 0.0
        dist = [0.0]
        for i in range(1,df.shape[0]):
            lat1 = df.iloc[i-1]['Lat']
            long1 = df.iloc[i-1]['Long']
            lat2 = df.iloc[i]['Lat']
            long2 = df.iloc[i]['Long']
            phi_1 = lat1*math.pi/180.0 # in radians
            phi_2 = lat2*math.pi/180.0 # in radians
            delta_phi = phi_1 - phi_2
            lamda_1 = long1
            lamda_2 = long2
            delta_lambda  = (lamda_1 - lamda_2 )*math.pi/180.0

            R = 6371000 # Earth radius in meter

            a = (math.sin(delta_phi/2))**2 + math.cos(phi_1)*math.cos(phi_2)*math.sin(delta_lambda/2)*math.sin(delta_lambda/2)

            c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
            great_circle_distance = R*c # in meters
            
            # If distance is too large, then there is a gap between gps data points, I won't include gap distances
            # Here I assumed that in one sampke time interval car cannot go beyond 100 m/s, i.e. too large of a distance between two points
            if great_circle_distance >= 100*sample_time:
                continue

            distance = distance + great_circle_distance
            dist.append(distance)
        return dist

    def gps_speed(self):
        dist_vector = strymmap._calcgpsdist(self.dataframe)
        distdf = pd.DataFrame()
        distdf['Time'] = self.dataframe['Gpstime'].iloc[1:]
        distdf['Message'] = dist_vector
        gps_speed = strymread.differentiate(distdf, method='S', verbose=True)
        gps_speed = gps_speed.iloc[1:]
        gps_speed = strymread.denoise(gps_speed, method = 'MA')
        return gps_speed

    @staticmethod
    def timeindex(df, inplace=False):
        
        if inplace:
            newdf = df
        else:
            newdf =df.copy()

        newdf['Gpstime'] = df['Gpstime']
        newdf['ClockTime'] = newdf['Gpstime'].apply(strymread.dateparse)
        Time = pd.to_datetime(newdf['Gpstime'], unit='s')
        newdf['Clock'] = pd.DatetimeIndex(Time)
        
        if inplace:
            newdf.set_index('Clock', inplace=inplace)
            newdf.drop(['ClockTime'], axis = 1, inplace=inplace)
        else:
            newdf = newdf.set_index('Clock')
            newdf = newdf.drop(['ClockTime'], axis = 1)
        return newdf