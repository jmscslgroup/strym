#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: May 2, 2020
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


import sys, getopt
import os
import math
import matplotlib.pyplot as plt
import seaborn as sea
import pandas as pd
import numpy as np
from .strymread import ts_sync
from .strymread import create_fig
from .strymread import centroid

class phasespace:
    '''
    `phasespace` provides an interface  for phase-space analysis, plots phase space diagram and performs
    other analysis

    Attributes
    ----------------
    df: `pandas.DataFrame`
        Data for phase-space. There are three columns to the dataframe: "Time", "X", "Y".

    centroid: `tuple`
        Two-element tuple (C_x,C_y) that is centroid of the cluster given by `df`.

    distance: `numpy.array`
        Numpy array to save distance of all points from the cluster's centroid.

    acd: `float`
        Average Centroid Distance of a cluster.

    Parameters
    ----------------

    dfx: `pandas.DataFrame`
        First timeseries dataframe for x-axis on phase-space diagram. First column should be "Time" and 
        second column should be "Message"

    dfy: `pandas.DataFrame`
        Second timeseries dataframe for x-axis on phase-space diagram. First column should be "Time" and 
        second column should be "Message"

    resample_type: `str`, `double`
        Specify how to resampling should be done in case `dfx` and `dfy` don't have same sampling rate.
        
        `str`: resample_type can either be "first" or "second, if specified as string.  If rate="first", then dfy 
        will be resampled by inheriting time points from dfx.  If rate="first", then `dfx` will be resampled by 
        inheriting time points from `dfy`. 

        `double`: Alternatively, user can specify desired sampling rate with which `dfx` and `dfy` will be
        resampled.
        
        If `dfx` and `dfy` do not have same end and start time, then they will be truncated to match start
        and end time.
        
    kwargs: variable list of argument in the dictionary format

    '''
    def __init__(self, dfx, dfy, resample_type, **kwargs):
        
        self.verbose = True
        
        try:
            self.verbose = kwargs["verbose"]
        except KeyError as e:
            pass

        if np.all(dfx['Time'].values  ==dfy['Time'].values):
            if self.verbose:
                print("No resampling is required as time points of both dataframe are identical")
        else:
            dfx, dfy = ts_sync(df1=dfx, df2=dfy, rate=resample_type)

        df = dfx.copy(deep=True)
        
        df.rename(columns={"Message": "X"}, inplace = True)

        df["Y"] = dfy["Message"]

        self.df = df
        
        self.cluster()

    def phaseplot(self, title="Phase-space plot", xlabel='Timeseries 1', ylabel='Timeseries 2'):
        '''
        `phasepolot` creates phase-space diagram with temporal informatiom embedded as colormap.

        Parameters
        ---------------
        title: `str`, default="Phase-space plot"
            Specifes title of the phase-space diagram

        '''
        fig, ax = create_fig(1)
        ax = ax[0]
        c = self.df['Time'] # for colormap
        im = ax.scatter(self.df["X"], self.df["Y"], c=self.df["Time"], alpha=0.8, cmap="magma")
        ax.set_title(title)
        cbr = fig.colorbar(im, ax=ax)
        cbr.set_label("Time")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.show()
        return fig, ax

    def cluster(self):
        '''
        `cluster` calculates centroid of the cluster, and distance of all points from the centroid and stores as a distance vector.
        '''
        X = self.df['X'].values
        Y = self.df['Y'].values

        assert (len(X) == len(Y)), ("length of X-vector and Y-vector are not same")
        C_x, C_y = centroid(X, Y)

        self.centroid = (C_x, C_y)

        distance = np.empty((0,1), float)
        for index in range(0, len(X)):
            if math.isnan(X[index]) or math.isnan(Y[index]):
                continue
            dist = np.square((C_x - X[index])**2.0 + (C_y - Y[index])**2.0)
            distance = np.append(distance, dist)

        self.distance = distance
        self.acd = np.mean(distance)


    def centroidplot(self, title="Density of cluster distance from its centroid",  xlabel='Centroid Distance', ylabel='Counts'):
        '''
        `cetroidplot` visualizes the distribution of distance of each point in the cluster from its centroid.

        Parameters
        ---------------
        title: `str`, default="Density of cluster distance from its centroid"
            Specifes title of the centroidplot
        
        '''
        fig, ax = create_fig(1)
        ax = ax[0]
        
        sea.set_style("white")
        plt.grid()
        sea.set_palette("deep")
        bins =20

        #sea.distplot(distance, hist=True, kde=True,  bins=bins)
        plt.hist(self.distance, color = '#2dbdac', edgecolor = '#1c6878', bins=bins)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)   
        plt.show()
        return fig, ax