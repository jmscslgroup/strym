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
from .strymread import strymread
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

class phasespace:
    '''
    `phasespace` provides an interface  for phase-space analysis, plots phase space diagram and performs
    other analysis

    Attributes
    ----------------
    df: `pandas.DataFrame`
        Data for phase-space. There are three columns to the dataframe: "Time", "X", "Y".

    centroidxy: `tuple`
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
    def __init__(self, dfx, dfy, resample_type = "first", **kwargs):
        self.verbose = kwargs.get("verbose", True)
        if np.all(dfx['Time'].values  ==dfy['Time'].values):
            if self.verbose:
                print("No resampling is required as time points of both dataframe are identical")
        else:
            dfx, dfy = strymread.ts_sync(df1=dfx, df2=dfy, rate=resample_type)

        df = dfx.copy(deep=True)
        
        df.rename(columns={"Message": "X"}, inplace = True)

        df["Y"] = dfy["Message"]

        self.df = df
        
        self.cluster()

    @property
    def theta(self):
        
        return np.arctan( (self.df['Y'] - self.centroidxy[1]) /(self.df['X'] - self.centroidxy[0]))

    def phaseplot(self, title="Phase-space plot", xlabel='Timeseries 1', ylabel='Timeseries 2', plot_each=False, **kwargs):
        '''
        `phasepolot` creates phase-space diagram with temporal informatiom embedded as colormap.

        Parameters
        ---------------
        title: `str`, default="Phase-space plot"
            Specifes title of the phase-space diagram

        Returns
        ----------

        ax
            Axes object of the plot drawn

        '''
        
        if not plot_each:
            
            fig = None
            ax = None

            if 'fig' in kwargs:
                fig = kwargs.get('fig')

            if 'ax' in kwargs:
                ax = kwargs.get('ax')
                if len(ax) >1:
                    ax = ax[0]
            else:
                fig, ax = strymread.create_fig(1)
                ax = ax[0]

            im = ax.scatter(self.df["X"], self.df["Y"], c=self.df["Time"], alpha=0.8, cmap=strymread.sunset, s = 2)
            ax.set_title(title)
            cbr= strymread.set_colorbar(fig = fig, ax = ax, im = im, label = "Time")
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            plt.show()
            return ax

        else:
            fig = None
            ax = None
            if 'fig' in kwargs:
                fig = kwargs.get('fig')

            if 'ax' in kwargs:
                ax = kwargs.get('ax')

                if isinstance(ax, list) and len(ax) < 3:
                    print("ERROR: Insufficient number of axes for the current call.")
                    return ax
            else:
                fig, ax = strymread.create_fig(ncols = 3)

            im = ax[2].scatter(self.df["X"], self.df["Y"], c=self.df["Time"], alpha=0.8, cmap=strymread.sunset)
            ax[2].set_title(title)
            
            # axins1 = inset_axes(ax[2],
            #         width="50%",  # width = 50% of parent_bbox width
            #         height="3%",  # height : 5%
            #         loc='upper right')
            # cbr = fig.colorbar(im, ax=ax[2], cax=axins1, orientation="horizontal")
            # cbr.set_label("Time", fontsize = 20)

            cbr= strymread.set_colorbar(fig = fig, ax = ax[2], im = im, label = "Time")
            cbr.set_ticks([])
            ax[2].set_xlabel(xlabel)
            ax[2].set_ylabel(ylabel)

            bottom, top = ax[2].get_ylim()  # return the current ylim
            ax[2].set_ylim(bottom*0.8 - 1.0, top*1.2 + 1.0)   # set the ylim to bottom, top
            left, right = ax[2].get_xlim()  # return the current xlim
            ax[2].set_xlim(left*0.8 - 1.0, right*1.2 + 1.0)   # set the xlim to left, right
            

            im = ax[0].scatter(self.df["Time"], self.df["X"], c=self.df["Time"], alpha=0.8, cmap=strymread.sunset)
            ax[0].set_xlabel("Time")
            ax[0].set_ylabel(xlabel)
            ax[0].set_title(xlabel)
            
            im = ax[1].scatter(self.df["Time"], self.df["Y"], c=self.df["Time"], alpha=0.8, cmap=strymread.sunset)
            ax[1].set_xlabel("Time")
            ax[1].set_ylabel(ylabel)
            ax[1].set_title(ylabel)

            if kwargs.get('show', True):
                plt.show()

            return fig, ax

    def cluster(self):
        '''
        `cluster` calculates centroid of the cluster, and distance of all points from the centroid and stores as a distance vector.
        '''
        X = self.df['X'].values
        Y = self.df['Y'].values

        assert (len(X) == len(Y)), ("length of X-vector and Y-vector are not same")
        C_x, C_y = phasespace.centroid(X, Y)

        self.centroidxy = (C_x, C_y)

        distance = np.empty((0,1), float)
        for index in range(0, len(X)):
            if math.isnan(X[index]) or math.isnan(Y[index]):
                continue
            dist = np.square((C_x - X[index])**2.0 + (C_y - Y[index])**2.0)
            distance = np.append(distance, dist)

        self.distance = distance
        self.acd = np.mean(distance)

    def centroidplot(self, title="Density of cluster distance from its centroid",  xlabel='Centroid Distance', ylabel='Counts', **kwargs):
        '''
        `cetroidplot` visualizes the distribution of distance of each point in the cluster from its centroid.

        Parameters
        ---------------
        title: `str`, default="Density of cluster distance from its centroid"
            Specifes title of the centroidplot
        
        '''
        ax = None
        
        if 'ax' in kwargs:
            ax = kwargs.get('ax')
            if isinstance(ax, list) and len(ax) >1:
                ax = ax[0]
        else:
            _, ax = strymread.create_fig(1)
            ax = ax[0]

        sea.set_style("white")
        sea.set_palette("deep")
        bins =20

        #sea.distplot(distance, hist=True, kde=True,  bins=bins)
        ax.hist(self.distance, color = '#2dbdac', edgecolor = '#1c6878', bins=bins)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)  
        if kwargs.get('show', True):
            plt.show()
        return ax

    @staticmethod
    def centroid(X, Y):
        '''
        Calculates the centroid of a phase-space cluster specified by `X` and `Y` Vectors
        
        Parameters
        ----------
        X: `pandas.core.series.Series`
            X-coordinate on phase-space 
        Y: `pandas.core.series.Series`
            Y-coordinate on phase-space
            
        Returns
        --------
        `float, float`
            Centroid of the phase space cluster specified by `X` and `Y` Vectors
        '''
        
        C_x = np.sum(X)/len(X)
        C_y = np.sum(Y)/len(Y)
        
        return C_x, C_y


    @staticmethod
    def AWCSS(X, Y):
        '''
        Calculates the average distance of phase-space cluster specified by `X` and `Y` Vectors from its centroid
        
        Parameters
        ----------
        X: `pandas.core.series.Series`
            X-coordinate on phase-space 
        Y: `pandas.core.series.Series`
            Y-coordinate on phase-space
            
        Returns
        --------
        `float`
            Average within the cluster distance from centroid
        '''
        
        assert (len(X) == len(Y)), ("length of X-vector and Y-vector are not same")
        C_x, C_y = phasespace.centroid(X, Y)
        sum = 0.0
        for index in range(0, len(X)):
            if math.isnan(X.iloc[index]) or math.isnan(Y.iloc[index]):
                continue
            dist = np.square((C_x - X.iloc[index])**2.0 + (C_y - Y.iloc[index])**2.0)
            sum = sum + dist
        avg = sum/len(X)
        return avg