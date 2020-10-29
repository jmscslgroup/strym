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
from scipy.interpolate import fitpack
from .strymread import strymread
import seaborn as sea
from .phasespace import phasespace
import datetime
import time
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import os
import random
from scipy import optimize
import math

def _acdplots():
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

def threept_center(x1, x2, x3, y1, y2, y3):
    """
    Calculates center coordinate of a circle circumscribing three points
    
    Parameters
    --------------
    x1: `double`
        First x-coordinate 
    x2: `double`
        Second x-coordinate 
    x3: `double`
        Third y-coordinate 
    y1: `double`
        First y-coordinate 
    y2: `double`
        Second y-coordinate 
    y3: `double`
        Third y-coordinate 
    
    Returns
    ----------
    double, double:
        Returns center coordinates of the circle. Return None, None if the determinant is zero
    
    """
    
    determinant = 2*( (x3-x2)*(y2 - y1) - (x2 - x1)*(y3-y2) )
    
    if determinant < 0.1:
        return None, None
    
    
    x_numerator = (y3 - y2)*(x1**2 + y1**2) + (y1 - y3)*(x2**2 + y2**2) + (y2 - y1)*(x3**2 + y3**2)
    y_numerator = (x3 - x2)*(x1**2 + y1**2) + (x1 - x3)*(x2**2 + y2**2) + (x2 - x1)*(x3**2 + y3**2)
    
    xc = x_numerator/(2*determinant)
    yc = -y_numerator/(2*determinant)
    
    return xc, yc

def coord_precheck(x, y):
    """
    Check the x, y coordinates for consistency and lengths
    If x and y are not of the same length, it should return False
    
    Parameters
    -------------
    x: `list`| `pd.Series` | `np.array`
        X-coordinates

    y: `list`| `pd.Series` | `np.array`
        Y-coordinates


    Returns
    ---------
    
    bool:
        Returns True of x and y coordinate lists are of same lengths
    
  
    """
    length_x = 0
    length_y = 0
    if isinstance(x, list):
        length_x = len(x)
    elif isinstance(x, pd.Series):
        length_x = x.shape[0]
    elif isinstance(x, np.ndarray):
        length_x = x.shape[0]

    if isinstance(y, list):
        length_y = len(y)
    elif isinstance(y, pd.Series):
        length_y = y.shape[0]
    elif isinstance(y, np.ndarray):
        length_y = y.shape[0]

    if length_x == 0 or length_y == 0:
        print("Empty list or data supplied.")
        return False
    elif length_x != length_y:
        print("The number of x-coordinates is not equal to the number of y-coordinates.")
        return False
    elif length_x < 5:
        print("Too few data-points.")
        return False
    
    return True

def init_center(x, y):
    """
    Initialize center of circle encompassing (xi,yi) coordinates before attempting 
    to do least square fitting

    Parameters
    -------------
    x: `list`| `pd.Series` | `np.ndarray`
        X-coordinates

    y: `list`| `pd.Series` | `np.ndarray`
        Y-coordinates

    Returns
    ----------
    double, double
        Center coordinates of a circle
    
    """
    if not coord_precheck(x, y):
        return None, None
    
    x = x.to_numpy() if isinstance(x, pd.Series) else x
    x = np.array(x) if isinstance(x, list) else x
    
    # randonly sample 40 coordinates if number of coordinates are too large
    if len(x) > 40:
        x = random.sample(list(x), 40)
        y = random.sample(list(y), 40)
    
    # number of coordinate points
    m = len(x) if isinstance(x, list) else x.shape[0]
      
    xclist = []
    yclist = []
    
    for i in range(0, m-2):
        for j in range(i+1, m-1):
            for k in range(j+1,m ):
                xc, yc = threept_center(x[i], x[j], x[k], y[i], y[j], y[k])
                if xc is not None and yc is not None:
                    xclist.append(xc)
                    yclist.append(yc)
        
    
    return np.median(xclist), np.median(yclist)

def graham_scan(x, y):
    '''
    Perform graham scan algorithm on (x, y) to return convex hull and convex perimeter
    
    Parameters
    -------------
    x: `numpy.array` | `pandas.Series` | `list`
        X-coordinates of the cluster to fit

    y: `numpy.array` | `pandas.Series` | `list`
        Y-coordinates of the cluster to fit
    
    Returns
    -----------
    
    `pandas.DataFrame`;
        Pandas DataFrame with sorted points representing Convex Hull
    `double`:
        Convex hull perimeter
    '''

    Points = pd.DataFrame()
    Points['x'] = x
    Points['y'] = y
    # Find the point with the lowest y-coordinate.
    # if there are multiple points with the same lowest
    # y-coordinate , pick one with lowest x-coordinate
    # call this Point P

    lowest_x = Points[ Points['y'] == np.min(Points['y'])]
    P = Points[(Points['x'] == np.min(lowest_x['x'])) & (Points['y'] == np.min(Points['y']))]

    # Now the set of points must be sorted in the increasing order of the angle they and the point P make with the x-axis

    Points['theta_P'] = np.arctan2( (Points['y'] - P['y'].iloc[0]), (Points['x'] - P['x'].iloc[0]) )
    Points.sort_values(by = 'theta_P', inplace=True)
    
    Convex_Hull = pd.DataFrame(columns=['x', 'y', 'theta_P'])

    def ccw(a, b, c):

        # Check if three points a, b, c make counter clockwise turn:
        '''
        The points
        (x1∣y1);(x2∣y2);(x3∣y3)
        are in anticlockwise order, then
        det(x1 & y1 & 1\\x2 & y2 & 1\\x3 & y3 & 1)>0 . If clockwise, then <0, colinear if == 0
        '''
        matrix = [[a['x'], a['y'], 1], 
                    [b['x'], b['y'], 1],
                    [c['x'], c['y'], 1]]

        determinant = np.linalg.det(matrix)
        if np.abs(determinant) < 0.000001:
            determinant = 0
        return determinant

    for i, row in Points.iterrows():

        while (Convex_Hull.shape[0] > 1) and (ccw(Convex_Hull.iloc[1], Convex_Hull.iloc[0], row) <= 0 ):
            Convex_Hull = Convex_Hull.iloc[1:]
            Convex_Hull = Convex_Hull.reset_index(drop = True) 

        Convex_Hull.loc[-1] = [row['x'], row['y'], row['theta_P']]  # adding a row
        Convex_Hull.index = Convex_Hull.index + 1  # shifting index
        Convex_Hull.sort_index(inplace=True) 

        perimeter  = 0
        for i in range(Convex_Hull.shape[0]-1):
            edge = np.sqrt( (Convex_Hull.iloc[i]['x'] - Convex_Hull.iloc[i+1]['x'])**2 + \
                    (Convex_Hull.iloc[i]['y'] - Convex_Hull.iloc[i+1]['y'])**2)
            perimeter = perimeter + edge
            
        last_edge = np.sqrt( (Convex_Hull.iloc[0]['x'] - Convex_Hull.iloc[-1]['x'])**2 + \
                    (Convex_Hull.iloc[0]['y'] - Convex_Hull.iloc[-1]['y'])**2)

        perimeter = last_edge  + perimeter
        perimeter

        return Convex_Hull, perimeter

def ellipse_fit(x, y, fit_circle= False):
    """
    Fits an ellipse to the data point via least square method.
    
    Parameters
    -------------
    X: `numpy.array` | `pandas.Series` | `list`
        X-coordinates of the cluster to fit

    Y: `numpy.array` | `pandas.Series` | `list`
        Y-coordinates of the cluster to fit

    fit_circle: `bool`
        Fit circle instead of Ellipse (i.e. when Major Axis = Minor Axis)

    Returns
    ----------
    `double`, `double`, `double`, `double`, `double:
        X-coordinate of fitted Circle/Eillipse's center, Y-coordinate of fitted Circle/Eillipse's center, Length of Semi-Major Axis, Length of Semi-Minor Axis, Residual As a goodness of fit
    
    Notes
    --------
    **Circle-fitting**    

    Circle fitting is done using Equation

     .. math::
        F(X) = aX^T X  + b^T x + c = 0

    Minimizing algebraic distance
    
    By putting all x, y corrdinates X=(x,y) into above equation
    and get the system of equaion :math:`Bu = 0` with :math:`u = (a, b_1, b_2, c)^T`

    For :math:`m > 3` we cannot expect the system to have a solution, unless all the points
    are on circle. Hence, we solve overdetermined system Bu = r where u is chosen
    to minimize :math:`||r||` where :math:`|| ||` is L2 norm. Hence the problem is minimize :math:`||Bu||`
    subject to :math:`||u|| = 1`.

    Minimizing geometrical distance
    
    Equation can also be written as

    .. math::
        (x + \cfrac{b_1}{2a})^2  + (y + \cfrac{b_2}{2a})^2 = \cfrac{||b||^2}{4a^2 - (c/a)}


    In this case, we minimize the sum of squares of the distance :math:`d_i^2 = (||z - xi||- r)^2`
    
    Let parameters be :math:`u = (z_1, z_2, r)`

    Then our problem becomes minimize :math:`\sum d_i(u)^2`
    
    **Ellipse fitting**

    Ellipse is a special case of a general conic :math:`F(x,y) = ax^2 + bxy + cy^2 + dx + ey + f = 0` subject to the constraint :math:`b^2 - 4ac < 0`.


    See Also
    -----------
    `Method for Circle Fitting <https://web.archive.org/web/20201002005236/https://www.emis.de/journals/BBMS/Bulletin/sup962/gander.pdf>`_

    `Ellipse Fitting using Least Square <http://autotrace.sourceforge.net/WSCG98.pdf>`_

    `Ellipse Wikipedia <https://en.wikipedia.org/wiki/Ellipse>`_

   
    """ 
    z10, z20 = init_center(x, y)

    if z10 is None or  z20 is None:
        print("Fitting not possible.")
        
    length_x = len(x) if isinstance(x, list) else x.shape[0]

    z1 = None
    z2 = None
    r1 = None
    r2 = None
    if fit_circle:
        def euclidean_dist(z1, z2):
            d = []    
            for m in range(0,length_x):
                dm = np.sqrt((  z1 - x[m] )**2 +(z2 - x[m] )**2)
                d.append(dm)

            return np.array(d)

        def objective(u,xy):
            xc,yc,Ri = u
            distance = [np.sqrt( (x-xc)**2 + (y-yc)**2 ) for x,y in xy]
            res = [(Ri-dist)**2 for dist in distance]
            return res


        r0 = np.mean(euclidean_dist(z10, z20))
        
        # initial values
        u_0 = [z10, z20, r0]
        
        data = np.column_stack((x, y))

        final_theta, solution_flag = optimize.leastsq(objective, u_0,args=(data))

        if solution_flag not in [1, 2, 3, 4]:
            print("Warning: no optimal solution was found.")

        z1 = final_theta[0]
        z2 = final_theta[1]
        r = final_theta[2]
        
        
        r1 = r
        r2 = r
        return z1, z2, r1, r2

    else:
        if not coord_precheck(x, y):
            return None, None

        x= np.array(x) if isinstance(x, list) else x
        y= np.array(y) if isinstance(y, list) else y
        D1= np.vstack([x**2, x*y, y**2]).T
        D2 = np.vstack([x, y, np.ones_like(x)]).T
        S1 = D1.T @ D1
        S2 = D1.T @ D2
        S3 = D2.T @ D2
        C1 = np.array([[0., 0., 2.], [0., -1., 0.], [2., 0., 0.]])
        M = np.linalg.inv(C1) @ (S1 - S2 @ np.linalg.inv(S3) @ S2.T)

        _, eigvec = np.linalg.eig(M)
        cond = ( 4*np.multiply(eigvec[0, :], eigvec[2, :]) - np.power(eigvec[1, :], 2) )

        a1 = eigvec[:, np.nonzero(cond > 0)[0]]
        a2 = np.linalg.inv(-S3) @ S2.T @ a1
        a =a1[0]
        b = a1[1]
        c = a1[2]
        d =a2[0]
        e= a2[1]
        f = a2[2]

        term1 = (b**2 - 4*a*c)
        z1 = (2*c*d - b*e)/term1
        z2 = (2*a*e - b*d)/term1

        term2 = 2*(a*e*e + c*d*d - b*d*e + term1*f)
        term3 = (a + c)
        term4 = np.sqrt( (a-c)**2 + b**2)

        r1_num = -1*np.sqrt(term2 * (term3 + term4))
        r2_num = -1*np.sqrt(term2 * (term3 - term4))

        r1 = r1_num/term1
        r2 = r2_num/term1
        
        phi = 0
        if b != 0:
            #phi = np.arctan( (1/b)* (c - a - np.sqrt( (a-c)**2  + b**2 ))  )  
            phi = np.arctan2((c - a - np.sqrt( (a-c)**2  + b**2 ))  , b)  
        elif b == 0 and a < c:
            phi = 0
        elif b == 0 and a > c:
            phi = 1.5708

        # with above configuration two kind of ellipses are possible and they both are pendicular to each other, however, only one will be aligned with actual data. We will calculate the residual for both possible ellipses and choose only in which residual is less

        # let's calculate residual as a goodness of fit
        # first we have to sort (x, y) by angles
        d = pd.DataFrame()
        d['X'] = x
        d['Y'] = y
        d['theta'] = np.arctan2( (y - z2), (x - z1) )
        d.sort_values(by = 'theta', inplace=True)
        x = d['X'].tolist()
        y = d['Y'].tolist()

        xdash = []
        ydash = []
        for p in np.linspace(-np.pi, np.pi, length_x):
            x1 = z1 + r1*math.cos(p)
            y1 = z2 + r2*math.sin(p)
            xdash.append(x1)
            ydash.append(y1)

        residual= 0
        for i in range(0, length_x):
            d = np.sqrt((x[i] - xdash[i])**2 + (y[i] - ydash[i])**2)
            residual = residual + d
        residual = residual/length_x

        return z1[0], z2[0], r1[0], r2[0], phi[0], residual

    

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

    every_iteration: `int`
        If `plot_iteration` is true, then plot the intermediate figures every `every_iteration` iteration
    
    plot_timespace: `bool`
        If `True` plots and save timespace diagram of wavestrength for the given drive.

    save_timespace: `bool`
        If `True` save the timespace diagram to the disk

    wave_threshold: `double`
        The value of threshold of wavestrength above which classify the driving mode as stop-and-go. It defaults to the value of 50.
        
    animation: `bool`
        If `True` produces animation of phasespace evolving with the time

    title: `str`
        Desire plot title for phasespace animation

    image_path: `str`
        Path on the disk where to store phasespace animation    


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
    n_Sample_WS = int((1/DeltaT)*window_size) # Number of samples for window_size
    print("Number of samples for {} seconds: {}".format(window_size, n_Sample_WS))

    df.index = np.arange(0, df.shape[0])
    #print(n_Sample_WS)
    df['wavestrength'] = 0
    df['EllipseFit_semimajor_axis_len'] = 0
    df['EllipseFit_semiminor_axis_len'] = 0
    df['Goodness_of_Ellipse_Fit'] = 0
    
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
        df_tempWS = df[r-n_Sample_WS-1:r-1]

        velocity_tempWS = pd.DataFrame()
        velocity_tempWS['Time'] = df_tempWS['Time']
        velocity_tempWS['Message'] = df_tempWS['Speed']
        accel_tempWS = pd.DataFrame()
        accel_tempWS['Time'] = df_tempWS['Time']
        accel_tempWS['Message'] = df_tempWS['Accelx']
        ps = phasespace(dfx=velocity_tempWS, dfy=accel_tempWS, resample_type="first", verbose=False)

        if np.all(velocity_tempWS['Message'] == 0) or np.all(accel_tempWS['Message'] == 0):
            z1 = 0
            z2 = 0
            r1 = 0
            r2 = 0
            phi = 0
            residual = 0
        else:
            z1, z2, r1, r2, phi, residual = ellipse_fit(x = velocity_tempWS['Message'].to_numpy(), y  = accel_tempWS['Message'].to_numpy())
        
        count = count + 1
        if plot_iteration or animation:
            if count % every_iteration  == 0:
                count = 0
                print("--------------------------------------------------------------")
                print('Time Range: {} to {}'.format(accel_tempWS['Time'].iloc[0], accel_tempWS['Time'].iloc[-1]))
                #fig, ax = strymread.create_fig()
                fig, ax = _acdplots()
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
                ax[4].set_aspect('equal', adjustable='box')
                c1= patches.Ellipse((z1, z2), r1*2,r2*2,   angle = math.degrees(phi), color='g', fill=False, linewidth = 5)
                ax[4].add_artist(c1)

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
                    fig.clear()
                    plt.close(fig)
                
                print("Average Centroid Distane of cluster is {}".format(ps.acd))


        #df.iloc[df_tempWS.index[-1], df.columns.get_loc('wavestrength') ] = ps.acd
        df['wavestrength'].iloc[df_tempWS.index[-1]] = ps.acd
        
        #df.iloc[df_tempWS.index[-1], df.columns.get_loc('EllipseFit_semimajor_axis_len') ] = r1
        #df.iloc[df_tempWS.index[-1], df.columns.get_loc('EllipseFit_semiminor_axis_len') ] = r2
        #df.iloc[df_tempWS.index[-1], df.columns.get_loc('Goodness_of_Ellipse_Fit') ] = residual

        df['EllipseFit_semimajor_axis_len'].iloc[df_tempWS.index[-1]] = r1
        df['EllipseFit_semiminor_axis_len'].iloc[df_tempWS.index[-1]] = r2
        df['Goodness_of_Ellipse_Fit'].iloc[df_tempWS.index[-1]] = residual
        

    if animation:
        figdirs = os.listdir(image_path)
        figdirs.sort()
        video_name = 'wave_strength' + dt + '.mp4'
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
    
    # stop_ang_go_distance = 0.0
    # for c in high_wave_chunk:
    #     d = c['Position'][-1] - c['Position'][0]
    #     stop_ang_go_distance = stop_ang_go_distance + d
    
    stop_ang_go_distance = 0.0
    for c in high_wave_chunk:
        pos_temp = strymread.integrate(c, msg_axis="Speed")
        stop_ang_go_distance = stop_ang_go_distance + pos_temp['Message'][-1]
    
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
