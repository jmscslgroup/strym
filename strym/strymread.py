#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Feb 17, 2020
# About: strymread class to read CAN data from CSV file captured using 
# libpanda (https://jmscslgroup.github.io/libpanda/) or from `strym` class.
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

import time
import ntpath
import datetime
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["figure.figsize"] = (16,8)
from scipy.interpolate import interp1d
from scipy import signal

import pandas as pd # Note that this is not commai Panda, but Database Pandas
from scipy import integrate
import pickle
import os
from os.path import expanduser
import seaborn as sea
import plotly.express as px
import csv
import copy

# cantools import
import cantools
import strym.DBC_Read_Tools as dbc
import pkg_resources
from subprocess import Popen, PIPE

dbc_resource = ''

try:
    import importlib.resources as pkg_resources
    with pkg_resources.path('strym', 'dbc') as rsrc:
        dbc_resource = rsrc
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    print("Python older than 3.7 detected. ")
    try:
        import importlib_resources as pkg_resources
        with pkg_resources.path('strym', 'dbc') as rsrc:
            dbc_resource = rsrc
    except ImportError:
        print("importlib_resources not found. Install backported importlib_resources through `pip install importlib-resources`")

import vin_parser as vp
# from sqlalchemy import create_engine
import sqlite3

import matplotlib.colors as colors
def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap
    
import IPython         
shell_type = IPython.get_ipython().__class__.__name__

if shell_type in ['ZMQInteractiveShell', 'TerminalInteractiveShell']:
    import plotly.offline as pyo
    # Set notebook mode to work in offline
    pyo.init_notebook_mode()
    
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from .config import config

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

    bus: `list` | default = None
        A list of integer correspond to Bus ID.

    dbcfolder: `str` | default = None
        Specifies a folder path where to look for appropriate dbc if  dbcfile='' or dbcfile = None
        Appropriate dbc file can be inferred from <brand>_<model>_<year>.dbc
        If dbcfolder  is None or empty string, then by default, strymread will look for dbc file in the dbc folder of the package where we ship sample dbc file to work with.
    
    verbose: `bool`
        Option for verbosity, prints some information when True

    createdb: `bool`
        If True, creates a sqlite3 database for raw CAN data if the database doesn't exist

    dbdir: `str`
        Optional argument that specifies where sqlite3 database will be stored.
        The default location is `~/.strym/`

    Attributes
    ---------------
    dbcfile: `str`, default = ""
        The filepath of DBC file 

    csvfile:`str`  | `pandas.DataFrame`
        The filepath of CSV Data file, or, raw  CAN Message DataFrame

    dataframe: `pandas.Dataframe`
        Pandas dataframe that stores content of csvfile as dataframe

    dataframe_raw: `pandas.Dataframe`
        Pandas original dataframe with all bus IDs. When `bus=` is passed to the constructor to filter out dataframe based on bus id, then original dataframe is save
        in dataframe_raw

    candb: `cantools.db`
        CAN database fetched from DBC file

    burst: `bool`
        A boolean flag that checks if CAN data came in burst. If `True`, then CAN Data was captured in burst, else
        `False`. If CAN Data came in burst (as in say 64 messages at a time or so)
        then any further analysis might not be reliable. Always check that. 

    success: `bool`
        A boolean flag, if `True`, tells that reading of CSV file was successful.

    bus: `list` | default = None
        A list of integer correspond to Bus ID.

    dbcfolder: `str` | default = None
        Specifies a folder path where to look for appropriate dbc if `dbcfile=""` or `dbcfile = None`
        Appropriate dbc file can be inferred from <brand>_<model>_<year>.dbc
        If dbcfolder  is None or empty string, then by default, strymread will look for dbc file in package's dbcfolder
        where we ship sample dbc file to work with.

    dbdir:`str`
        Location of database where sqlite3 database for CAN Dataframe will stored.
        Default location: `~/.strym/`

    database: `str`
        The name of the database corresponding to the model/make of the vehicle from which the CAN data
        was captured
    
    inferred_dbc: `str`
        DBC file inferred from the name of the csvfile passed.
            

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

    sunset = truncate_colormap(plt.get_cmap('magma'), 0.0, 0.7) # truncated color map from magma
    def __init__(self, csvfile, dbcfile = "", **kwargs):
       
       # success attributes will be set to True ultimately if everything goes well and csvfile is read successfully
        self.success = False

        # if file size is less than 60 bytes, return without processing
        if os.path.getsize(csvfile) < 60:
            print("Nothing significant to read in {}. No further analysis is warranted.".format(csvfile))
            return
        
        # Optional argument for verbosity
        self.verbose = kwargs.get("verbose", False)

        # Optional argument for bus ID
        self.bus = kwargs.get("bus", None)

        # Optional argument for dbcfolder where to look for dbc files
        self.dbcfolder = kwargs.get("dbcfolder", None)

        # Optional argument to tell strymread whether to create a table of the raw count in the db
        self.createdb = kwargs.get("createdb", False)

        default_db_dir = expanduser("~") + "/.strym/" 
        # Optional argument for where TIMESERIES DB will be saved
        self.dbdir = kwargs.get("dbdir", default_db_dir)

        if not os.path.exists(self.dbdir):
            if self.verbose:
                print("The directory {} for timeseries db doesn't exist, creating one".format(self.dbdir ))
            
            try:
                os.mkdir(self.dbdir)
            except OSError as error: 
                print(error)
        
        # If a single bus ID is passed, convert it to list of one item, if multiple bus ID
        # needs to be passed, then it must be passed as int
        if isinstance(self.bus, int):
            self.bus = [self.bus]    

        # If data were recorded in the first then burst attribute will be set to True. In practical scenario, we won't proceeding
        # with further analysis when data comes in burst, however, if csvfile has data in burst, no real error will be raised. It
        # will be upto user to check attribute boolean for True/False
        self.burst = False

        if csvfile is None:
            print("csvfile is None. Unable to proceed with further analysis. See https://jmscslgroup.github.io/strym/api_docs.html#module-strym for further details.")
            return

        if isinstance(csvfile, pd.DataFrame):
            self.dataframe = csvfile
            self.csvfile = ''
        elif isinstance(csvfile, str):

            # Check if file exists
            if not os.path.exists(csvfile):
                print("Provided csvfile: {} doesn't exist, or read permission error".format(csvfile))
                return
            self.csvfile = csvfile
            self.basefile = ntpath.basename(csvfile)
        else:
            print("Unsupported type for csvfile. Please see https://jmscslgroup.github.io/strym/api_docs.html#module-strym for further details.")
            
            return

        if len(self.csvfile) > 0:
            # All CAN messages will be saved as pandas dataframe
            try:
                # Get the number of rows using Unix `wc` word count function

                is_windows = sys.platform.startswith('win')

                if not is_windows:
                    word_counts = Popen(['wc', '-l', self.csvfile], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                    output, err = word_counts.communicate()
                    output = output.decode("utf-8")
                    output = output.strip()
                    output = output.split(' ')
                    n_lines = int(output[0])
                    if n_lines < 5:
                        print("Not enough data to read in the provided csvfile {}".format(ntpath.basename(self.csvfile)))
                        return 
                    self.dataframe = pd.read_csv(self.csvfile,dtype={'Time': np.float64,'Bus':np.uint8, 'MessageID': np.uint32, 'Message': str, 'MessageLength': np.uint16}, nrows=n_lines - 2)
                
                else:
                    self.dataframe = pd.read_csv(self.csvfile,dtype={'Time': np.float64,'Bus':np.uint8, 'MessageID': np.uint32, 'Message': str, 'MessageLength': np.uint16}, skipfooter=2)


            except pd.errors.ParserError:
                print("Ill-formated CSV File. A properly formatted CAN-data CSV file must have at least following columns:  ['Time', 'Bus', 'MessageID', 'Message']")
                print("No data was written the csvfile. Unable to perform further operation")
                return
            except UnicodeDecodeError:
                print("Ill-formated CSV File. A properly formatted CAN-data  CSV file must have at least following columns:  ['Time', 'Bus', 'MessageID', 'Message']")
                print("No data was written to the csvfile. Unable to perform further operation")
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

        def vin(csvfile):
            """
            returns the vehicle identification number, VIN, (if detected) from the filename
            uses a very very simple method of looking for a 17 char string near the end of the filename

            Parameters
            --------------
            csvfile: `str`
                Parse VIN number from the name of the `csvfile`

            """

            # we use underscores to split up the filename
            splits = csvfile.split('_')
            candidates = []
            # print(f'The splits of the file are {splits}')
            for split in splits:
                # all VIN are 17 chars long
                if len(split) == 17:
                    # keep them in an array, in case the path has other 17 char elements
                    candidates.append(split)
            if len(candidates) >= 1:
                # return the end element, as none of our fileendings has 17 char elements at this time
                # HACK: if folks create _some17charfileending.csv then this will fail
                return candidates[-1]
            else:
                return 'VIN not part of filename'

        vin = vin(self.csvfile)
        brand = "toyota"
        model = "rav4"
        year = "2019"

        try:
            if vp.check_valid(vin) == True:
                brand = vp.manuf(vin)
                brand = brand.split(" ")[0].lower()
                try:
                    model = vp.online_parse(vin)['Model'].lower()
                except ConnectionError as e:
                    print("Retrieving model of the vehicle requires internet connection. Check your connection.")
                    return
                year = str(vp.year(vin))

        except:
            if self.verbose:
                print('No valid vin... Continuing as Toyota RAV4. If this is inaccurate, please append VIN number to csvfile prefixed with an underscore.')

        self.inferred_dbc = "{}_{}_{}.dbc".format(brand, model, year)
            
        if (dbcfile is None) or(dbcfile==""):
            dbcfile = str(dbc_resource) + "/" + self.inferred_dbc
            
        if not os.path.exists(dbcfile):
            print("The dbcfile: {} doesn't exist, or read permission error".format(dbcfile))
            return
        
        # if control comes to the point, then the reading of CSV file was successful
        self.success = True
           
        self.dataframe =  self.timeindex(self.dataframe, inplace=True)
        self.dataframe_raw = None
        if self.bus is not None:
            if not np.all(np.isin(self.bus, self.dataframe['Bus'].unique())):
                print("One of the bus id not available.")
                print("Available BUS IDs are {}".format(self.dataframe['Bus'].unique()))
                self.success = False
                return
            else:
                self.dataframe_raw = self.dataframe.copy(deep = True)
                self.dataframe = self.dataframe[self.dataframe['Bus'].isin(self.bus)]

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
            
        # initialize the dbc lookups for any particular usage
        # this creates the dict later used to figure out which signals/msgs to 
        # use when decoding these data
        self._dbc_init_dict()


        # We will create an SQLite DB based on VIN number
        self.database = brand.upper() + '_' + model.upper() + '_' + year.upper() + ".db"
        self.raw_table = "RAW_CAN"

        self.db_location = '{}{}'.format(self.dbdir, self.database)
        
        if self.createdb:
            dbconnection = self.dbconnect(self.db_location)
            cursor = dbconnection.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS {} (Clock TIMESTAMP, Time REAL NOT NULL, Bus INTEGER, MessageID INTEGER, Message TEXT, MessageLength INTEGER, PRIMARY KEY (Clock, Bus, MessageID, Message));'.format(self.raw_table))
            dbconnection.commit()
            try:
                self.dataframe[['Time', 'Bus', 'MessageID', 'Message', 'MessageLength']].to_sql(self.raw_table, con=dbconnection, index=True, if_exists='append')
            except sqlite3.IntegrityError as e:
                print(e)
                if self.verbose:
                    print("Attempted to insert duplicate entries to the RAW_CAN table.\nRAW_CAN table has (Clock, Bus, MessageID, Message) composite primary key.")


    def dbconnect(self, db_location):
        """
        Creates dbconnection and returns db connection object
        
        Parameters
        ------------
        db_location: `str`
            sqlite db url

        """
        dbconnection = None
        try:
            dbconnection = sqlite3.connect(db_location)
        except sqlite3.Error as e:
            print(e)

        # dbengine = create_engine(db_location, echo = self.verbose )
        # dbengine.connect()
        # dbconnection = self.dbengine.raw_connection()
        return dbconnection

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
        msg: `string` | `int` 
            A valid message that can be found in the given DBC file. Can be specified as message name or message ID
        
        signal: `string` | `int`
            A valid signal in string format corresponding to `msg_name` that can be found in the given DBC file.  Can be specified as signal name or signal ID

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

    def count(self, plot = False):
        '''
        A utility function to return and optionally plot  the counts for each Message ID as bar graph

        Returns
        ----------
        `pandas.DataFrame`
            A pandas DataFrame with total message counts per Message ID and total count by Bus

        Example
        ---------
        >>> import strym
        >>> from strym import strymread
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> dbcfile = 'newToyotacode.dbc'
        >>> csvdata = '2020-03-20.csv'
        >>> r0 = strymread(csvfile=csvlist[0], dbcfile=dbcfile)
        >>> r0.count()    
        '''
        dataframe = self.dataframe

        if plot:
            r1 = dataframe[dataframe['MessageID'] <=200]
            r2 = dataframe[(dataframe['MessageID'] >200) & (dataframe['MessageID'] <= 400)]
            r3 = dataframe[(dataframe['MessageID'] >400) & (dataframe['MessageID'] <= 600)]
            r4 = dataframe[(dataframe['MessageID'] >600) & (dataframe['MessageID'] <= 800)]
            r5 = dataframe[(dataframe['MessageID'] >800) & (dataframe['MessageID'] <= 1000)]
            r6 = dataframe[(dataframe['MessageID'] >1000) & (dataframe['MessageID'] <= 1200)]
            r7 = dataframe[(dataframe['MessageID'] >1200) & (dataframe['MessageID'] <= 1400)]
            r8 = dataframe[(dataframe['MessageID'] >1400) ]

            r_df = [r1, r2, r3, r4, r5, r6, r7, r8]
            self._setplots(ncols=2, nrows=4)
            
            fig, axes = self.create_fig(ncols=2, nrows=4)
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
            fig.suptitle("Message ID counts: "+ ntpath.basename(self.csvfile), y=0.98)
            fig.show()

        bus = dataframe['Bus'].unique()
        bus.sort()
        columns = ['Counts_Bus_' + str(int(s)) for s in bus]
        columns.insert(0, 'MessageID')
        all_msgs = self.messageIDs()
        dfx = pd.DataFrame(columns=columns)
        dfx['MessageID'] = all_msgs
        dfx.index = dfx['MessageID'].values
        
        countbybus = dataframe.groupby(['MessageID', 'Bus'])

        
        for key,item in countbybus:
            a_group = countbybus.get_group(key)
            dfx.at[key[0], 'Counts_Bus_{}'.format(int(key[1]))] = a_group.shape[0]

        dfx.fillna(0, inplace=True)

        dfx['TotalCount'] = 0
        for b in bus:

            dfx['TotalCount'] =  dfx['TotalCount'] + dfx['Counts_Bus_{}'.format(int(b))]

        return dfx
        
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

        dist = self.integrate(speed_in_ms)

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
        # OLD
        # return self.get_ts('SPEED', 1)
        # NEW
        d=self.topic2msgs('speed')
        ts =  self.get_ts(d['message'],d['signal'])

        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def accely(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for acceleration in y-direction from the CSV file
        
        '''
        # OLD
        # ts = self.get_ts('KINEMATICS', 'ACCEL_Y')

        d=self.topic2msgs('accely')
        ts =  self.get_ts(d['message'],d['signal'])


        
        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def accelx(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for acceleration in x-direction  (i.e. longitudinal acceleration) from the CSV file
        
        '''
        
        # OLD
        # ts = self.get_ts('ACCELEROMETER', 'ACCEL_X')

        d=self.topic2msgs('accelx')
        ts =  self.get_ts(d['message'],d['signal'])


        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def accelz(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for acceleration in z-direction  from the CSV file
        
        '''
        ts = self.get_ts('ACCELEROMETER', 'ACCEL_Z')

        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def steer_torque(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for steering torque from the CSV file
        
        '''
        
        ts = self.get_ts('KINEMATICS', 'STEERING_TORQUE')

        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def yaw_rate(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for yaw rate from the CSV file
        
        '''
        ts = self.get_ts('KINEMATICS', 'YAW_RATE')

        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts
        

    def steer_rate(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for steering  rate from the CSV file
        
        '''
        ts = self.get_ts('STEER_ANGLE_SENSOR', 'STEER_RATE')


        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def steer_angle(self):
        '''
        Returns
        --------
        `pandas.DataFrame`
            Timeseries data for steering  angle from the CSV file
        
        '''
#         signal_id = dbc.getSignalID('STEER_ANGLE_SENSOR', 'STEER_ANGLE', self.candb)
#         return self.get_ts('STEER_ANGLE_SENSOR', signal_id)
        d=self.topic2msgs('steer_angle')
        ts = self.get_ts(d['message'],d['signal'])

        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts
    # NEXT

    def steer_fraction(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseries data for steering  fraction from the CSV file

        '''
        ts = self.get_ts('STEER_ANGLE_SENSOR', 'STEER_FRACTION')


        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def wheel_speed_fl(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseeries data for wheel speed of front left tire from the CSV file
        
        '''
        message = 'WHEEL_SPEEDS'
        signal = 'WHEEL_SPEED_FL'
        ts = self.get_ts(message, signal)


        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def wheel_speed_fr(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseeries data for wheel speed of front right tire from the CSV file
        
        '''
        message = 'WHEEL_SPEEDS'
        signal = 'WHEEL_SPEED_FR'
        ts = self.get_ts(message, signal)


        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def wheel_speed_rr(self):
        '''
        Returns
        ---------
        `pandas.DataFrame`
            Timeseeries data for wheel speed of rear right tire from the CSV file
        
        '''
        message = 'WHEEL_SPEEDS'
        signal = 'WHEEL_SPEED_RR'
        ts = self.get_ts(message, signal)


        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

    def wheel_speed_rl(self):
        '''
        Returns
        ----------
        `pandas.DataFrame`
            Timeseeries data for wheel speed of rear left tire from the CSV file
        
        '''
        message = 'WHEEL_SPEEDS'
        signal = 'WHEEL_SPEED_RL'
        ts = self.get_ts(message, signal)


        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

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
                raise ValueError("Invalid track id:{}".format(track_id))
                
            df_obj =self.get_ts('TRACK_B_'+str(track_id), 1)
        elif isinstance(track_id, np.ndarray) or isinstance(track_id, list):
            for id in track_id:
                if id < 0 or id > 15:
                    raise ValueError("Invalid track id:{}".format(track_id))
                    
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
                raise ValueError("Invalid track id:{}".format(track_id))
                
            df_obj =self.get_ts('TRACK_A_'+str(track_id), 1)
        elif isinstance(track_id, np.ndarray) or isinstance(track_id, list):
            for id in track_id:
                if id < 0 or id > 15:
                    raise ValueError("Invalid track id:{}".format(track_id))
                    
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
                raise ValueError("Invalid track id:{}".format(track_id))
                
            df_obj =self.get_ts('TRACK_A_'+str(track_id), 2)
        elif isinstance(track_id, np.ndarray) or isinstance(track_id, list):
            for id in track_id:
                if id < 0 or id > 15:
                    raise ValueError("Invalid track id:{}".format(track_id))
                    
                df_obj1 =self.get_ts('TRACK_A_'+str(id), 2)
                if df_obj1.empty:
                    continue
                df_obj.append(df_obj1)

        return df_obj

    def rel_velocity(self, track_id):
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
            df_obj =self.get_ts('TRACK_A_'+str(track_id), signal="REL_SPEED")
        elif isinstance(track_id, np.ndarray) or isinstance(track_id, list):
            for id in track_id:
                if id < 0 or id > 15:
                    print("Invalid track id:{}".format(track_id))
                    raise
                df_obj1 =self.get_ts('TRACK_A_'+str(id), signal="REL_SPEED")
                if df_obj1.empty:
                    continue
                df_obj.append(df_obj1)

        return df_obj

    def acc_state(self, plot = False):
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

        if plot:
            fig, ax = self.create_fig(1)
            plt.rcParams["figure.figsize"] = (16,6)
            ax[0].scatter(x='Time', y='Message', data=df,c = 'Time', s= 15)
            plt.yticks([0, 2, 5, 6, 10, 11], ['0', 'disabled (2)', 'faulted (5)', 'enabled (6)', 'hold_waiting_user_cmd (10)', 'hold (11)'])
            plt.title("ACC State " + os.path.basename(self.csvfile),  fontsize=18)
            plt.xlabel('Time', fontsize=16)
            plt.ylabel('Cruise Control State', fontsize=16)
            plt.show()

        return df

    def lead_distance(self):
        '''
        Get the distance information of lead vehicle

        Returns
        ----------
        `pandas.DataFrame`
            Timeseeries data for lead distance from the CSV file        
        '''
        
        ts = self.get_ts('DSU_CRUISE', 'LEAD_DISTANCE')

        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        # We will remove the bus column as it is irrelevant to bus column
        # if we want to remove duplicates
        if 'Bus' in ts.columns:
            ts.drop(columns=['Bus'], inplace=True)

        ts = strymread.remove_duplicates(ts)
        return ts

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
            r = strymread.remove_duplicates(r)
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
        ts_yaw = self.integrate(ts_yaw_rate)

        ts_resampled_yaw, ts_resampled_speed = self.ts_sync(ts_yaw, ts_speed)

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
                raise ValueError('Time should be specified as a tuple with first value beginning time, and second value as end time. E.g . time=(10.0, 20.0)')
                
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
                raise ValueError('ids should be specified as an integer or a  list of integers.')
                
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
                raise ValueError('conditions should be specified as a string or a  list of strings with valid conditions. See documentation for more detail..')
                
        except KeyError as e:
            pass

        if conditions is None:
            r_new = copy.deepcopy(self)
            r_new.dataframe = df
            return r_new

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
                            raise ValueError('Request Message ID {} was unavailable in the data file {}'.format(required_id,  self.csvfile))
                            

                        ts = self.get_ts(required_id, required_signal)

                        bool_result = eval("ts " + constrip[1] + constrip[2])
                        index = bool_result['Message']

                # Get the list of time slices satisfying the given condition
                if (index is None):
                    continue
                slices = self.timeslices(index)
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
        
        conditions: `str` | `list<str>`
        
            Human readable condition for subsetting of message dataframe.
            Following conditions are available:
        
        - "lead vehicle present": Extracts only those message for which there was lead vehicle present.
            
        Returns
        --------
        `list`
            A list of tuples with start and end time of slices. E.g. [(t0, t1), (t2, t3), ...] satisfying the given conditions

        '''

        conditions  = None
        try:
            if isinstance(kwargs["conditions"], list):
                conditions = kwargs["conditions"]

            elif isinstance(kwargs["conditions"], str):
                conditions = []
                conditions.append(kwargs["conditions"])
            else:
                raise ValueError('conditions should be specified as a string or a  list of strings with valid conditions. See documentation for more detail..')
                
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
                            raise ValueError('Request Message ID {} was unavailable in the data file {}'.format(required_id,  self.csvfile))
                            

                        ts = self.get_ts(required_id, required_signal)

                        bool_result = eval("ts " + constrip[1] + constrip[2])
                        index = bool_result['Message']

                # Get the list of time slices satisfying the given condition
                if (index is None):
                    continue
                slices = self.timeslices(index)
                slices_set.append(slices)

        return slices_set

    def export2mat(self, force_rewrite=False):
        '''
        Extract the known messages in MAT file for further downstream analysis

        Parameters
        -------------

        force_rewrite: `bool`, default: False
            If the mat file exists then `force_rewrite=True` regenerates the file and overwrite the existing one.
            If the mat file doesn't exist, then this parameter will be ignored.
 
        Returns
        -----------
        `list`: 
            A list of  strings that is file names of extracted data as .mat files
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
            raise ValueError("No CAN Database found. Unable to extract data")

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
        rel_velocity = self.rel_velocity(track_ids)
        rel_accel = self.rel_accel(track_ids)
        acc_state = self.acc_state()
        lead_distance = self.lead_distance()

        dt_object = datetime.datetime.fromtimestamp(time.time())
        creation_date = dt_object.strftime('%Y-%m-%d-%H-%M-%S-%f')

        import socket
        system_name = socket.gethostname()
        variable_dictionary = {}
        variable_dictionary = { 'speed': speed.to_numpy(), 'accely': accely.to_numpy(), 'accelx': accelx.to_numpy(), 'accelz': accelz.to_numpy(), 
            'steer_torque': steer_torque.to_numpy(),  'yaw_rate': yaw_rate.to_numpy(), 'steer_rate': steer_rate.to_numpy(),
            'steer_angle': steer_angle.to_numpy(), 'steer_fraction': steer_fraction.to_numpy(), 'wheel_speed_fl': wheel_speed_fl.to_numpy(),
            'wheel_speed_fr': wheel_speed_fr.to_numpy(), 'wheel_speed_rr': wheel_speed_rr.to_numpy(),
            'wheel_speed_rl': wheel_speed_rl.to_numpy(), 'acc_state': acc_state, 'lead_distance': lead_distance.to_numpy(), 'creation_date': creation_date,
            'system_name': system_name }

        for i in range(0, 16):
            variable_dictionary['long_dist_' + str(i)] = long_dist[0].to_numpy()
            variable_dictionary['lat_dist_' + str(i)] = lat_dist[0].to_numpy()
            variable_dictionary['rel_velocity_' + str(i)] = rel_velocity[0].to_numpy()
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

    def state_space(self, rate = 20, cont_method = 'nearest', cat_method = 'nearest', todb = False):
        """
        `state_space` generates a DatFrame with Time column and several other signals - uniformly
        sampled with common start and end-points for further downstream analysis
        """

        speed = self.speed()
        distance_covered  = self.integrate(speed)
        accelx = self.accelx()
        accely = self.accely()
        accelz = self.accelz()
        steer_torque = self.steer_torque()
        yaw_rate = self.yaw_rate()
        steer_rate = self.steer_rate()
        steer_angle = self.steer_angle()
        steer_fraction = self.steer_fraction()
        wheel_speed_fl = self.wheel_speed_fl()
        wheel_speed_fr = self.wheel_speed_fr()
        wheel_speed_rl = self.wheel_speed_rl()
        wheel_speed_rr = self.wheel_speed_rr()
        lead_distance = self.lead_distance()
        acc_status = self.acc_state()

        #we will be estimating relative velocity  based on lead distance data using AE method
        # For that first we will need to divide data into chunks
        chunks = strymread.create_chunks(lead_distance, column_of_interest = "Message", plot = False)
        relative_vel_list = []
        for c  in chunks:
            cdiff = strymread.differentiate(c, method="AE")
            relative_vel_list.append(cdiff)

        relative_vel = pd.concat(relative_vel_list)
        relative_vel.sort_index(inplace=True)

        dfs = [speed, distance_covered, accelx, accely, accelz, steer_torque, yaw_rate, 
            steer_rate, steer_angle, steer_fraction, wheel_speed_fl, 
            wheel_speed_fr, wheel_speed_rl, wheel_speed_rr, lead_distance,
            acc_status, relative_vel]
        
        states = [ "speed", "distance_covered", "accelx", "accely", "accelz", "steer_torque", 
                    "yaw_rate", "steer_rate", "steer_angle", "steer_fraction", 
                    "wheel_speed_fl", "wheel_speed_fr", "wheel_speed_rl",
                    "wheel_speed_rr", "lead_distance", "acc_status", "relative_vel"]

        categorical_index = [14]

        # Step 1. Find the latest start point among all of the signals.
        # Step 2. Find the earliest end point among all of the signals.
        # Step 3. Calculate the value at those point for all of the signals
        # Step 4. Truncate anything before the common first point
        # Step 5. Trunchate anything after the common end point.

        start_points = []
        end_points = []

        # print(dfs)
        
        for d in dfs:
            start_points.append(d['Time'][0])
            end_points.append(d['Time'][-1])

        # Step 1
        common_start_point  = np.max(start_points)
        
        argmax = [i for i, j in enumerate(start_points) if j == common_start_point]
        common_start_clock = pd.to_datetime(common_start_point, unit='s')

        # Step 2
        common_end_point  = np.min(end_points)
        argmin =  [i for i, j in enumerate(end_points) if j == common_end_point]
        common_end_clock = pd.to_datetime(common_end_point, unit='s')

        dflist = []
        
        # Step 3
        for i, d in enumerate(dfs):

            if i  not in argmax:
                d = d.append(pd.DataFrame({'Time':common_start_point, 'Message':float("NAN")}, 
                      index = [common_start_clock]), sort = False)

            d.sort_index(inplace=True)
            
            d.bfill(inplace=True)
                
            if i not in argmin:
                d = d.append(pd.DataFrame({'Time':common_end_point, 'Message':float("NAN")}, 
                        index = [common_end_clock]), sort = False)
        
            d.sort_index(inplace=True)

            if i in categorical_index:
                d.interpolate(method=cat_method, inplace=True)
            else:
                d.interpolate(method=cont_method, inplace=True)
        
            # Step 4 and Step 5
            d = d[(d['Time'] >= common_start_point) & (d['Time'] <= common_end_point)]
            
            if i in categorical_index:
                d = self.resample(d, rate=rate, categorical=True, cont_method =  cont_method, cat_method = cat_method)
            else:
                d = self.resample(d, rate=rate, categorical=False, cont_method = cont_method, cat_method = cat_method)

            dflist.append(d)

        state_var = dflist[0]
        for i, d in enumerate(dflist):
            state_var[states[i]] = d['Message']
            
        state_var.drop(columns=['Message'], inplace=True)  

        state_space_table  = "STATE_SPACE"
        dbconnection = self.dbconnect(self.db_location)
        cursor = dbconnection.cursor()
            
        cursor.execute('CREATE TABLE IF NOT EXISTS {} (Clock TIMESTAMP, Time REAL NOT NULL, speed REAL, \
            distance_covered REAL, accelx REAL, accely REAL, accelz REAL, steer_torque REAL, yaw_rate REAL, \
                steer_rate REAL, steer_angle REAL, steer_fraction REAL, wheel_speed_fl REAL, \
                    wheel_speed_fr REAL,wheel_speed_rl REAL,wheel_speed_rr REAL,\
                        lead_distance REAL, acc_status INTEGER, relative_vel REAL,\
                        PRIMARY KEY (Clock));'.format(state_space_table))

        states.append("Time")
        try:
            state_var[states].to_sql(self.raw_table, con=dbconnection, index=True, if_exists='append')
        except sqlite3.IntegrityError as e:
            if self.verbose:
                print("Insertion of raw CAN messages to STATE_SPACE table failed due to primary key violation. STATE_SPACE table has (Clock) primary key.")

        return state_var

    @staticmethod
    def create_chunks(df, continuous_threshold = 3.0, column_of_interest = 'Message', plot = False):
        """
        `create_chunks` computes separate chunks from a timeseries data.

        Parameters
        -------------
        df: `pandas.DataFrame`
            DataFrame that needs to divided into chunks

        continuous_threshold: `float`, Default = 3.0
            Continuous threshold above which we a change point detection is made, and signals start of a new chunk.

        column_of_interest: `str` , Default = "Message"
            Column of interest in DataFrame on which `continuous_threshold` should act to detect change point for creation of chunks

        plot: `bool`, Default = False
            If True, a scatter plot of Full timeseries of `df` overlaid with separate continuous chunks of `df` will be created.

        Returns
        ---------
        `list` of `pandas.DataFrame`
            Returns a list of DataFrame with same columns as `df`

        """
        if column_of_interest not in df.columns.values:
            print("Supplied column of interest not available in columns of supplied df.")
            raise
            
        if 'Time' not in df.columns.values:
            print("There is no Time column in supplied df. Please pass a df with a Time column.")
            raise

        

        # Messages such as acceleration, speed may come on multiple buses
        # as observed from data obtained from Toyota RAV4 and Honda Pilot
        # and often they are copy of each other, they can be identified as
        # duplicate if they were received with same time-stamp

        df = strymread.remove_duplicates(df)
        
        chunksdf_list = []
        for i, msg in df.iterrows():

            if i == df.index[0]:
                start = i
                last = i
                continue

            # Change point detection
            if np.abs(msg[column_of_interest] - df.loc[last][column_of_interest]) > continuous_threshold:
                chunk = df.loc[start:last]
                start = i
                chunksdf_list.append(chunk)

            last = i

            # when the last message is read
            if i == df.index[-1]:
                chunk = df.loc[start:last]
                chunksdf_list.append(chunk)

        if plot:
            fig, ax = strymread.create_fig(num_of_subplots=1)
            ax[0].scatter(x = 'Time', y = column_of_interest, data = df, s= 20, \
                        marker = 'o', alpha = 0.5, color = "#462255")

            for d in chunksdf_list:
                ax[0].scatter(x = 'Time', y = column_of_interest, data = d, s= 1)

            ax[0].set_xlabel('Time [s]')
            ax[0].set_ylabel(column_of_interest)
            ax[0].set_title('Full Timeseries overlaid with Separate Continuous Chunks')
            plt.show()
            
        return chunksdf_list

    def topic2msgs(self,topic):
        '''
        Return a dictionary value with the message ID and signal name for this particular DBC file, based on
        the passed in topic name. This is needed because various DBC files have different default names and
        signal structures depending on manufacturer. This redirection provides robustness to strym when the
        dbc files are not standardized---as they will never be so.

        Parameters
        -------------
        topic: `string`
            The string name of the topic in question. Only limited topics are supported by default

        Returns
        -------------
        d: `dictionary`
            Dictionary with the key/value pairs for `message` and `signal` that should be
            passed to the corresponding strym function. To access the message signal, use
            d['message'] and d['signal']
        '''
        #import os
        #dbcshort=os.path.basename(self.dbcfile)
        dbcshort = self.inferred_dbc

        #print('dbcshort={},topic={},dict={}'.format(dbcshort,topic,self.dbcdict))
        d = self.dbcdict[dbcshort][topic]
        # TODO add an exception here if the d return value is empty
        return d

    def _dbc_addTopic(self,dbcfile,topic,message,signal):
        '''
        Add a new message/signal pair to a topic of interest for this DBC file. For example,
        the Toyota Rav4 speed is found in a CAN Message with message name SPEED and signal 1, 
        but for a Honda Pilot the speed is in a message named ENGINE_DATA with signal 'XMISSION_SPEED'
        
        The use of this method allows the init function to consistently create dictionary entries
        that can be queried at runtime to get the correct message/signal pair for the DBC file in use,
        by functions that will be extracting the correct data.
        
        This function should typically be called only by _dbc_init_dict during initialization
        
        Parameters
        -------------
        dbcfile: `string`
            The stringname of the dbc file, without any path, but including the file extension
            
        topic: `string`
            The abstracted name of the signal of interest, e.g., 'speed'
        
        message: `string`
            The CAN Message Name from within the DBC file that corresponds to the topic
        
        signal: `string`
            The signal within the CAN message that provides the data of interest

        '''

        self.dbcdict[dbcfile][topic] = {'message': message, 'signal': signal}

    def _dbc_init_dict(self):
        '''
        Initialize the dictionary for all potential DBC files we are using. The name
        of the dbcfile (without the path) is used as the key, and the values are
        additional dictionaries that give the message/signal pair for signals of interest
        
        To add to this dictionary, take exising message/signal known pairs, and add them
        to the DBC file for which they are valid. The dictionary created by this init
        function is used by other functions to get the correct pairs for query.
        
        Parameters
        -------------
        None
        
        '''
        toyota_rav4_2019='toyota_rav4_2019.dbc'
        toyota_rav4_2020='toyota_rav4_2020.dbc'
        honda='honda_pilot_2017.dbc'
        
        self.dbcdict={  toyota_rav4_2019: { },
                        toyota_rav4_2020: { },
                        honda : { }
                     }

        self._dbc_addTopic(toyota_rav4_2019,'speed','SPEED',1)
        self._dbc_addTopic(toyota_rav4_2019,'steer_angle','STEER_ANGLE_SENSOR','STEER_ANGLE')
        self._dbc_addTopic(toyota_rav4_2019,'accely','KINEMATICS','ACCEL_Y')
        self._dbc_addTopic(toyota_rav4_2019,'accelx','ACCELEROMETER','ACCEL_X')



        self._dbc_addTopic(toyota_rav4_2020,'speed','SPEED',1)
        self._dbc_addTopic(toyota_rav4_2020,'steer_angle','STEER_ANGLE_SENSOR','STEER_ANGLE')
        self._dbc_addTopic(toyota_rav4_2020,'accely','KINEMATICS','ACCEL_Y')
        self._dbc_addTopic(toyota_rav4_2020,'accelx','ACCELEROMETER','ACCEL_X')


# NEXT
        self._dbc_addTopic(honda,'speed','ENGINE_DATA','XMISSION_SPEED')
        self._dbc_addTopic(honda,'steer_angle','STEERING_SENSORS','STEER_ANGLE')
        self._dbc_addTopic(honda,'accely','KINEMATICS','LAT_ACCEL')
        self._dbc_addTopic(honda,'accelx','VEHICLE_DYNAMICS','LONG_ACCEL')


    @staticmethod    
    def integrate(df, init = 0.0, msg_axis = 'Message', integrator=integrate.cumtrapz):

        '''
        Integrate a timeseries data using scipy.integrate.cumtrapz

        Parameters
        -------------
        df: `pandas.Datframe`
            A two column Pandas data frame. First Column should have name 'Time' and Second Column Should be named 'Message'

        init: `double`
            Initial conditions for integration. Default Value: 0.0.

        msg_axis: `str`
            The value of column in `df` the needs to be integrated with respect to the time.

            Default is 'Message`

        integrator: `function`
            Integrator method. By default, it is `scipy.integrate.cumptrapz`

        Returns
        ----------
        df: `pandas.Datframe`
            A two column Pandas data frame with first column named 'Time' and second column named 'Message'

        '''
        if 'Time' not in df.columns:
            print("Data frame provided is not a timeseries data.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be {}".format(msg_axis))
            raise ValueError('Time column not found')
        
        if msg_axis not in df.columns:
            print("Column naming convention violated.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be {} ".format(msg_axis))
            raise ValueError('{} column not found'.format(msg_axis))

        result = integrator(df[msg_axis],df['Time'].values, initial=init)

        newdf = pd.DataFrame()
        newdf['Time'] = df['Time']
        newdf['Message'] = result
        return newdf

    @staticmethod
    def differentiate(df, method='S', **kwargs):
        '''
        Differentiate the given timeseries datafrom using spline derivative
        
        Parameters
        -------------
        df:  `pandas.DataFrame`
            Original Dataframe to be differentiated

        method: `str`
            Specifies method used for differentiation

            S: spline, spline based differentiation
            
            AE: autoencoder based denoising-followed by discrete differentiation

        kwargs
            variable keyword arguments
        
        verbose: `bool`
            If True, print logs

        dense_time_points: `bool`
            Used in AutoEncoder `AE` based differentiation. If True, then differnetiation is computer on 50 times denser time points.
            
            
        Returns
        ------------
        `pandas.DataFrame`
            Differentiated Timeseries Data

        '''
        df_new = pd.DataFrame()
        dense_time_points = kwargs.get("dense_time_points", False)
        verbose = kwargs.get("verbose", False)

        # find the time values that are same and drop the latter entry. It is essential for spline
        # interpolation to work 
        
        # Usually timeseries have duplicated TimeIndex because more than one bus might produce same
        # information. For example, speed is received on Bus 0, and Bus 1 in Toyota Rav4.
        # Drop the duplicated index, if the type of the index pd.DateTimeIndex
        # Easier to drop the index, this way. If the type is not DateTime, first convert to DateTime
        # and then drop.
        if isinstance(df.index, pd.DatetimeIndex):
            df = df[~df.index.duplicated(keep='first')]
        else:
            df = strymread.timeindex(df, inplace=True)
            df= df[~df.index.duplicated(keep='first')]
            
        # collect_indices = []
        # for i in range(0, len(df['Time'].values)-1):
        #     if df['Time'].values[i] == df['Time'].values[i+1]:
        #         collect_indices.append(df.index.values[i+1])
        # df = df.drop(collect_indices)
        assert(np.all(np.diff(df['Time'].values) > 0.0)), ('Timestamps are not unique')

        # if number of datapoints is less than 6, fall back to Autoencoder method
        if df.shape[0] < 6:
            method = "AE"

        if method == "S":
            from scipy.interpolate import UnivariateSpline
            spl = UnivariateSpline(df['Time'], df['Message'], k=4, s=0)
            d = spl.derivative()
            
            df_new['Time'] = df['Time']
            df_new['Message'] = d(df['Time']) 

        elif method == "AE":
            time_original = df['Time'].values
        
            if time_original[-1] != time_original[0]:
                time = (time_original - time_original[0])/(time_original[-1] - time_original[0])
            else:
                time = time_original
            message_original = df['Message'].values    
            
            msg_max = np.max(message_original)
            msg_min = np.min(message_original)

            if msg_max != msg_min:
                message = (message_original  - msg_min)/(msg_max - msg_min)
            else:
                message = message_original
            
            import tensorflow as tf
            model = tf.keras.Sequential()
            model.add(tf.keras.layers.Dense(units = 1, activation = 'linear', input_shape=[1]))
            model.add(tf.keras.layers.Dense(units = 128, activation = 'relu'))
            model.add(tf.keras.layers.Dense(units = 64, activation = 'relu'))
            model.add(tf.keras.layers.Dense(units = 32, activation = 'relu'))
            model.add(tf.keras.layers.Dense(units = 64, activation = 'relu'))
            model.add(tf.keras.layers.Dense(units = 128, activation = 'relu'))
            model.add(tf.keras.layers.Dense(units = 1, activation = 'linear'))
            model.compile(loss='mse', optimizer="adam")
            
            if verbose:
                model.summary()
            # Training
            model.fit( time, message, epochs=1000, verbose=verbose)
            
            if dense_time_points:
                newtimepoints_scaled = np.linspace(time[0],time[-1], df.shape[0]*50)
            else:
                newtimepoints_scaled = time
            y_predicted_scaled = model.predict(newtimepoints_scaled)

            newtimepoints = newtimepoints_scaled*(time_original[-1] - time_original[0]) + time_original[0]
            y_predicted = y_predicted_scaled*(msg_max - msg_min) + msg_min
            
            df_new = pd.DataFrame()
            df_new['Time'] = newtimepoints
            df_new['Message'] = y_predicted
            
            collect_indices = []
            for i in range(0, len(df_new['Time'].values)-1):
                if df_new['Time'].values[i] == df_new['Time'].values[i+1]:
                    collect_indices.append(df_new.index.values[i+1])
            df_new = df_new.drop(collect_indices)
            
            assert(np.all(np.diff(df_new['Time'].values) > 0.0)), ('Timestamps are not unique')
            
            df_new['diff'] = df_new['Message'].diff()/df_new['Time'].diff()
            df_new.at[0,'diff']=0.0
            df_new.drop(columns=['Message'], inplace=True)
            df_new.rename(columns={"diff": "Message"}, inplace = True)

        df_new = strymread.timeindex(df_new)
        return df_new

    @staticmethod
    def remove_duplicates(df):
        '''
        Remove rows with duplicate time index from the timeseries data

        Parameters
        --------------
        df: `pandas.DataFrame`
            A pandas dataframe with at least one column `Time` or DateTimeIndex type Index
        '''
        # Usually timeseries have duplicated TimeIndex because more than one bus might produce same
        # information. For example, speed is received on Bus 0, and Bus 1 in Toyota Rav4.
        # Drop the duplicated index, if the type of the index pd.DateTimeIndex
        # Easier to drop the index, this way. If the type is not DateTime, first convert to DateTime
        # and then drop.
        if isinstance(df.index, pd.DatetimeIndex):
            df= df[~df.index.duplicated(keep='first')]
            
        else:
            df = strymread.timeindex(df, inplace=True)
            df= df[~df.index.duplicated(keep='first')]
            
        return df


    @staticmethod
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

    @staticmethod
    def resample(df, rate=50, categorical = False, **kwargs):
        '''
        Resample the time-series dataframe `df` of varying, non-uniform sampling.

        Resampling is done using cubic interpolation and spline method.

        Parameters
        -------------
        df: `pandas.DataFrame`
            Original Dataframe to be resampled

        rate: `double`
            Desired sampling rate in Hz

        cont_method: `str`
            Resampling method for continuous dataset. Available methods: "cubic", "nearest", "linear", "nearest", "exact"

        cat_method: `str'
            Resampling method for categorical dataset. Available method: "nearest"

        categorical: `bool`
            Boolean flag specifying if dataframe being passed represents a categorical data

         time_col: `str`
            Name of time column in `df`. Default value is "Time"

        msg_col: `str`
            Name of message column in `df`. Default value is "Message"
        
        Returns
        ------------
        dfnew1: `pandas.DataFrame`
            New resampled timseries DataFrame

        '''

        # Remove duplicate entries. If two data points have
        # same timestamps, then interpolation fails. Usually, we have
        # duplicates because same data is received on more than one bus.
        if not np.all(np.diff(df['Time']) > 0):
            df = strymread.remove_duplicates(df)


        cont_method = kwargs.get("cont_method", "cubic")

        cat_method = kwargs.get("cat_method", "nearest")

        # Optional argument for time column
        time_col = kwargs.get("time_col", "Time")

        # Optional argument for message column
        msg_col = kwargs.get("msg_col", "Message")

        dft0 = df[time_col].iloc[0]
        dftend = df[time_col].iloc[-1]
        n = (dftend - dft0)*rate
        n = int(n)
        t_newdf1 = np.linspace(dft0, dftend, num=n)
        # Interpolate function using cubic method

        if categorical:
            f1 = interp1d(df[time_col].values,df[msg_col], kind = cat_method)
        else:
            f1 = interp1d(df[time_col].values,df[msg_col], kind = cont_method)

        newvalue1 = f1(t_newdf1)
        dfnew = pd.DataFrame()
        dfnew[time_col] = t_newdf1
        dfnew[msg_col] = newvalue1
        dfnew =strymread.timeindex(dfnew)
       
        return dfnew

    @staticmethod
    def ts_sync(df1, df2, rate=50, **kwargs):
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

        method: `str`
            Resampling method for  dataset. Available methods: "cubic", "nearest", "linear", "nearest", "exact"
        
        Returns
        -------
        
        dfnew1: `pandas.DataFrame`
            First new resampled timseries DataFrame
        
        dfnew2: `pandas.DataFrame`
            Second new resampled timseries DataFrame
        
        
        '''

        # prechecks
        # 1. Check if data frames are empty
        # 2. If data frames contain "Time" columns or not
        # 3. 
        # 3. Two timeseries dataframes must overlap in time for ts_sync to work



        if df1.shape[0] < 5 or df2.shape[0] < 0:
            raise ValueError("One of the supplied dataframes has less than 5 rows, not enough for interpolation")

        if not "Time" in df1.columns:
            raise ValueError("First dataframe doesn't have 'Time' column")
        
        if not "Time" in df2.columns:
            raise ValueError("Second dataframe doesn't have 'Time' cFirstolumn")

        # when the first timeseries is before the second timeseries for the whole duration
        if (df1["Time"].iloc[0] < df2["Time"].iloc[0]) and (df1["Time"].iloc[-1] < df2["Time"].iloc[0]):
            fig, ax = strymread.create_fig(1)
            ax[0].scatter(x = 'Time', y = 'Message', data = df1, label = 'df1', s = 5)
            ax[0].scatter(x = 'Time', y = 'Message', data = df2, label = 'df2', s= 5)
            ax[0].legend()
            fig.show()
            raise ValueError("The first timeseries is before the second timeseries for the whole duration.\nNo synchronization can be performed in this case. See figure above")
            

        # when the second timeseries is before the first timeseries for the whole duration
        if (df2["Time"].iloc[0] < df1["Time"].iloc[0]) and (df2["Time"].iloc[-1] < df1["Time"].iloc[0]):
            fig, ax = strymread.create_fig(1)
            ax[0].scatter(x = 'Time', y = 'Message', data = df1, label = 'df1', s = 5)
            ax[0].scatter(x = 'Time', y = 'Message', data = df2, label = 'df2', s = 5)
            ax[0].legend()
            fig.show()
            raise ValueError("The second timeseries is before the first timeseries for the whole duration.\nNo synchronization can be performed in this case. See figure above.")

        
        method = kwargs.get("method", "cubic")
        # Usually timeseries have duplicated TimeIndex because more than one bus might produce same
        # information. For example, speed is received on Bus 0, and Bus 1 in Toyota Rav4.
        # Drop the duplicated index, if the type of the index pd.DateTimeIndex
        # Easier to drop the index, this way. If the type is not DateTime, first convert to DateTime
        # and then drop.
        if isinstance(df1.index, pd.DatetimeIndex):
            df1 = df1[~df1.index.duplicated(keep='first')]
        else:
            df1 = strymread.timeindex(df1, inplace=True)
            df1 = df1[~df1.index.duplicated(keep='first')]

        if isinstance(df2.index, pd.DatetimeIndex):
            df2 = df2[~df2.index.duplicated(keep='first')]
        else:
            df2 = strymread.timeindex(df2, inplace=True)
            df2 = df2[~df2.index.duplicated(keep='first')]

        
        assert(np.all(np.diff(df1['Time'].values) > 0.0)), ('Timestamps of first timeseries dataframe are not monotonically increasing.')

        assert(np.all(np.diff(df2['Time'].values) > 0.0)), ('Timestamps of second timeseries dataframe are not monotonically increasing.')
    
        ##################################################
        ###          Making the first time-points of two timeseries common         ###
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
        
        
        if df1.shape[0] < 3:
            Warning("Number of datapoints of truncated timeseries is less than 3, returning original dataframes. Resampling and time-synchronization is not possible")
            return df1, df2
        elif df2.shape[0] < 3:
            Warning("Number of datapoints of truncated timeseries is less than 3, returning original dataframes. Resampling and time-synchronization is not possible")
            return df1, df2
        
        assert (df1.Time.iloc[0] == df2.Time.iloc[0]), ("First time of two timeseries dataframe is nor equal. First time of df1: {0}, First time of df2: {1}".format(df1.Time.iloc[0], df2.Time.iloc[0]))
        ##################################################

        ##################################################
        ###          Making the last time-points of two timeseries common         ###
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

        if df1.shape[0] < 3:
            Warning("Number of datapoints of truncated timeseries is less than 3, returning original dataframes. Resampling and time-synchronization is not possible")
            return df1, df2
        elif df2.shape[0] < 3:
            Warning("Number of datapoints of truncated timeseries is less than 3, returning original dataframes. Resampling and time-synchronization is not possible")
            return df1, df2

        ##################################################
        # If rate is a string, then time points of one dataframe will be inherited from the other dataframe
        if isinstance(rate, str):
            if rate not in ["first", "second"]:
                print("Invalid value for rate.")
                raise ValueError("rate must either be 'First' or 'Second'")

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
                f2 = interp1d(df2['Time'].values,df2['Message'], kind = method)
                newvalue2 = f2(df1['Time'].values)
                
                dfnew1['Time'] = df1['Time'].values
                dfnew1['Message'] = df1['Message'].values
                dfnew1 = strymread.timeindex(dfnew1)

                dfnew2['Time'] = df1['Time'].values
                dfnew2['Message'] = newvalue2
                dfnew2 = strymread.timeindex(dfnew2)


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


                f1 = interp1d(df1['Time'].values,df1['Message'], kind = method)
                newvalue1 = f1(df2['Time'].values)
                dfnew1['Time'] = df2['Time'].values
                dfnew1['Message'] = newvalue1
                dfnew1 = strymread.timeindex(dfnew1)

                dfnew2['Time'] = df2['Time'].values
                dfnew2['Message'] = df2['Message'].values
                dfnew2 = strymread.timeindex(dfnew2)

            return dfnew1, dfnew2

        # Control will go here only if rate is not "first" or "second"
        
        
        # assert (t_newdf1.shape == t_newdf2.shape), "Total numbers of samples are not same in resamples timeseries."
                
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
        
        df1 = strymread.timeindex(df1)
        df2 = strymread.timeindex(df2)
        dfnew1 = strymread.resample(df = df1, rate = rate, cont_method = method)
        dfnew2 = strymread.resample(df = df2, rate = rate, cont_method = method)

        return dfnew1, dfnew2

    @staticmethod
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

    @staticmethod
    def ranalyze(df, title='Timeseries', savefig = False):
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

        # Removing duplicate timestamps
        if not np.all(np.diff(df['Time']) > 0):
            df = strymread.remove_duplicates(df)

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
        
        fig, axes = strymread.create_fig(ncols=2, nrows=2)
        # fig, axes = plt.subplots(ncols=2, nrows=2)
        ax1, ax2, ax3, ax4 = axes.ravel()
        inst_rate.hist(ax=ax1)
        ax1.minorticks_on()
        ax1.set_title('Rate Histogram')

        inst_rate.boxplot(ax=ax2)
        ax2.set_title('Rate Box Plot' + '\n' + 'Mean: ' + str(round(mean_rate,2)) + ', Median:' + str(round(median_rate,2)) + ', Max:' + str(round(max_rate, 2)) + ', Min:' + str(round(min_rate,2)) + ', STD:' + str(round(std_rate,2)) + ', IQR:'+ str(round(iqr,2)))
        
        # plot the time diffs as a function of time.
        ax3.plot(df.iloc[1:]['Time'], diffs['Time Diff'], '.')
        ax3.minorticks_on()
        ax3.set_title('Timeseries of Time diffs')
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Time Diffs')

        # plot frequency as a function of time
        ax4.plot(df.iloc[1:]['Time'],df.iloc[1:]['Inst Rate'], '.')
        ax4.minorticks_on()
        ax4.set_title('Timeseries of Instantaneous Frequency')
        ax4.set_xlabel('Time')
        ax4.set_ylabel('Frequency')

        fig.suptitle("Message Rate Analysis: "+ title, y=1.02)

        if savefig:
            dt_object = datetime.datetime.fromtimestamp(time.time())
            dt = dt_object.strftime('%Y-%m-%d-%H-%M-%S-%f')
            description =dt + "_"+title + "_RateAnalysis"
            fig.savefig(description + ".pdf", dpi = 100)
            fig.savefig(description + ".png", dpi = 100)

        plt.show()

    @staticmethod
    def plt_ts(df, title="", msg_axis = 'Message' , **kwargs):
        '''
        A utility function to plot a timeseries
        ''' 
        if 'Time' not in df.columns:
            print("Data frame provided is not a timeseries data.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be 'Message' ")
            raise ValueError('Time column not found')

        if msg_axis not in df.columns:
            print("Column naming convention violated.\nFor standard timeseries data, Column 1 should be 'Time' and Column 2 should be {} ".format(msg_axis))
            raise ValueError('{} column not found'.format(msg_axis))
        
        ax = None
        fig = None

        if title == "":
            title = "Timeseries plot"
        elif len(title) > 0:
            title = "Timeseries plot: " + title

        Index = df.index.strftime('%m/%d/%Y, %r')
        cb_indices = np.linspace(0, df.shape[0]-1, 15, dtype=int)
        cb =Index[cb_indices]
        cbtime = df.Time[cb_indices].values

        
        if shell_type in ['ZMQInteractiveShell', 'TerminalInteractiveShell']:
           config['interactive'] = False

        if config['interactive']:
                fig=px.scatter(df, x="Time", y=msg_axis, color ="Time", labels={"Time": "Time (s)", msg_axis:msg_axis },
                    title = title, color_continuous_scale=["black", "purple", "red"], width = 1000, height = 800)
                fig.update_layout(font_size=16,  
                    xaxis = dict(
                        tickvals = cbtime,
                        ticktext = cb,
                        tickangle = 75
                    ),
                    title={
                                'xanchor': 'center',
                                'yanchor': 'top', 
                                'y':1.0, 
                                'x':0.5,}, 
                    coloraxis_showscale=False,

                    title_font_size = 24)

                fig.update_traces(marker=dict(size=3))
        else:
            if 'ax' in kwargs:
                ax = kwargs.get('ax')
                if isinstance(ax, list) and len(ax) >1:
                    ax = ax[0]
            else:
                fig, ax = strymread.create_fig(1)
                ax = ax[0]

            im = ax.scatter(df["Time"], df[msg_axis], c=df["Time"], alpha=0.8, cmap=strymread.sunset, s=8)
            ax.set_title(title)
            ax.set_xlabel('Time (s)')

            ax.xaxis.set_ticks(cbtime)
            ax.set_xticklabels(cb, rotation = 75)
            ax.set_ylabel(msg_axis)
            ax.set_title(title)
            
        if kwargs.get('show', True):
            fig.show()

        if kwargs.get('returnfig', False):
            return fig

    @staticmethod
    def violinplot(df, title='Violin Plot'):
        '''
        A violin plot to show the data distribution
        '''
        strymread._setplots(ncols=2, nrows=1)
        plt.rcParams['figure.figsize'] = [18, 12]
        fig, axes = plt.subplots(ncols=2, nrows=1)
        ax = axes.ravel()

        sea.violinplot( ax = ax[0], y =df , orient="h")
        ax[0].set_title("Violin Plot: " + title)

        sea.boxplot(y = df, ax=ax[1])
        ax[1].set_title("Box Plot: " + title)

        plt.show()

    @staticmethod
    def temporalviolinplot(dataframe, by=30, title='Timeseries'):
        '''
        A temporal plot showing evolution of distribution as a function by time

        '''
        speed_split, split = self.split_ts(dataframe, by = by)
        import seaborn as sea
        fig, ax = strymread.create_fig(ncols=1, nrows=1)
        sea.violinplot(x="Second", y="Message", data=speed_split, ax = ax)
        ax.set_title("Temporal Violin Plot: " + title)
        plt.show()

    @staticmethod
    def timeindex(df, inplace=False):
        '''
        Convert multi Dataframe of which on column must be 'Time'  to pandas-compatible timeseries where timestamp is used to replace indices
        The convesion happens with no time zone information, i.e. all Clock time are in GMT

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
            newdf =df.copy(deep = True)

        Time = pd.to_datetime(newdf['Time'], unit='s')
        newdf.reset_index(drop=True, inplace=True)
        newdf['Clock'] = pd.DatetimeIndex(Time).tolist()
        
        if inplace:
            newdf.set_index('Clock', inplace=inplace)
        else:
            newdf = newdf.set_index('Clock')
        return newdf

    @staticmethod
    def dateparse(ts):
        '''
        Converts POSIX timestamp to human readable Datformat as per GMT

        Parameters
        -------------
        ts: `float`
            POSIX formatted timestamp 

        Returns
        ----------
        `str`
            Human-readable timestamp as per GMT
        '''
        from datetime import datetime, timezone
        # if you encounter a "year is out of range" error the timestamp
        # may be in milliseconds, try `ts /= 1000` in that case
        ts = float(ts)
        d = datetime.fromtimestamp(ts).astimezone(tz=None).strftime('%Y-%m-%d %H:%M:%S:%f')
        return d

    @staticmethod
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

    @staticmethod
    def time_shift(df1, df2, time_col1 = 'Time', time_col2='Time', msg_col1 = 'Message', msg_col2= 'Message'):
        """
        Compute the time shift specified by `time_col2` of `df2` with respect to 
        time of `df1` specified by `time_col1`. Once you get time shift you will add it to 
        time axis of second dataframe.

        Caveat: Units of time in time columns of both timeseries dataframe must be same.
        
        
        Parameters
        --------
        Parameters
        -----------
        df1: `pandas.DataFrame`
            First timeseries datframe.
        
        df2: `pandas.DataFrame`
            Second timeseries datframe.

        time_col1: `str`
            Name of time column in `df1`. Default value is "Time"

        time_col2: `str`
            Name of time column in `df2`. Default value is "Time"

        msg_col1: `str`
            Name of message column in `df1`. Default value is "Message"

        msg_col2: `str`
            Name of message column in `df2`. Default value is "Message"
            
        Returns
        --------
        `double`
            Time shift in the unit of time as used in time columns of both timeseries dataframe.
        
        """
        resample_time = np.max([np.median(np.diff(df1[time_col1])), np.median(np.diff(df1[time_col1]))])
        
        df1_re = strymread.resample(df1, rate = 1./resample_time, cont_method= 'nearest', time_col = time_col1, msg_col = msg_col1)
        df2_re = strymread.resample(df2, rate = 1./resample_time, cont_method= 'nearest',time_col = time_col2,  msg_col = msg_col2)
        
        initial_time_gap = df1_re[time_col1][0] - df2_re[time_col2][0]
        
        x = df1_re[msg_col1].values
        y = df2_re[msg_col2].values

        correlation = signal.correlate(x, y, mode="full")
        lags = signal.correlation_lags(x.size, y.size, mode="full")
        lag = lags[np.argmax(correlation)]
        
        lag_in_time_units = lag*resample_time
        
        total_time_shift = initial_time_gap + lag_in_time_units
        return total_time_shift


    @staticmethod
    def _setplots(**kwargs):
       
        ncols = 1
        nrows= 1
        if kwargs.get('ncols'):
            ncols = kwargs['ncols']

        if kwargs.get('nrows'):
            nrows = kwargs['nrows']

        if shell_type in ['ZMQInteractiveShell', 'TerminalInteractiveShell']:

            plt.style.use('default')
            plt.rcParams['figure.figsize'] = [15*ncols, 6*nrows]
            plt.rcParams['font.size'] = 22.0 + 3*(ncols-1)+ min(2*(nrows - 1), 10)
            plt.rcParams['figure.facecolor'] = '#ffffff'
            #plt.rcParams[ 'font.family'] = 'Roboto'
            #plt.rcParams['font.weight'] = 'bold'
            plt.rcParams['xtick.color'] = '#828282'
            plt.rcParams['xtick.minor.visible'] = True
            plt.rcParams['ytick.minor.visible'] = True
            plt.rcParams['xtick.labelsize'] = 14 + 2*(ncols-1)+ min(2*(nrows - 1), 10)
            plt.rcParams['ytick.labelsize'] = 14 + 2*(ncols-1)+ min(2*(nrows - 1), 10)
            plt.rcParams['ytick.color'] = '#828282'
            plt.rcParams['axes.labelcolor'] = '#000000'
            plt.rcParams['text.color'] = '#000000'
            plt.rcParams['axes.labelcolor'] = '#000000'
            plt.rcParams['grid.color'] = '#cfcfcf'
            plt.rcParams['axes.labelsize'] = 20+ 3*(ncols-1)+ min(2*(nrows - 1), 10)
            plt.rcParams['axes.titlesize'] = 25+ 3*(ncols-1)+ min(2*(nrows - 1), 10)
            #plt.rcParams['axes.labelweight'] = 'bold'
            #plt.rcParams['axes.titleweight'] = 'bold'
            plt.rcParams["figure.titlesize"] = 30.0 + 4*(ncols-1) + min(2*(nrows - 1), 10)
            #plt.rcParams["figure.titleweight"] = 'bold'

            plt.rcParams['legend.markerscale']  = 4.0 +3*(ncols-1)+ min(2*(nrows - 1), 10)
            plt.rcParams['legend.fontsize'] = 18.0 + 3*(ncols-1)+ min(2*(nrows - 1), 10)
            plt.rcParams["legend.framealpha"] = 0.5
            
        else:
            plt.style.use('default')
            plt.rcParams['figure.figsize'] = [18*ncols, 6*nrows]
            plt.rcParams['font.size'] = 12.0
            plt.rcParams['figure.facecolor'] = '#ffffff'
            #plt.rcParams[ 'font.family'] = 'Roboto'
            #plt.rcParams['font.weight'] = 'bold'
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
            #plt.rcParams['axes.labelweight'] = 'bold'
            #plt.rcParams['axes.titleweight'] = 'bold'
            plt.rcParams["figure.titlesize"] = 24.0
            #plt.rcParams["figure.titleweight"] = 'bold'
            plt.rcParams['legend.markerscale']  = 1.0
            plt.rcParams['legend.fontsize'] = 8.0
            plt.rcParams["legend.framealpha"] = 0.5
            
    @staticmethod
    def create_fig(num_of_subplots=1, **kwargs):

        nrows = num_of_subplots
        ncols = 1
        
        if kwargs.get('ncols'):
            ncols = kwargs['ncols']
        
        if kwargs.get('nrows'):
            nrows = kwargs['nrows']
        
        strymread._setplots(ncols=ncols, nrows=nrows)
        fig, ax = plt.subplots(ncols=ncols, nrows=nrows)
        

        if nrows == 1 and ncols == 1:
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
                a.ticklabel_format(useOffset=False)
        else:
            for a in ax:
                a.minorticks_on()
                a.grid(True, which='both')
                a.ticklabel_format(useOffset=False)
                
        fig.tight_layout(pad=1.0*nrows)
        return fig, ax


    @staticmethod
    def set_colorbar(fig, ax, im, label):
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        axins1 = inset_axes(ax,
                    width="50%",  # width = 50% of parent_bbox width
                    height="3%",  # height : 5%
                    loc='upper right')
        cbr = fig.colorbar(im, ax=ax, cax=axins1, orientation="horizontal")
        cbr.set_label(label, fontsize = 20)

        return cbr
