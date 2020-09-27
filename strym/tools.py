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
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import os
import cv2

def _acplots():
    """
    Function for internal use.

    Creates plot using grid spect for using with ACD algorithm

    Returns
    ----------

    fig, ax
        Returns figure and axes object
    """

    nrows = 3
    ncols = 6
    strymread._setplots(ncols=2,nrows=5)
    fig = plt.figure()
    spec = gridspec.GridSpec(ncols=ncols, nrows=nrows, figure=fig)
    ax1 = fig.add_subplot(spec[0, 0:3])
    ax2 = fig.add_subplot(spec[0, 3:6])
    ax3 = fig.add_subplot(spec[1, 0:2])
    ax4 = fig.add_subplot(spec[1, 2:4])
    ax5 = fig.add_subplot(spec[1, 4:6])
    ax6= fig.add_subplot(spec[2, :])

    ax  = [ax1, ax2, ax3, ax4, ax5, ax6]

    for i, a in enumerate(ax):
        a.minorticks_on()
        a.set_alpha(0.4)
        a.grid(which='major', linestyle='-', linewidth='0.25', color='dimgray')
        a.grid(which='minor', linestyle=':', linewidth='0.25', color='dimgray')
        a.patch.set_facecolor('#efefef')
        a.spines['bottom'].set_color('#828282')
        a.spines['top'].set_color('#828282')
        a.spines['right'].set_color('#828282')
        a.spines['left'].set_color('#828282')
    
    return fig, ax
    

def acd(strymobj= None, window_size=30, plot_iteration = False, every_iteration = 200, plot_timespace = True, save_timespace = False, wave_threshold = 50.0, animation = False, title = 'Average Centroid Distance', **kwargs):
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
    `pandas.DataFrame`
        Returns Pandas Data frame consisting of WaveStrength column as a timeseries

    `double`
        Returns stop-and-go distance measured based on the `wave_threshold` in meters 

    """

    # Check strymread object was able to successfully read the 
    if strymobj is not None:
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
    else:
        file_name = ''
        speed = kwargs.get("speed", None)
        if speed is None:
            print("No speed data provided. Skipping ...\n")
            return None
        accelx = kwargs.get("accelx", None)
        if accelx is None:
            print("No longitudinal  data provided. Skipping ...\n")
            return None

        speed_unit = kwargs.get("speed_unit", "km/h")
        if speed_unit.lower() not in ["km/h", "m/s"]:
            print("Unrecognized speed unit '{}'. Provide speed unit in km/h or m/s\n".format(speed_unit))
            return None

        if speed_unit.lower() == "km/h":
            ### Convert speed to m/s
            speed['Message'] = speed['Message']*0.277778
        elif speed_unit.lower() == "m/s":
            print("INFO: Speed unit is m/s")


        position = kwargs.get("position", None)
        if position is None:
            position  = strymread.integrate(speed)

    # strymread.plt_ts(speed, title="Original Speed (m/s)")
    # strymread.plt_ts(position, title="Original Position (m)")
    # strymread.plt_ts(accelx, title="Original Accel (m/s^2)")

    # Synchronize speed and acceleration for common time points with a rate of 20 Hz

    rate = kwargs.get("rate", 20)

    speed_resampled, accel_resampled = strymread.ts_sync(speed, accelx, rate=rate, method = "nearest")
    position_resampled, _ = strymread.ts_sync(position, accelx, rate=rate, method = "nearest")


    # strymread.plt_ts(speed_resampled, title="Resampled Speed (m/s)")
    # strymread.plt_ts(position_resampled, title="Resampled position (m)")
    # strymread.plt_ts(accel_resampled, title="Resampled Accel (m/s^2)")
    
    assert ((speed_resampled.shape[0] == accel_resampled.shape[0]) and (position_resampled.shape[0]==accel_resampled.shape[0])), "Synchronization Error"

    df = speed_resampled.copy(deep=True)


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

    # Save images in /tmp folder dy default

    dt_object = datetime.datetime.fromtimestamp(time.time())
    dt = dt_object.strftime('%Y-%m-%d-%H-%M-%S-%f')

    image_path = kwargs.get("image_path", "/tmp")
    image_path = image_path + '/WaveStrength_' + dt
    if animation:
        if not os.path.exists(image_path):
            try:
                os.mkdir(image_path)
            except OSError:
                print("[ERROR] Failed to create the image folder {0}.".format(image_path))

    figure_count = 1

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
        if plot_iteration or animation:
            if count % every_iteration  == 0:
                count = 0
                print("--------------------------------------------------------------")
                print('Time Range: {} to {}'.format(accel_tempWS['Time'].iloc[0], accel_tempWS['Time'].iloc[-1]))
                #fig, ax = strymread.create_fig()
                fig, ax = _acplots()
                strymread.plt_ts(speed_resampled, ax = ax[0], show = False, title = "Speed")
                strymread.plt_ts(accel_resampled, ax = ax[1], show = False, title="Acceleration")
                
                # Create a Rectangle patch that represents window of the iteration
                rect = patches.Rectangle((velocity_tempWS['Time'].iloc[0], np.min(speed_resampled['Message'])),\
                    np.abs(velocity_tempWS['Time'].iloc[-1] - velocity_tempWS['Time'].iloc[0]),\
                        np.max(speed_resampled['Message']) - np.min(speed_resampled['Message']),\
                        linewidth=4,edgecolor='g',facecolor='none')
                ax[0].add_patch(rect)

                rect = patches.Rectangle((accel_tempWS['Time'].iloc[0], np.min(accel_resampled['Message'])),\
                    np.abs(accel_tempWS['Time'].iloc[-1] - accel_tempWS['Time'].iloc[0]),\
                        np.max(accel_resampled['Message']) - np.min(accel_resampled['Message']),\
                        linewidth=4,edgecolor='g',facecolor='none')

                ax[1].add_patch(rect)

                ax1 = ps.phaseplot(title='Phase-space plot',\
                         xlabel='Speed', ylabel='Acceleration', plot_each = True, ax = [ax[2], ax[3], ax[4]], show = False, fig = fig)

                subtext = 'Time Window: ['+\
                         str(accel_tempWS['Time'].iloc[0]) + ', ' + str(accel_tempWS['Time'].iloc[-1])+']\n' + file_name +'\n'
                ax[2].xaxis.label.set_size(35)
                ax[3].xaxis.label.set_size(35)
                ax[4].xaxis.label.set_size(35)

                ax[2].yaxis.label.set_size(35)
                ax[3].yaxis.label.set_size(35)
                ax[4].yaxis.label.set_size(35)

                ax[2].title.set_fontsize(40)
                ax[3].title.set_fontsize(40)
                ax[4].title.set_fontsize(40)

                ax[4].set_xlim(np.min(speed_resampled['Message'])-2.0, np.max(speed_resampled['Message'])+ 2.0)
                ax[4].set_ylim(np.min(accel_resampled['Message'])-2.0, np.max(accel_resampled['Message'])+ 2.0)

                ax2 = ps.centroidplot( xlabel='Centroid Distance', ylabel='Counts', ax = ax[5], show = False)
                plt.subplots_adjust(wspace=0, hspace=0)
                plt.tight_layout()
                my_suptitle = fig.suptitle(title + '\n' + subtext, y = 1.06)
                if animation:
                    figure_file_name = image_path + '/' + "wave_strength_{:06d}.png".format(figure_count) 
                    fig.savefig(figure_file_name, dpi = 100,bbox_inches='tight',bbox_extra_artists=[my_suptitle])
                    figure_count = figure_count + 1

                if plot_iteration:
                    plt.show()
                else:
                    plt.close(fig)
                print("Average Centroid Distane of cluster is {}".format(ps.acd))

        df['wavestrength'].iloc[df_tempWS.index[-1]] = ps.acd


    if animation:
        figdirs = os.listdir(image_path)
        figdirs.sort()
        images = [img for img in figdirs if img.endswith(".png")]
        # frame = cv2.imread(os.path.join(image_path, images[0]))
        # height, width, layers = frame.shape

        video_name = 'wave_strength' + dt + '.mp4'
        # video = cv2.VideoWriter(video_name, 0, 1, (width,height))

        # for image in images:
        #     video.write(cv2.imread(os.path.join(image_path, image)))

        # cv2.destroyAllWindows()
        # video.release()
        import ffmpeg
        (
        ffmpeg
        .input(image_path + '/*.png', pattern_type='glob', framerate=5)
        .output(video_name)
        .run()
        )

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

        im = ax[0].scatter(df['Time'], df['Position'], c=np.log(df['wavestrength']+1), cmap=strymread.sunset, s=3)
        im2 = ax[1].scatter(df['Time'], df['Position'], c=df['Speed'], cmap=strymread.sunset, s=3)
        im3 = ax[2].scatter(df['Time'], df['Speed'], c=df['Time'], cmap=strymread.sunset, s=3)
        im4 = ax[3].scatter(df['Time'], df['wavestrength'], c=df['Time'], cmap=strymread.sunset, s=3)
        
        cbr= strymread.set_colorbar(fig = fig, ax = ax[0], im = im, label = "log(wavestrength+1)")
            
        ax[0].set_xlabel('Time')
        ax[0].set_ylabel('Position')
        ax[0].set_title('Time-Space Diagram with log(wavestrength+1) as color map')

        cbr= strymread.set_colorbar(fig = fig, ax = ax[1], im = im2, label = "speed")

        ax[1].set_xlabel('Time')
        ax[1].set_ylabel('Position')
        ax[1].set_title('Time-Space Diagram with speed as color map')
        
        cbr= strymread.set_colorbar(fig = fig, ax = ax[2], im = im3, label = "Time")

        ax[2].set_xlabel('Time')
        ax[2].set_ylabel('Speed')
        ax[2].set_title('Time-Speed Diagram with Time as color map')

        cbr= strymread.set_colorbar(fig = fig, ax = ax[3], im = im4, label = "Time")


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
    
    return df, stop_ang_go_distance