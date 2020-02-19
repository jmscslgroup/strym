#!/usr/bin/env python
# coding: utf-8

from strym import strymread
import strym
import matplotlib.pyplot as plt
import numpy as np

r =strymread(csvfile="/home/ivory/CyverseData/JmscslgroupData/PandaData/2020_02_18/2020-02-18-12-49-46-552710__CAN_Messages.csv", dbcfile='./newToyotacode.dbc')


speed = r.ts_speed()
# rate analysis
strym.ranalyze(speed, title='Speed Data')

track_id = np.arange(0, 1)
long_dist = r.ts_long_dist(track_id)

strym.ranalyze(long_dist, title='Longitudinal Distance Data: TRACK A 0')