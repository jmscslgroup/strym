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
import math
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["figure.figsize"] = (16,8)
from scipy.interpolate import interp1d

from strym import centroid, dateparse

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
import seaborn as seas
import gmplot
import gmaps
from dotenv import load_dotenv
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

    Returns
    ---------------
    `strymmap`
        Returns an object of type `strymmap`

    Example
    ----------------
    
    You will need put to ensure that you have right Google API KEY before you can use  `strymmap`.
    You can generate API KEY at https://console.developers.google.com/projectselector2/apis/dashboard.

    Put API KEY as an environment variable in the file ~/.env as follows `export GOOGLE_MAP_API_KEY=abcdefghijklmnopqrstuvwxyz`.
    Use your own key instead of `abcdefghijklmnopqrstuvwxyz`.

    A good tutorial on how to perform API setup is given at https://web.archive.org/web/20200404070618/https://pybit.es/persistent-environment-variables.html

    >>> import strym
    >>> from strym import strymmap
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> csvdata = '2020-03-20.csv'
    >>> r0 = strymmap(csvfile=csvdata)
    '''

    def __init__(self, csvfile, **kwargs):
        load_dotenv()
        plt.style.use('ggplot')
        API_Key =os.getenv('GOOGLE_MAP_API_KEY')
        gmaps.configure(api_key=API_Key)
        plt.rcParams["font.family"] = "Times New Roman"
        # CSV File
        self.csvfile = csvfile

        # All CAN messages will be saved as pandas dataframe
        try:
            self.dataframe = pd.read_csv(self.csvfile)
        except pd.errors.ParserError:
            print("Ill-formated CSV File. A properly formatted CSV file must have column names as ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']")
            print("Not generating map for the drive route.")
            return
        except UnicodeDecodeError:
            print("Ill-formated CSV File. A properly formatted CSV file must have column names as ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']")
            print("Not generating map for the drive route.")
            return
        except pd.errors.EmptyDataError:
            print("CSVfile is empty.")
            return

        if self.dataframe.shape[0] == 0:
            print("No data was written the csvfile. Not generating map for the drive.")
            return
        self.dataframe  = self.dataframe.dropna()

        if np.all(self.dataframe.columns.values == ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']) == False:
            print("Ill-formated CSV File. A properly formatted CSV file must have column names as ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']")
            print("Not generating map for drive route.")
            return 

        status = self.dataframe['Status'] == 'A'
        self.dataframe = self.dataframe[status]

        if self.dataframe.shape[0] == 0:
            print("GPS failed to acquire satellite signal  during this drive. Not generating map for the drive.")
            return


        self.aq_time = dateparse(self.dataframe['Gpstime'].values[0])
        print('GPS signal first acquired at {}'.format(self.aq_time))

        centroid_lat, centroid_long = centroid(self.dataframe['Lat'], self.dataframe['Long'])

        self.gmap=gmplot.GoogleMapPlotter(centroid_lat, centroid_long, zoom = 14)
        self.gmap.apikey = API_Key
        
        self.latitude = self.dataframe['Lat']
        self.longitude = self.dataframe['Long']
        self.altitude = self.dataframe['Alt']

        # Location where you want to save your file.
        self.gmap.plot(self.latitude , self.longitude , 'cornflowerblue', edge_width=5)
        self.mapfile = self.csvfile[0:-4] + '.html'
        self.gmap.draw( self.mapfile )

    def plotroute(self):
        '''
        Plot the driving routes on Google Map

        Note: Only compatble to work with Jupyter Notebook. 
        You must execute `jupyter nbextension enable --py gmaps` before running jupyter notebook in your python environment.

        Returns
        ---------
        `gmaps.figure.Figure`
            Figure object correspond to Google Map figure with waypoints embedded on it
        '''
        centroid_lat, centroid_long = centroid(self.dataframe['Lat'], self.dataframe['Long'])
        center_coordinates = (centroid_lat, centroid_long)
        fig = gmaps.figure(center=center_coordinates, zoom_level=11.85, map_type='TERRAIN', )

        coordinates = pd.DataFrame()
        coordinates['latitude'] = self.latitude
        coordinates['longitude'] = self.longitude

        waypoints = coordinates.values.tolist()
        t = coordinates.values.tolist()
        t.reverse()
        wps = waypoints + t
        driving_route = gmaps.Polygon(
            wps,
            stroke_color=(0, 0, 255, 1),
            fill_color=(0, 0, 0, 0)
        )

        drawing_layer = gmaps.drawing_layer(
            features=[driving_route],
            show_controls=False
        )

        driving_layer = gmaps.heatmap_layer(coordinates)
        driving_layer.max_intensity = 100
        driving_layer.point_radius = 5
        fig.add_layer(drawing_layer)
        fig
        return fig