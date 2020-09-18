#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Set 11, 2020
# About: This provides some function tools that implement algorithms for CAN data analysis at aggregate level

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
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from .strymread import strymread
import seaborn as sea
from .phasespace import phasespace
import datetime
import time

def acd(strymobj, window_size=30, plot_iteration = False, plot_timespace = True, save_timespace = False, wave_threshold = 50.0):
    """
    Average Centroid Distance Algorithm for calculating stop-and-go wavestrength from 

    `acd` implements average centroid distance algorithm to find out the stop-and-go distance traveled based on the given
    threshold.

    Parameters
    -------------

    strymobj: `strymread`
        A valid stymread object

    window_size: `int`
        Window size over which to form the cluster of data points on speed-acceleration phasespace

    plot_iteration: `bool`
        If `True` plots the intermediate phase-space plots of speed-acceleration phasespace for the `window_size` and distribution of centroid distances

    plot_timespace: `bool`
        If `True` plots and save timespace diagram of wavestrength for the given drive.

    wave_threshold: `double`
        The value of threshold of wavestrength above which classify the driving mode as stop-and-go. It defaults to the value of 50.
        

    Returns
    ----------
    `double`
        Returns stop-and-go distance measured based on the `wave_threshold` in meters 

    """

    # Check strymread object was able to successfully read the 
    if not strymobj.success:
        print("Invalid/Errored strymread object supplied. Check if supplied datafile to strymread is valid.")
        return None

    file_name = strymobj.csvfile
    file_name = file_name.split('/')[-1][0:-4]

    ## Get the speed
    speed = strymobj.speed()

    if speed.shape[0] == 0:
        print("No speed data found\n")
        return None
    elif speed.shape[0] < 10:
        print("Speed data too low. Skipping ...\n")
        return None

    ### Convert speed to m/s
    speed['Message'] = speed['Message']*0.277778
    position  = strymread.integrate(speed)
    # Get the position

    ## Get the longitudinal acceleration
    accelx = strymobj.accelx()

    if accelx.shape[0] == 0:
        print("No Acceleration data found\n")
        return None
    elif accelx.shape[0] < 10:
        print("Acceleration data too low. Skipping ...\n")
        return None
    

    # strymread.plt_ts(speed, title="Original Speed (m/s)")
    # strymread.plt_ts(position, title="Original Position (m)")
    # strymread.plt_ts(accelx, title="Original Accel (m/s^2)")

    # Synchronize speed and acceleration for common time points with a rate of 20 Hz
    speed_resampled, accel_resampled = strymread.ts_sync(speed, accelx, rate=20, method = "nearest")
    position_resampled, _ = strymread.ts_sync(position, accelx, rate=20, method = "nearest")


    # strymread.plt_ts(speed_resampled, title="Resampled Speed (m/s)")
    # strymread.plt_ts(position_resampled, title="Resampled position (m)")
    # strymread.plt_ts(accel_resampled, title="Resampled Accel (m/s^2)")
    
    assert ((speed_resampled.shape[0] == accel_resampled.shape[0]) and (position_resampled.shape[0]==accel_resampled.shape[0])), "Synchronization Error"

    df = speed_resampled


    df["Speed"] =  speed_resampled["Message"]
    df["Accelx"] = accel_resampled["Message"]
    df["Position"] = position_resampled["Message"]
    df.drop(columns=["Message"], inplace=True)
    
    if df.shape[0] < 3:
        print("Extremely low sample points in synced-resampled data to obtain any meaningful measure. Skipping ...")
        return None

    DeltaT = np.mean(df['Time'].diff())
    #print(1./DeltaT)
    n_Sample_WS = int((1/DeltaT)*window_size) # Number of samples for 30 seconds
    #print(n_Sample_WS)

    df.index = np.arange(0, df.shape[0])
    #print(n_Sample_WS)
    df['wavestrength'] = 0
    count = 0
    for r, row in  df.iterrows():
        if r <=n_Sample_WS:
            continue
        df_tempWS = df[r-n_Sample_WS:r]
        velocity_tempWS = pd.DataFrame()
        velocity_tempWS['Time'] = df_tempWS['Time']
        velocity_tempWS['Message'] = df_tempWS['Speed']
        accel_tempWS = pd.DataFrame()
        accel_tempWS['Time'] = df_tempWS['Time']
        accel_tempWS['Message'] = df_tempWS['Accelx']
        ps = phasespace(dfx=velocity_tempWS, dfy=accel_tempWS, resample_type="first", verbose=False)
        count = count + 1
        if plot_iteration:
            if count % 200  == 0:
                count = 0
                print("--------------------------------------------------------------")
                print('Time Range: {} to {}'.format(accel_tempWS['Time'].iloc[0], accel_tempWS['Time'].iloc[-1]))
                ps.phaseplot(title='Phase-space plot of speed-acceleration. Time window ['+\
                         str(accel_tempWS['Time'].iloc[0]) + ', ' + str(accel_tempWS['Time'].iloc[-1])+']\n' + file_name +'\n',\
                         xlabel='Speed', ylabel='acceleration')
                ps.centroidplot( xlabel='Centroid Distance', ylabel='Counts')
                print("Average Centroid Distane of cluster is {}".format(ps.acd))
        df['wavestrength'].iloc[df_tempWS.index[-1]] = ps.acd

    # Filter out data for which strong wave was detected
    high_wave = df[df['wavestrength'] > wave_threshold]
    
    # high_wave now is discontinuous in Time column, use this information to create separate
    # continuous chunks and over which we calculate the total distance
    high_wave_chunk = strymread.create_chunks(high_wave, continuous_threshold=0.1, \
                                              column_of_interest = 'Time', plot = False)
    
    stop_ang_go_distance = 0.0
    for c in high_wave_chunk:
        d = c['Position'][-1] - c['Position'][0]
        stop_ang_go_distance = stop_ang_go_distance + d
    
    if plot_timespace or save_timespace:
        fig, ax = strymread.create_fig(nrows = 4, ncols=1)

        im = ax[0].scatter(df['Time'], df['Position'], c=np.log(df['wavestrength']+1), cmap='magma', s=3)
        im2 = ax[1].scatter(df['Time'], df['Position'], c=df['Speed'], cmap='magma', s=3)
        im3 = ax[2].scatter(df['Time'], df['Speed'], c=df['Time'], cmap='magma', s=3)
        im4 = ax[3].scatter(df['Time'], df['wavestrength'], c=df['Time'], cmap='magma', s=3)

        cbr = fig.colorbar(im, ax=ax[0])
        cbr.set_label("wavestrength")
        ax[0].set_xlabel('Time')
        ax[0].set_ylabel('Position')
        ax[0].set_title('Time-Space Diagram with log(wavestrength+1) as color map')

        cbr = fig.colorbar(im2, ax=ax[1])
        cbr.set_label("speed")
        ax[1].set_xlabel('Time')
        ax[1].set_ylabel('Position')
        ax[1].set_title('Time-Space Diagram with speed as color map')

        cbr = fig.colorbar(im3, ax=ax[2])
        cbr.set_label("Time")
        ax[2].set_xlabel('Time')
        ax[2].set_ylabel('Speed')
        ax[2].set_title('Time-Speed Diagram with Time as color map')

        cbr = fig.colorbar(im4, ax=ax[3])
        cbr.set_label("Time")
        ax[3].set_xlabel('Time')
        ax[3].set_ylabel('wavestrength')
        ax[3].set_title('Time-WaveStrength Diagram with Time as color map')
        
        dt_object = datetime.datetime.fromtimestamp(time.time())
        dt = dt_object.strftime('%Y-%m-%d-%H-%M-%S-%f')

        if save_timespace:
            file_to_save = "ACD_"+ file_name + "_time_space_diagram_" + dt
            fig.savefig(file_to_save + ".png", dpi = 100)
            fig.savefig(file_to_save + ".pdf", dpi = 100)
    
        if plot_timespace:
            plt.show()
        else:
            plt.close(fig)
    
    return stop_ang_go_distance