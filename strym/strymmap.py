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

import time
import numpy as np
import math
import matplotlib.pyplot as plt
plt.rcParams["figure.figsize"] = (16,8)
from scipy.interpolate import interp1d

from .phasespace import phasespace
from .strymread import strymread

from logging import Logger
from .utils import configure_logworker
LOGGER = configure_logworker()

from matplotlib import cm
import pandas as pd # Note that this is not commai Panda, but Database Pandas
import os
import sys
from subprocess import Popen, PIPE
import gmaps
from dotenv import load_dotenv
load_dotenv()
from .config import config

import IPython 
shell_type = IPython.get_ipython().__class__.__name__

if shell_type in ['ZMQInteractiveShell', 'TerminalInteractiveShell']:

    import ntpath
    import bokeh.io
    import bokeh.plotting
    import bokeh.models
    import bokeh.transform
    from bokeh.palettes import Magma256 as palette
    from bokeh.models import ColorBar
    from bokeh.io import output_notebook

    from bokeh.io.export import get_screenshot_as_png
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    from .tools import ellipse_fit
    output_notebook()

    import plotly.express as px
    import plotly.io as pio
    import plotly.offline as pyo
    # Set notebook mode to work in offline
    pyo.init_notebook_mode()

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
    
    Generating GOOGLE MAP API KEY

    You will ensure that you have right Google API KEY before you can use  `strymmap`.
    You can generate API KEY at https://console.developers.google.com/projectselector2/apis/dashboard.

    Put API KEY as an environment variable in the file ~/.env by executing following from the command line
    
    `echo "export GOOGLE_MAP_API_KEY=abcdefghijklmnopqrstuvwxyz" >> ~/.env`

    Use your own key instead of `abcdefghijklmnopqrstuvwxyz`.

    A good tutorial on how to perform API setup is given at https://web.archive.org/web/20200404070618/https://pybit.es/persistent-environment-variables.html

    Generating MAP BOX API KEY

    Generating MAP BOX API key is easier than generating, Google map API Key
    Just create an account on mapbox.com and select create token.

    You can also check tutorials on https://www.youtube.com/watch?v=6iQEhaE1bCY

    Put API Key as an environment variable in the file ~/.env by executing following from the command line

    `echo "export MAP_BOX_API=abcdefghijklmnopqrstuvwxyz" >> ~/.env`.

    Use your own key instead of `abcdefghijklmnopqrstuvwxyz`.

    
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


        # At this point, GPS data file reading is successful, set `success` to `True`
        self.success = True
        self.aq_time = strymread.dateparse(self.dataframe['Gpstime'].values[0])
        print('GPS signal first acquired at {}'.format(self.aq_time))

        self.dataframe =  strymmap.timeindex(self.dataframe, inplace=True)

        self.latitude = self.dataframe['Lat']
        self.longitude = self.dataframe['Long']
        self.altitude = self.dataframe['Alt']

        centroid_lat, centroid_long = phasespace.centroid( self.latitude,self.longitude)
        center_coordinates = (centroid_lat, centroid_long)

        coordinates = pd.DataFrame()
        coordinates['latitude'] = self.latitude
        coordinates['longitude'] = self.longitude
        self.mapfile = self.csvfile[0:-4] + '.html'
        time_axis = kwargs.get("time_axis", True)
        
        if config["map"] == "googlemap":
            
            
            self.API_Key =os.getenv('GOOGLE_MAP_API_KEY')
            
            if self.API_Key is None:
                self.API_Key = input("Enter Google MAP API Key: ")
                Popen('echo "export GOOGLE_MAP_API_KEY={}" >> ~/.env'.format(self.API_Key), shell= True)


            gmaps.configure(api_key=self.API_Key)

            styles="""
            [{ "featureType": "all", "elementType": "geometry", "stylers": [ { "color": "#b5d3ff"}]},
            { "featureType": "all", "elementType": "labels.text.fill", "stylers": [ { "gamma": 0.01}, {"lightness": 20},{"weight": "1.39"},{"color": "#0d1529"}]},
            { "featureType": "all", "elementType": "labels.text.stroke", "stylers": [ { "weight": "0.96"}, { "saturation": "9"}, { "visibility": "on"},{ "color": "#f2f2f2"}] },
            { "featureType": "all", "elementType": "labels.icon", "stylers": [ { "visibility": "off"}]},
            { "featureType": "landscape", "elementType": "geometry", "stylers": [{ "lightness": 30}, { "saturation": "9"},{ "color": "#fbfffa"}] },
            { "featureType": "poi", "elementType": "geometry", "stylers": [ { "saturation": 20 }] },
            { "featureType": "poi.park", "elementType": "geometry", "stylers": [ {"lightness": 20 }, { "saturation": -20}]},
            { "featureType": "road", "elementType": "geometry", "stylers": [ { "lightness": 10 }, { "saturation": -30 } ]},
            { "featureType": "road", "elementType": "geometry.fill", "stylers": [ { "color": "#b1c4cc"}]},
            { "featureType": "road", "elementType": "geometry.stroke", "stylers": [ { "saturation": 25}, { "lightness": 25 }, { "weight": "0.01"}]},
            { "featureType": "water", "elementType": "all", "stylers": [ { "lightness": -20 }]}
            ]
            """


            gmap_options = bokeh.models.GMapOptions(lat=centroid_lat, lng=centroid_long, 
                                map_type='roadmap', zoom=int(config["mapzoom"]), styles = styles)
            fig = bokeh.plotting.gmap(self.API_Key, gmap_options, title='Drive Route for ' + ntpath.basename(self.csvfile), 
                    width=config["mapwidth"], height=config["mapheight"], tools=['hover', 'reset', 'wheel_zoom', 'pan'])

            source = bokeh.models.ColumnDataSource(self.dataframe)

            if time_axis:
                
                mapper = bokeh.transform.linear_cmap('Gpstime', palette[:192], np.min(self.dataframe['Gpstime']), np.max(self.dataframe['Gpstime'])) 
                center = fig.circle('Long', 'Lat', size=4, alpha=1.0, 
                                color=mapper, source=source, )
                color_bar = ColorBar(color_mapper=mapper['transform'],  location=(0,0), title='Time')
                fig.add_layout(color_bar, 'right')
            else:

                fig.circle('Long', 'Lat', size=5, alpha=1.0, fill_color='red', 
                line_color = 'red', source=source)

            bokeh.plotting.output_file(filename= self.mapfile, title='Drive Router for ' + ntpath.basename(self.csvfile))
            bokeh.plotting.save(fig, self.mapfile)

            self.fig = fig

            driver = webdriver.Chrome(ChromeDriverManager().install())
            self.image = get_screenshot_as_png(fig, height=800, width=1800, driver=driver)
            time.sleep(1)
            driver.close()
            driver.quit() # See https://web.archive.org/web/20200404100708/https://sites.google.com/a/chromium.org/chromedriver/getting-started and https://web.archive.org/web/20200404101003/https://www.selenium.dev/selenium/docs/api/py/index.html
            self.image.save(self.csvfile[0:-4] + '.png',"PNG")

        elif config["map"] == "mapbox":
            self.API_Key =os.getenv('MAP_BOX_API')

            if self.API_Key is None:
                self.API_Key = input("Enter Mapbox API Key: ")
                Popen('echo "export MAP_BOX_API={}" >> ~/.env'.format(self.API_Key), shell= True)


            if time_axis:
                color = "Gpstime"
            else:
                color = None

            fig = px.scatter_mapbox(self.dataframe, lat="Lat", lon="Long", color=color,
                  color_continuous_scale=["black", "purple", "red" ], size_max=30, zoom=config["mapzoom"],
                  height = config["mapheight"], width = config["mapwidth"], #center = dict(lat = g.center)
                        title='Drive Route for ' + ntpath.basename(self.csvfile),
                       #mapbox_style="open-street-map"
                       )
            Index = self.dataframe.index.strftime('%m/%d/%Y, %r')
            cb_indices = np.linspace(0, self.dataframe.shape[0]-1, 10, dtype=int)
            cb =Index[cb_indices]
            cbtime = self.dataframe.Gpstime[cb_indices].values
            
            fig.update_layout(font_size=16,  title={'xanchor': 'center','yanchor': 'top', 'y':0.9, 'x':0.5,}, 
                    title_font_size = 24, mapbox_accesstoken=self.API_Key, mapbox_style = "mapbox://styles/strym/ckhd00st61aum19noz9h8y8kw", 
                    coloraxis_colorbar=dict(
                        title="Time",
                        tickvals=cbtime,
                        ticktext=cb,
                        ticks="outside", ticksuffix=" TIME",
                        dtick=50
                    ))
            fig.update_traces(marker=dict(size=6))
            fig.write_image(self.csvfile[0:-4] + '.png')
            fig.write_html(self.csvfile[0:-4] + '.html')

            self.fig = fig

            


    def gpsdistance(self):
        """
        Calculate the distance covered based on the Lat, Long coordinates traversed

        Returns
        ---------
        Distance covered in meters

        """

        dist =  strymmap._calcgpsdist(self.dataframe)
        return dist






    def plotroute(self, interactive=True, returnfig = False):
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

        if not self.success:
            print("There is no route to plot as GPS Data was not read successfully.")
            return None

        if interactive:
            if config["map"] == "googlemap":
                time.sleep(1)
                try:
                    bokeh.plotting.reset_output()
                    bokeh.plotting.output_notebook()
                    bokeh.plotting.show(self.fig)  # angrily yells at me about single ownership
                except:
                    bokeh.plotting.output_notebook()
                    bokeh.plotting.show(self.fig)
            elif config["map"] == "mapbox":
                self.fig.show()
        else:
            if config["map"] == "googlemap":
                display(self.image)
            elif config["map"] == "mapbox":
                from PIL import Image
                im = Image.open(self.csvfile[0:-4] + '.png')
                display(im)


        if returnfig:
            return self.fig


    @staticmethod
    def _calcgpsdist(df, sample_time = 0.1):

        distance = 0.0

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

        return distance


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
