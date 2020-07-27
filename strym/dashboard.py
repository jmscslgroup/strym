#!/usr/bin/env python
# 
# Author: Jonathan Sprinkle
# Copyright (c) 2020 Arizona Board of Regents
# About: Works within the strym package to collect metadata files 
#   from within a folder and print interesting aspects of the collection
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

import json
import sys

class dashboard:
    
    """
    `dashboard` works within the strym package to collect metadata files 
    from within a folder and print interesting aspects of the collection
    
    Parameters
    --------------
    directory: `str`
        Reads from the specified directory

    verbose: `bool`
        Boolean flag, if `True` verbosity is enabled

    kwargs: variable list of argument in the dictionary format
    

    Attributes
    --------------

    directory: `str`
        Reads from the specified directory

    verbose: `bool`
        Boolean flag, if `True` verbosity is enabled

    metadata_dict: `dict`
        Metadata dictionary

    jsonlist: `list`
        A list contain json data

    """

    def __init__(self,directory='./',verbose=False,start=None,end=None,**kwargs):
        self.directory = directory
        self.verbose = verbose
        self.start=start
        self.end=end
#         print(self.directory)
        # process all the input folders first
    
#         parentfolder = "/Users/sprinkle/work/data/cyverse/rahulbhadani/JmscslgroupData/PandaData/"
        import glob
        folderlist = glob.glob(self.directory+"*")

        if verbose:
            print(folderlist)
        jsonlist = []
        for datafolder in folderlist:
        #     datafolder = "/Users/sprinkle/work/data/cyverse/rahulbhadani/JmscslgroupData/PandaData/2020_03_03/"
            import glob
            jsonlisttmp = glob.glob(datafolder+"/*.json")
            if verbose:
                print(jsonlisttmp)
            if len(jsonlisttmp) > 0:
                for f in jsonlisttmp:
                    jsonlist.append(f)
        if verbose:
            print(jsonlist)
        metadata_dict = []

        for json_file_str in jsonlist:
            try:
                with open(json_file_str) as json_file:
                    data = json.load(json_file)
                    metadata_dict.append(data)
            except Exception as ex:
#                 if verbose:
                    print(f'Skipping {json_file_str}, continuing (ex={ex})')
                
        self.metadata_dict = metadata_dict
        self.jsonlist = jsonlist
    
    def statistics(self):
        """
        Retrieves interesting statistics

        Returns
        ----------

        `str` :
            String formatted JSON

        """
        result=''
        result += f'Metadata entries: {len(self.metadata_dict)}\n'
        result += f'JSON files found: {len(self.jsonlist)}\n'
        return result
    
    def miles(self):
        """
        Retrieves distance traveled in miles

        Returns
        ----------

        `float` :
            Total distance travelled in miles

        """
        dist=0
        self.error_count=0
        for d in self.metadata_dict:
            try:
                dist = dist + d['distance_miles']
            except Exception as ex:
                self.error_count += 1
                if self.verbose:
                    print(f'No key distance_miles in dictionary, skipping')
        return dist

    def kilometers(self):
        """
        Retrieves distance traveled in Kilometers

        Returns
        ----------

        `float` :
            Total distance travelled in Kilometers

        """
        dist=0
        self.error_count=0
        for d in self.metadata_dict:
            try:
                dist = dist + d['distance_km']
            except Exception as ex:
                self.error_count += 1
                if self.verbose:
                    print(f'No key distance_kilometers in dictionary, skipping')
        return dist


    def main(argv):
        
        import os, getopt
        directory = './'
        verbose = False
        try:
            opts, args = getopt.getopt(argv,"hvd:s:e:",["directory="])
        except getopt.GetoptError:
            print('dashboard.py <-v,--verbose> -d <directory> -s <start_date> -e <end_date>')
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print('dashboard.py <-v,--verbose> -d <directory>')
                sys.exit()
            elif opt in ('-d', '--directory'):
                directory = arg
                print(f'directory={directory}')
            elif opt in ('-s', '--start-date'):
                import datetime
                start = datetime.fromisoformat(arg)
                print(f'start_date={start}')
            elif opt in ('-e', '--end-date'):
                import datetime
                end = datetime.fromisoformat(arg)
                print(f'end_date={end}')
            elif opt in ('-v', '--verbose'):
                verbose = True
                print(f'verbose={verbose}')


        from strym import dashboard
        try:
            db = dashboard(directory=directory,verbose=verbose)
            print(db.statistics())
            print(f'Total driving distance (miles): {db.miles()} ({db.error_count} files not parsed)')    
            print(f'Total driving distance (km): {db.kilometers()} ({db.error_count} files not parsed)')

        except Exception as ex:
            print(f'Exception when processing {directory} (msg={ex})')

            
            
        # find all the JSON files in this directory
#         parentfolder = "/Users/sprinkle/work/data/cyverse/rahulbhadani/JmscslgroupData/PandaData/"
#         import glob
#         folderlist = glob.glob(parentfolder+"*")
#         print(folderlist)
#         jsonlist = []
#         for datafolder in folderlist:
#         #     datafolder = "/Users/sprinkle/work/data/cyverse/rahulbhadani/JmscslgroupData/PandaData/2020_03_03/"
#             import glob
#             jsonlisttmp = glob.glob(datafolder+"/*.json")
#             print(jsonlisttmp)
#             if len(jsonlisttmp) > 0:
#                 for f in jsonlisttmp:
#                     jsonlist.append(f)

#         print(jsonlist)
#         metadata_dict = []

#         for json_file_str in jsonlist:
#             try:
#                 with open(json_file_str) as json_file:
#                     data = json.load(json_file)
#                     metadata_dict.append(data)
#             except Exception as ex:
#                 print(f'Skipping {json_file_str}, continuing (ex={ex})')

#         dist=0
#         for d in metadata_dict:
#             try:
#                 dist = dist + d['distance_miles']
#             except Exception as ex:
#                 print(f'No key distance_miles in dictionary, skipping')
#         print(dist)


            
    
    if __name__ == "__main__":
        main(sys.argv[1:])