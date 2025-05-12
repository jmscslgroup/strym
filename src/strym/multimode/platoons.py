#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Apr 2, 2020
# About: Contains a class to find files that are overlapping in time and space
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

from logging import Logger
import os
import ntpath
import glob
import gc
import numpy as np
from pathlib import Path
import math
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import euclidean_distances
import pandas as pd

from ..utils import configure_logworker
LOGGER = configure_logworker()

from ..strymmap import strymmap
from .. strymread import strymread

class  platoons:
    def __init__(self, folders, **kwargs):
        """
        `platoons finds one or more files that overlapping in time and space based on timestamp and GPS  location.
        This function is helpful to identify a subset of strym data 


        Parameters
        -------------

        folders:  `list`
            A list of folder that contains data files captured using libpanda and comma.ai Panda black/grey panda devices

        
        Attributes
        ------------
        
        success: `bool`
            This flag tells of call to `platoons` was able to successfully instantiate a platoon object
            
        CAN_files: `list`
            list of CAN data files found from the folder
        
        GPS fileS: `list`
            list of GPS data files found from the folder
        
        
        
        
        """
        self.success = False

        self.CAN_files = None
        self.GPS_files = None
        
        # Check if the folder exists and is not empty

        if isinstance(folders, str):
            
            folders = [folders]
        
        isDIR = []
        valid_folders = []
        for f in folders:
            isDirectory = os.path.isdir(f)
            if not isDirectory:
                LOGGER.warn("{} is not a directory, we will skip it.".format(f))
            else:
                valid_folders.append(f)
            isDIR.append(isDirectory)


        if  ~np.any(isDIR):
            del isDIR
            gc.collect()
            LOGGER.error("None of the directory in the provided list of folders is valid.")
            return

        CAN_files = []
        for f in valid_folders:
            for path in Path(f).rglob('*CAN*.csv'):
                if os.path.getsize(str(path)) < 60:
                    LOGGER.debug("Nothing significant to read in {}. Not adding to the list of CAN data files for route matching.".format(str(path)))
                    continue
                    
                CAN_files.append(str(path))

        GPS_files = []
        for f in valid_folders:
            for path in Path(f).rglob('*GPS*.csv'):
                if os.path.getsize(str(path)) < 60:
                    LOGGER.debug("Nothing significant to read in {}. Not adding to the list of GPS data files for route matching.".format(str(path)))
                    continue
                GPS_files.append(str(path))
        
        self.CAN_files = CAN_files
        self.GPS_files = GPS_files

        del CAN_files
        del GPS_files
        gc.collect()

    def spatial_finder(self, seedfile, space_eps = 0.0001, max_overlap_distance = 200, gps_fragmentation = 10, min_seed_distance= 200, **kwargs):
        """
        `spatial_finder` finds the two or more datasets that have been collected in nearly same geographical location

        Parameters
        -------------
        seedfile: `str`
            The GPS file from Panda Black/Gray that will act as a seed file for finding spatially similar files        

        space_eps: `float`

        max_overlap_distance: `double`
            Maximum distanced overlapped between seed route and target routes

        gps_fragmentation: `double`
            Gps fragmentation factor that determins when to this if routes should be fragment based on (i) either missing GPS signal (ii) there is a loop in route (iii) Route has traced same points multiple times
        
        """

        map_obj = []
        for gps in self.GPS_files:
            g = strymmap(csvfile= gps)
            if not g.success:
                continue
            map_obj.append(g)

        seedroute = strymmap(csvfile=seedfile)
        if not seedroute.success:
            LOGGER.error("Seed file reading was not successful. Please provide a valid GPS data file as seed.")
            return {}

        if seedroute.gpsdistance() < min_seed_distance:
            LOGGER.info("Not finding common routes as seed route has distance traveled less 200 m. Returning empty dictionary.")
            return {}


        common_route_dictionary = {}

        for i, track in enumerate(map_obj):
            LOGGER.info("Seed file is {}".format(seedroute.csvfile))
            LOGGER.info("Target file is {}".format(track.csvfile))
            if track.csvfile == seedroute.csvfile:
                continue

            T1 = seedroute.dataframe[['Long', 'Lat']].values
            T2 = track.dataframe[['Long', 'Lat']].values
            
            # Calculate the pairwise distance between  T1 and T2
            W = euclidean_distances(T1, T2)
            WMATE = pd.DataFrame(W)

            # Retrieve segments from pairwise distance for which distance is less than `space_eps`
            WMAT = WMATE[WMATE < space_eps]
            WV = WMAT.values
            jk = np.argwhere(~np.isnan(WV))
            x_1 = [i[0] for i in jk]
            x_2 = [i[1] for i in jk]
            x_1 = list(set(x_1))
            x_2 = list(set(x_2))

            # see if x_2 is fragmented
            discont = np.argwhere(np.diff(x_2) > gps_fragmentation)
            discont = np.insert(discont, 0, 0)
            x2list = []
            for i in range(1, len(discont)):
                x2list.append(x_2[discont[i-1]+1:discont[i]])

            common_1 = seedroute.dataframe.iloc[x_1]


            common_2list = []
            for x2l in x2list:
                common_2 = track.dataframe.iloc[x2l]
                common_2 = common_2.sort_values(by=['Gpstime'])
                common_2list.append(common_2)
            
            
            for count, common_2 in enumerate(common_2list):

                dist2 = strymmap._calcgpsdist(common_2)
                LOGGER.info("Common route distance is {}".format(dist2))

                # Only saving route if total distance in common route of target is max_overlap_distance m
                if dist2 > max_overlap_distance:
                    LOGGER.info("Saving route because total distance traveled by target route is max_overlap_distance meters and common route has been found.")
                    # dbscan = DBSCAN(algorithm='brute', min_samples =10, eps = 0.001, metric = 'euclidean' )
                    # cluster_labels = dbscan.fit_predict(common_2[["Long", "Lat"]].values)
                    # print("Labels = {}".format(set(cluster_labels)))
                    # common_2['label'] = cluster_labels
                    # route_partition = []

                    # if len(cluster_labels) > 1:
                    #     route_partition = []
                    #     for l in set(cluster_labels):
                    #         df_l = common_2[common_2['label'] == l]
                    #         df_l = df_l.sort_values(by=['Gpstime'])
                    #         route_partition.append(df_l)

                    # else:
                    #     route_partition.append(common_2)
                    
                    
                    #for count, partition in enumerate(route_partition):
                    #dist =  strymmap._calcgpsdist(partition)
                    common_route_dictionary['{}/{}'.format(count,ntpath.basename(track.csvfile))] = {}
                    common_route_dictionary['{}/{}'.format(count,ntpath.basename(track.csvfile))]['file_name'] = track.csvfile
                    common_route_dictionary['{}/{}'.format(count,ntpath.basename(track.csvfile))] ["start_time"] = common_2['Gpstime'].iloc[0]
                    common_route_dictionary['{}/{}'.format(count,ntpath.basename(track.csvfile))] ["end_time"] = common_2['Gpstime'].iloc[-1]
                    common_route_dictionary['{}/{}'.format(count,ntpath.basename(track.csvfile))] ["common_route_distance"] = dist2


                    if (kwargs.get("plot", False)):
                        fig, ax = strymread.create_fig(1)
                        ax[0].plot(seedroute.dataframe['Long'],seedroute.dataframe['Lat'], linewidth = 0,markersize = 8, marker = 'D', alpha=1.0, label = 'Seed Route - Complete', color = "green")
                        ax[0].plot(track.dataframe['Long'],track.dataframe['Lat'], linewidth = 0, markersize = 6, marker = 'D', alpha=1.0, label = 'Target Route - Complete', color = "blue")
                        ax[0].plot(common_1['Long'], common_1['Lat'], linewidth = 0, markersize = 4, marker = 'o', alpha=.8, label = 'Seed Route - Common',color = "orange")
                        ax[0].plot(common_2['Long'],common_2['Lat'], linewidth = 0, markersize = 2, marker = 'o', alpha=.7 , label = 'Target Route - Common', color = "black")
                        ax[0].set_title(ntpath.basename(track.csvfile))
                        fig.legend(loc = 'center right', fontsize = 12)
                        fig.show()

                    else:
                        LOGGER.info("Not  adding route fragment to dictionary being returned as it is less than specified max overlap distance of {} meter.".format(max_overlap_distance))

        return common_route_dictionary

        
    @staticmethod
    def spatial_similarity(p1, p2, space_eps = 0.0001):
        """
        Calculates spatial similarity between two points.

        Parameters
        --------------
        p1: `tuple`
            (Longitude, Latitutde) pair representing the first point
        
        p2: `tuple`
            (Longitude, Latitutde) pair representing the second point

        space_eps: `float`
            A parameter specifying the maximum allowable distance for two points p1, and p2 to match
        """

        phi_1 = p1[1]*math.pi/180.0 # in radians
        phi_2 = p2[1]*math.pi/180.0 # in radians
        delta_phi = phi_1 - phi_2
        lamda_1 = p1[0]
        lamda_2 = p2[0]

        delta_lambda  = (lamda_1 - lamda_2 )*math.pi/180.0

        R = 6371000 # Earthe radius in meter

        a = (math.sin(delta_phi/2))**2 + math.cos(phi_1)*math.cos(phi_2)*math.sin(delta_lambda/2)*math.sin(delta_lambda/2)

        c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
        great_circle_distance = R*c # in meters

        similarity_score = 0
        if great_circle_distance > space_eps:
            similarity_score = 0
        else:
            similarity_score = 1 - great_circle_distance/space_eps

        return similarity_score


    @staticmethod
    def score_LCS(T1, T2):
        """
        A recursive algorithm to find a longest common subsequence
        given a (long, lat) sequence of two trajectories T1 and T2

        Parameters
        --------------
        T1: `np.array`
            A numpy array with two columns (Long, Lat) representing  the first trajectory

        T2: `np.array`
            A numpy array with two columns (Long, Lat) representing the second trajectory
        """
        n = T1.shape[0]
        m = T2.shape[0]
        if n == 0 or m == 0:
            return 0

        s1 = platoons.score_LCS(T1[:-1], T2[:-1]) + platoons.spatial_similarity(T1[-1], T2[-1])
        s2 = platoons.score_LCS(T1, T2[:-1])
        s3 = platoons.score_LCS(T1[:-1], T2)

        return np.max([s1, s2, s3])
        

        