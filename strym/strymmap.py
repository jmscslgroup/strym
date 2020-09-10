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

from .phasespace import phasespace
from .strymread import strymread

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

import IPython 
shell_type = IPython.get_ipython().__class__.__name__

if shell_type in ['ZMQInteractiveShell', 'TerminalInteractiveShell']:

    import bokeh.io
    import bokeh.plotting
    import bokeh.models
    import bokeh.transform
    from bokeh.palettes import Plasma256 as palette
    from bokeh.models import ColorBar
    from bokeh.io import output_notebook

    from bokeh.io.export import get_screenshot_as_png
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    output_notebook()

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

        if shell_type not in ['ZMQInteractiveShell', 'TerminalInteractiveShell']:
            print("strymmap can only be used within Jupyter Notebook.")
            raise

        load_dotenv()
        plt.style.use('ggplot')
        self.API_Key =os.getenv('GOOGLE_MAP_API_KEY')
        gmaps.configure(api_key=self.API_Key)
        plt.rcParams["font.family"] = "Times New Roman"
        # CSV File
        self.csvfile = csvfile

        # All CAN messages will be saved as pandas dataframe
        try:
            self.dataframe = pd.read_csv(self.csvfile)
        except pd.errors.ParserError:
            print("PraseError: Ill-formated CSV File. A properly formatted CSV file must have column names as ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']")
            print("Not generating map for the drive route.")
            return
        except UnicodeDecodeError:
            print("Unicode Decode Error: Ill-formated CSV File. A properly formatted CSV file must have column names as ['Gpstime', 'Status', 'Long', 'Lat', 'Alt', 'HDOP', 'PDOP', 'VDOP']")
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
            print("Column Names found are {}".format(self.dataframe.columns.values))
            print("Not generating map for drive route.")
            return 

        status = self.dataframe['Status'] == 'A'
        self.dataframe = self.dataframe[status]

        if self.dataframe.shape[0] == 0:
            print("GPS failed to acquire satellite signal  during this drive. Not generating map for the drive.")
            return


        self.aq_time = strymread.dateparse(self.dataframe['Gpstime'].values[0])
        print('GPS signal first acquired at {}'.format(self.aq_time))

        self.dataframe =  strymmap.timeindex(self.dataframe, inplace=True)

        self.latitude = self.dataframe['Lat']
        self.longitude = self.dataframe['Long']
        self.altitude = self.dataframe['Alt']

        centroid_lat, centroid_long = phasespace.centroid( self.latitude,self.longitude)
        center_coordinates = (centroid_lat, centroid_long)
        fig = gmaps.figure(center=center_coordinates, zoom_level=11.85, map_type='TERRAIN', )

        coordinates = pd.DataFrame()
        coordinates['latitude'] = self.latitude
        coordinates['longitude'] = self.longitude

        gmap_options = bokeh.models.GMapOptions(lat=centroid_lat, lng=centroid_long, 
                            map_type='roadmap', zoom=13)
        fig = bokeh.plotting.gmap(self.API_Key, gmap_options, title='Drive Route for' + self.csvfile, 
                width=900, height=800, tools=['hover', 'reset', 'wheel_zoom', 'pan'])
        source = bokeh.models.ColumnDataSource(self.dataframe)
        mapper = bokeh.transform.linear_cmap('Gpstime', palette, np.min(self.dataframe['Gpstime']), np.max(self.dataframe['Gpstime'])) 
        center = fig.circle('Long', 'Lat', size=4, alpha=1.0, 
                        color=mapper, source=source, )
        color_bar = ColorBar(color_mapper=mapper['transform'],  location=(0,0), title='Time')
        fig.add_layout(color_bar, 'right')

        self.mapfile = self.csvfile[0:-4] + '.html'
        bokeh.plotting.output_file(filename= self.mapfile, title='Drive Router for ' + self.csvfile)
        bokeh.plotting.save(fig, self.mapfile)

        self.fig = fig

        driver = webdriver.Chrome(ChromeDriverManager().install())
        self.image = get_screenshot_as_png(fig, height=800, width=1800, driver=driver)
        time.sleep(1)
        driver.close()
        driver.quit() # See https://web.archive.org/web/20200404100708/https://sites.google.com/a/chromium.org/chromedriver/getting-started and https://web.archive.org/web/20200404101003/https://www.selenium.dev/selenium/docs/api/py/index.html
        self.image.save(self.csvfile[0:-4] + '.png',"PNG")

    def plotroute(self, interactive=True):
        '''
        Plot the driving routes on Google Map

        Note: Only compatble to work with Jupyter Notebook. 
        You must execute `jupyter nbextension enable --py gmaps` before running jupyter notebook in your python environment.

        Parameters
        --------------
        interactive: `bool`
            `True`, `False`to specify whether to plot an interactive map or not. `True`: plot interactive map, `False`: plot map as an image
            
        Returns
        ---------
        `bokeh.plotting.gmap.GMap`
            Figure object correspond to Google Map figure with waypoints embedded on it

        '''

        if interactive:
            time.sleep(1)
            try:
                bokeh.plotting.reset_output()
                bokeh.plotting.output_notebook()
                bokeh.plotting.show(self.fig)  # angrily yells at me about single ownership
            except:
                bokeh.plotting.output_notebook()
                bokeh.plotting.show(self.fig)


        else:
            display(self.image)

        return self.fig

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