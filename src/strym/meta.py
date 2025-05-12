#!/usr/bin/env python
# 
# Author: Jonathan Sprinkle
# Copyright (c) 2020 Arizona Board of Regents
# About: Works within the strym package to extract metadata from drives that are
#   recorded using libpanda, with optional corresponding dashcam video
# License: MIT License
# 
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

__author__ = 'Jonathan Sprinkle'
__email__  = 'sprinkjm@arizona.edu'

import strym
from .strymread import strymread
import math
import time
# import matplotlib.pyplot as plt
import numpy as np
import scipy.integrate as integrate
import sys
import os
import glob
import vin_parser as vp

class meta:
    """
    `meta` Works within the strym package to extract metadata from drives that are recorded using libpanda, with optional corresponding dashcam video

    Parameters
    -------------
    folder: `str`
        Folder to retrieves files from

    csvfile: `str`
        Datafiles

    dbcfile: `str`
        The DBC file which will provide codec for decoding CAN messages

    recursive: `bool`
        If `True`, look for csvfiles recursively in the folder `folder`

    kwargs: variable list of argument in the dictionary format


    """

    def __init__(self,folder='',csvfile='',dbcfile='',recursive=False,**kwargs):
        
        # set the csv file based on what we got; if empty, we're probably going to 
        # be doing what's in the passed in folder
        self.csvfile = csvfile
        
        # set the dbcfile to be what is passed in; 
        # if empty we will choose later
        # if multiple, we will look for one that matches our sensibilities
        self.dbcfile = dbcfile
#         print(f'dbcfile={self.dbcfile}')
        dbcdict = meta.dbcDictionary(self.dbcfile)
#         print(f'dbcdict={dbcdict}')
        
        self.drive = { 'filepath': self.csvfile, 
                      'filename': os.path.basename(self.csvfile) }
        print(f'Reading {self.csvfile}')
        
        try:
            vin = meta.vin(self.csvfile)
            self.drive['vin'] = vin
            makeStr=''
            wmiStr=''
#             import vin_parser as vp
#             print('vp omg')
            try:
                if vp.check_valid(vin) == True:
                    makeStr = vp.manuf(vin)
                    wmiStr = vp.wmi(vin)
                    self.drive['make'] = makeStr
            except:
                print('No valid vin..continuing as Toyota')
            
            dbc=None
            if len(wmiStr) > 0:
                dbc = dbcdict[wmiStr]
            # check to confirm that the dbc files match
            else:
                print('Error finding correct dbcfile, will use Toyota Version')
                dbc = dbcdict['2T3']
                    
#             print(f'dbc={dbc}')
            self.r0 = strymread(self.csvfile, dbc)

            self.drive['date'] = time.ctime(self.r0.dataframe["Time"][0])

            duration1 = self.r0.dataframe['Time'][len(self.r0.dataframe)-1] - self.r0.dataframe['Time'][0]
            duration_str = f'  Duration of this drive is {duration1} seconds ({math.trunc(int(duration1*1000)/(1000*60))} minutes {math.trunc(duration1 % 60)} seconds).'
            start_str = f'  Starting date/time of the drive is {time.ctime(self.r0.dataframe["Time"][0])}'

            # get the speed timeseries information from the data file
            speed_ts = self.r0.speed()
            # turn the timeseries into a python array for integration
            # transform from km/hr by multiplying 1000m/1km and 1 hr/3600s to get m/s
            speed_ar = np.array(speed_ts['Message'])*1000/3600
        #     speed_ar[0:-1]*1000/3600
            # find the difference of the time values
        #     dt = np.diff(np.array(speed_ts['Time']))
            dt = np.diff(speed_ts['Time'])
            # trapezoidal integration, divide by 1000 to get total km (rather than m)
            # Commented out: this produces negative values that don't make sense
        #     km_ts = np.trapz(y=speed_ar[0:-1],x=dt)/1000
            km_ts = np.trapz(y=speed_ar,x=np.array(speed_ts['Time']))/1000
            # commented out: this produces incorrect values that seem to be off by a factor of around 2, depending
            km_dx = np.trapz(y=speed_ar,dx=0.02)/1000
            # need to convert km/hr to km/s to get km later when integrating
            distance_str = f'  The trip was {km_ts} km ({km_ts*3.1/5} miles)'
        #     distance_str_dx f'  The dx version is {km_dx} km ({km_dx*3.1/5} miles)'

            #speed_ts['Time']
            #f'Total miles driven is {km_ts}'
        #     print(duration_str)
        #     print(start_str)
        #     print(distance_str)
        #     print('')
#             self.drive = { 'filepath': self.csvfile, 'filename': os.path.basename(self.csvfile), 'distance_km': km_ts, 'distance_miles': km_ts*3.1/5, 'duration_s': duration1, 
#                      'date': time.ctime(self.r0.dataframe["Time"][0]) }
            self.drive['distance_km'] = km_ts
            self.drive['distance_miles'] = km_ts*3.1/5
            self.drive['duration_s'] = duration1

        except Exception as ex:
            errString = f'Error processing {self.csvfile} with {self.dbcfile}, leaving note in drive (msg={ex}).'
            self.drive['error'] = errString
        
    def toJSON(self):

        """
        Returns dictionary-formatted driving meta-data

        """


        return self.drive
    
    
    @staticmethod
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
    
#     # returns the vehicle make, to help with DBC file selection
#     @staticmethod
#     def make(vin):
#         import vin_parser as vp
#         result = vp.manuf(vin)
#         return result
        
#     @staticmethod
#     def wmi(vin):
#         import vin_parser as vp
#         result = vp.wmi(vin)
#         return result

    
    @staticmethod
    # the key is the wmi, the value is the dbc file to use
    def dbcDictionary(dbcfiles):
        """

        """
        # example vins from Vehicles we know we have
        result = {"2T3": None, "5FN" : None}
        for dbc in dbcfiles:
            if dbc.find('oyota') >= 0:
                result['2T3'] = dbc
            elif dbc.find('onda') >= 0:
                result['5FN'] = dbc
        return result
    
    @staticmethod
    def usage():
        return 'meta.py -c <canCSVfile> -d <dbcfile> -o <outputJSONfile>'
    
    def write(self,outputfile=''):
        """
        Writes the JSON file in `outputfile`

        Parameters
        -------------
        outputfile: `str`
            The name of the outputfile where to write JSON formatted metadata

        Returns
        ---------
        `str`
            The name of the JSON output file.
            
        """
        import json
        import os
        import datetime

        # drive_i = metadata[215]
        self.drive["metadata_date"] = datetime.datetime.now().astimezone().strftime('%a %b %d %H:%M:%S %Y %Z')

        if outputfile=='':
            # find the name attached to this filename
            file_path = os.path.splitext(self.drive["filepath"])[0]
            index = file_path.find("CAN")
            outputfile = f'{file_path[0:index]}_metadata.json'

        print(outputfile)
        with open(outputfile,'w') as outfile:
            json.dump(self.drive,outfile,indent=4)
        return outputfile
    
    def main(argv):
        import os, getopt
        csvfile = ''
        dbcfile = []
        outputfile = ''
        print(f'argv={argv}')
        try:
            opts, args = getopt.getopt(argv,"hc:d:o:",["canCSVfile=","dbcfile=","outputJSONfile="])
        except getopt.GetoptError:
            print(meta.usage())
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print(meta.usage())
                sys.exit()
            elif opt in ('-c', '--canCSVfile'):
                csvfile = arg
                print('csvfile')
            elif opt in ("-d", "--dbcfile"):
                dbcfile.append(arg)
                print('dbcfile')
            elif opt in ("-o", "--outputJSONfile"):
                outputfile = arg
                print('outputfile')

#         print(f"Input CSV file of CAN Messages is {csvfile}")
#         print(f"Input DBC file of is {dbcfile}")
#         print(f"Output file is {outputfile}")
        from strym import meta
        try:
            meta1 = meta(csvfile=csvfile,dbcfile=dbcfile)
            meta1.write(outputfile)    
        except:
            print(f'Exception when processing {csvfile}, still going to try to write {outputfile}')
            meta1.write(outputfile)

    if __name__ == "__main__":
        main(sys.argv[1:])