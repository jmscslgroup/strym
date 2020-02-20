#!/usr/bin/env python
# coding: utf-8

from strym import strymread
import strym
import matplotlib.pyplot as plt
import numpy as np

r =strymread(csvfile="/home/ivory/CyverseData/JmscslgroupData/PandaData/2020_02_18/2020-02-18-13-00-42-209119__CAN_Messages.csv", dbcfile='./newToyotacode.dbc')

# plot the count statistics of message ID
r.count()

speed = r.ts_speed()

# time series plot
strym.plt_ts(speed, title="Speed (Km/h)")

# violin plot of speed data
strym.violinplot(speed["Message"], title="Speed (Km/h)")

# rate analysis
strym.ranalyze(speed, title='Speed Data')


track_id = np.arange(0, 1) # I want to analyze rate for 
long_dist = r.ts_long_dist(track_id)

strym.ranalyze(long_dist, title='Longitudinal Distance Data: TRACK A 0')