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