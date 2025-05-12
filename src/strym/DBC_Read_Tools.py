#!/usr/bin/env python
# coding: utf-8

# Author : Matthew Nice - Vanderbilt University, with some modifications by Rahul Bhadani
# Contact: matthew.nice@vanderbilt.edu, rahulbhadani@email.arizona.edu

# Initial Date: Feb 17, 2020
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

import numpy as np
import matplotlib.pyplot as pt
import csv
import pandas as pd
import cantools
import matplotlib.animation as animation
from matplotlib import style
import os



def initializeDBC_Cantools(fileName):
    db = cantools.database.Database()
    with open(fileName,'r') as fin:
        db.add_dbc_string(fin.read())
    return db

def getNumpyData(messageID,attribute,df,db):
    decimal_Data = convertData(messageID,attribute,df,db)
    numpy_Data = np.zeros([len(decimal_Data),2])
    numpy_Data[:,0] = decimal_Data['Time'].values
    numpy_Data[:,1] = decimal_Data['Message'].values
    return numpy_Data

def cleanDistanceData(numpyData):
    temp = []
    for i in range(len(numpyData)):
        if(numpyData[i,1] < 300):
            temp.append(numpyData[i,:])
    new_Dist_Data = np.array(temp)
    return new_Dist_Data

def plotMessages(messages, df, db):
    """Plot up to the first 9 signals of a message, and plot multiple messages in one line.
    Requires message IDs, dataframe, and DBC db.

    e.g. plotMessages([384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399],hwy3,db)"""
    y = len(messages)
    for j in range (0,y):
        x = len(db.get_message_by_frame_id(messages[j]).signals)
        if x > 9:
            print('There are more than 9 signals, only printing first 9.')
        pt.figure(j)
        pt.suptitle(db.get_message_by_frame_id(messages[j]).name)
        for i in range (0,x):
            m = convertData(messages[j],i,df,db)
            if i < 9:
                pt.subplot(3,3,i+1)
                name = db.get_message_by_frame_id(messages[j]).signals[i].name
                pt.tight_layout()
                pt.plot(m['Time'], m['Message'], 'k',marker = ",", linewidth = 0.2)
                pt.title(name)

def getMessageName(frameOrName,db):
    """Retrieve string name of a message from the db.

    frameOrName parameter should be ID integer.
    """
    myName = db.get_message_by_frame_id(frameOrName).name
    return myName

def getSignalName(frameOrName, signalNum,db):
    """Retrieve string name of signal.

    frameOrName is the ID str or int for the message. signalNum is the int representing that this signal
    is the nth signal in the message. If the signal is not in the DBC, it will return a name
    "not in the DBC", and print out a warning.

    e.g. getSignalName(37,1, db2) or getSignalName('STEER_ANGLE_SENSOR',2, db2)
    """
    if type(frameOrName) is int:
        try:
            name = db.get_message_by_frame_id(frameOrName).signals[signalNum].name
        except:
            print("warning: str addr not in DBC")
            name = "not in DBC"
    elif type(frameOrName) is str:
        try:
            name = db.get_message_by_name(frameOrName).signals[signalNum].name
        except:
            print("warning: str addr not in DBC")
            name = "not in DBC"
    return name


def getSignalID(frameOrName, signalName, db):
    """Get the int ID of a signal by giving the message name and signal name.

    frameOrName is the ID str or int for the message. signalName is the name of the signal that you want the ID for.
    """

    myNum = None
    if type(frameOrName) is int:
        try:
            num = db.get_message_by_frame_id(frameOrName).signals

            for  i in range(len(num)) :
                if num[i].name == signalName:
                    myNum = i
                    #print(myNum)
                i += 1
        except:
            print("warning: str addr not in DBC")
            myNum = "not in DBC"
    elif type(frameOrName) is str:
        try:
            num = db.get_message_by_name(frameOrName).signals

            for  i in range(len(num)) :
                if num[i].name == signalName:
                    myNum = i
                    #print(myNum)
                i += 1
        except:
            print("warning: str addr not in DBC")
            myNum = "not in DBC"

    return myNum

def findMessageInfo(messageNameorNum,db):
    """This function does text parsing on a dbc file to select the relevant pieces
    of information.

    It looks first for the kind of message that is desired, which
    is specified by messageNameorNum. It then looks through db, which is a Database object from cantools
    that corresponds to the lines of the dbc file. It returns the message, which
    includes the message attributes, its signals and their attributes as well."""

#Breakdown of a signal: name, start, length, byte_order, is_signed, is_float, scale, offset, minimum, maximum, unit, is_Multiplexer, idk=None ,idk=None , comment
    if type(messageNameorNum) is str:
        try:
            messageInfo = db.get_message_by_name(messageNameorNum) #if string used, get message by name, e.g. 'KINEMATICS'
        except:
            print("warning: str addr not in DBC")
            messageInfo = "not in DBC"
    elif type(messageNameorNum) is int:
        try:
            messageInfo = db.get_message_by_frame_id(messageNameorNum) #if number use, get message by frame id, e.g. 36
        except:
            print("warning: int addr not in DBC")
            messageInfo = "not in DBC"

    return messageInfo

def ExtractChffrData(messageNameOrNum,df,db):
    #Extracts the relevant time and hexidecimal data from the dataframe created from the csv:
    if type(messageNameOrNum) is str:
        x = findMessageInfo(messageNameOrNum, db)
        messageNameOrNum = x.frame_id #if string is given, retrieve the message id number
    a = df.loc[df['MessageID']== messageNameOrNum]
    Data = a[['Time','Message', 'Bus','MessageLength']]
    if Data.empty:
        print("warning: dataframe empty. no message in dataframe.")

    return Data

def Reformat_Can_Data(can_data_file_Path,newName):
    """NOTE: This is written specifically for the kind of data that is written in this folder, it may not
    #reformat other files correctly."""
    data = []
    with open(can_data_file_Path, newline='') as csvfile:
        can_reader = csv.reader(csvfile, delimiter=',')
        for row in can_reader:
            data.append(row)
    with open(newName,'w') as csvfile:
        can_writer = csv.writer(csvfile,delimiter=',')
        can_writer.writerow(data[0])
        for row in data[1:]:
            newRow = row
            newRow[3] = row[3][4:-1]
            newRow[2] = int(row[2],0)
            can_writer.writerow(newRow)

def CleanData(df, address = False):
    """Drop the data rows in the dataframe that have NA in them.
    When using the address option, it will fill in byte arrays to be 64 bits (8 bytes).
    """
    clean = df.dropna(axis=0,how='any') #drop na data from rows with any NA values. these rows are deleted from the dataframe.
    #clean = df[df.notna()] #define dataframe as the subset of the dataframe that is not NA. not sure if this should be used instead of the former.
    df = df.reset_index()
    x = df.loc[df['MessageID'] == address]

    if address > 0: #check if address parameter is in use
        if len(x['Message'].values[1]) != 16: #check if length of data is 16 (8 bytes)
            print("Making data 8 bytes")
            fullbytes = x.copy()
            fullbytes['Message'] = x['Message'].str.ljust(16,'0') #copy the data ljust'ed into new dataframe e.g. '00ff032a' --> '00ff032a00000000'

            df.update(fullbytes) #update the dataframe with correct data size
    return df

def convertData(messageNameID,attribute, df, db):
    """Finds the data for a message and returns a dataframe with time and integer hex for the signal you want.
    Will filter CAN msgs to be the length defined in the DBC database.
    messageNameID is the string or integer that represents your message.
    attribute is the string or integer that represents your signal."""

    message = findMessageInfo(messageNameID,db) #locate and store the message for use
    #print(message)
    length = message.length #msg length defined in DBC

    messageData = ExtractChffrData(messageNameID,df,db) #extract the time and hex data for the relevant message
    messageData = messageData.where(messageData.MessageLength == length).dropna() #filter data by message length in DBC
#     if type(attribute) is str:
#         attribute = getSignalID(messageNameID, attribute, db) #get the signal int ID if a string was used, for decoding the message below

    #for printing out characteristics of the signal being looked at. not actually using right now because I find it superfluous.
    #may be useful in the future
    if message != "not in DBC" and message.signals != []:
        if type(attribute) is str:
            start = message.get_signal_by_name(attribute).start
            length = message.get_signal_by_name(attribute).length
            scale = message.get_signal_by_name(attribute).scale
        elif type(attribute) is int:
            start = message.signals[attribute].start
            length = message.signals[attribute].length
            scale = message.signals[attribute].scale


        #print('StartPos is: '+str(start))
        #print('Length is: '+str(length))
        #print('Scale is: '+str(scale))

    decimalData = messageData.copy() #make a copy of messagedata, output hex to dec

    #For reference of the way I first tried to decode the message by signal:
        #decimalData['data'] = messageData['data'].str[startIndex:endIndex].apply(lambda x: int(x,16))*scale+offset
    try:
        multiplexed = db.get_message_by_frame_id(messageNameID).is_multiplexed()
        if multiplexed:
            print('Message multiplexed. Be wary your input is correct.')
            multiplexID = message.get_signal_by_name(attribute).multiplexer_ids[0]
    except:
        if message != "not in DBC":
            multiplexed = db.get_message_by_name(messageNameID).is_multiplexed()
            if multiplexed:
                print('Message multiplexed. Be wary your input is correct.')
                multiplexID = message.get_signal_by_name(attribute).multiplexer_ids[0]

    if message != "not in DBC" and message.signals != []: #if the message is in the DBC
#         print(message.signals)
        #print(messageData['data'])
        #bug = messageData['data']
        #if type(messageData['data'][317]) is not bytes:
        if multiplexed:
            df = df.where(df.Bus != multiplexID)


        messageData['Message'] = messageData['Message'].apply(lambda x: bytes.fromhex(x)) #transfrom the message's hexidecimal data into byte format
        #byte format: e.g. 0000000069118ec4 --> b'\x00\x00\x00\x00\x69\x11\x8e\xc4'
        #decode_message from cantools needs this byte format to work correctly db.decode_message(36,b'\x03\xfe\x01\x00\x42\x08\x80\xe5')
        #decode_message returns a dictionary of the signal values that make up the data value
        #the line below takes that dictionary and makes it into a list, then picks out the signal in the list that is relevant
        #since this is done in an anonymous function, it is applied to all data values in the dataframe.
        if type(attribute) is str:

            decimalData['Message'] = messageData['Message'].apply(lambda x: db.decode_message(messageNameID,x))#[attribute]
            decimalData['Message'] = decimalData['Message'].apply(lambda x: x[attribute] if attribute in x.keys() else None)
        else:
            decimalData['Message'] = messageData['Message'].apply(lambda x: list(db.decode_message(messageNameID,x).values())[attribute])
    else:#if the message is not in the DBC, decode the hexidecimal into integer value, but can't actually decode signals without DBC
        decimalData['Message'] = messageData['Message'].apply(lambda x: int(x,16))
        converted = "not in DBC"
        print("No delineation of signals, scale, or offset; message just decoded from hex to int.")
    decimalData = decimalData.dropna()
    return decimalData

def plotDBC(address, attributeNum, df, db):
    """Plot the data for a specific signal.

    address: the str or int of the address of the signal.
    attributeNum: the str or int of the signal you want to plot."""
    style.use('seaborn-ticks')
    decimalData = convertData(address,attributeNum, df, db) #convertData will return the data pairs to plot
    if (decimalData.empty != 0) or (decimalData['Message'].dtypes == 'object'): #if the data is empty or the data is an object, not plottable
        print("No Data Available To Plot")
        if decimalData['Message'].dtypes == 'object':
            print("Data is object type")
    else:
        if findMessageInfo(address,db) != "not in DBC":
            if type(attributeNum) is int:
                attributeNum = getSignalName(address, attributeNum, db) #get signal name for the title, if needed
            if type(address) is int:
                address = getMessageName(address, db) #get message name for title, if needed
        pt.rcParams["figure.figsize"] = (12,8)
        params = {'legend.fontsize': 15,
          'legend.handlelength': 2}
        pt.rcParams.update(params)
        pt.rcParams["font.family"] = "Times New Roman"
        pt.style.use('ggplot')
        fig =pt.figure()
        ax = fig.add_subplot(1,1,1)
        #ax.set_axisbelow(True)
        ax.minorticks_on()
        ax.tick_params(axis="x", labelsize=15)
        ax.tick_params(axis="y", labelsize=15)
        #ax.grid(which='major', linestyle='-', linewidth='0.5', color='skyblue')
        #ax.grid(which='minor', linestyle=':', linewidth='0.25', color='dimgray')
        ax.set_xlabel('Time')
        ax.set_ylabel('Message', fontsize=15)
        ax.set_title("Timeseries plot\nMessage Type: " + str(address) + ", Signal: " + str(attributeNum),fontsize= 16)
        decimalData.plot(x='Time', y='Message', ax = ax, color='firebrick', linewidth=1, grid=True, linestyle='-', marker ='.', markersize=2 )#plot the converted data
        pt.show()

def findObjectData(x):
    """For use in a lambda function to transform non-int converted data into something to plot.

    Uses so far:
        Turn Signal - 1556
        LKAS_HUD - 1042
        Gears - 956
    """

    if x == 'none' or x == 'standby' or x == 'P':
        return 0
    if x == 'left' or x == 'D':
        return 1
    else:
        return -1

def KF_leadDist(df, plot=False, sd = False):
    """This function is to give a filtered estimation of the state of the lead distance in an offline batch.

    Dataframe input needs only two columns: the measurements of lead distance, and the times of the measurements.
    Columns assumed titled 'Time', and 'Message'.

    Setting plot to True will output plots. SD to True adds in the standard deviationon the plots."""

    df=df.sort_values(by = 'Time').reset_index(drop=True) #make sure df is time sorted

    #cleaning up erroneous high lead distance values:
    for i in range(0,len(df.Message)):
        if df.Message[i] > 240:
            df = df.drop(i)

    times = df.Time.values
    measurements = df.Message.values

    initial_state_mean = [measurements[0], #distance
                          0] #relv

    transition_matrix = [[1, 1],
                         [0, 1]]

    observation_matrix = [[1, 0]]

    observation_covariance = [[1]] #R

    transition_covariance = [[1,0],
                            [0,1]] #Q


    kf1 = KalmanFilter(transition_matrices = transition_matrix,
                      observation_matrices = observation_matrix,
                      initial_state_mean = initial_state_mean,
                      transition_covariance =  transition_covariance,
                      observation_covariance = observation_covariance)

    (filtered_state_means, filtered_state_covariances) = kf1.filter(measurements)

    #calculating the variance of the states
    if sd == True:
        D_variance = []
        D_sd=[]
        rV_sd=[]
        for i in range(0,len(filtered_state_covariances)):
            D_variance.append(filtered_state_covariances[i][0][0])
            D_sd.append(3*np.sqrt(filtered_state_covariances[i][0][0]))
            rV_sd.append(1*np.sqrt(filtered_state_covariances[i][1][1]))

        D_1sd_minus = [i * -.33 for i in D_sd]
        D_1sd_plus = [i * .33 for i in D_sd]
        D_sd_minus=  [i * -1 for i in D_sd] #3 st dev minus
        Rv1sd_minus = [i * -1 for i in rV_sd]
    if plot == True:
        pt.figure(1)

        pt.plot(times,measurements,'ro', markersize = 2, label='Measurements')
        pt.plot(times,filtered_state_means[:, 0], 'bo', markersize = 2,label='Estimated State')
        if sd == True:
            pt.plot(times,measurements-D_sd, 'g--')
            pt.plot(times,measurements+D_sd, 'g--',label='3SD')
            pt.title('Measurements, Mean State, and Confidence Interval')
        else:
            pt.title('Measurements, and Mean Estimated State')
        pt.xlabel('Time (seconds)')
        pt.ylabel('Lead Distance (meters)')
        pt.legend()
        pt.show()

        slope = pd.Series(np.gradient(df.Message), df.Time, name='CAN RelV')

        pt.figure(2)
        pt.plot(times,filtered_state_means[:, 1], 'b--',label='Estimated Relv State')
        pt.plot(slope,'g--',marker='.',markersize = 5,ls='',label='Gradient from Measurements') #CAN data relv
        pt.title('Relative Velocity State Estimation')
        pt.xlabel('Time (seconds)')
        pt.ylabel('Relative Velocity (meters/second)')
        pt.legend()
        pt.show()

    return filtered_state_means, filtered_state_covariances

def radarPoints(df, db2):
    '''This function goes through all the radar tracks and returns a dataframe with the columns=['time','lon','lat','relv','theta','trackid','valid','score'].
    A dataframe of CAN data is all that is needed for input. Useful for data analysis of radar data, but it is slow.'''

    z = pd.DataFrame(columns=['time','lon','lat','relv','theta','trackid','valid','score'])
    lon = pd.DataFrame()
    lat = pd.DataFrame()
    relv = pd.DataFrame()
    valid = pd.DataFrame()
    score = pd.DataFrame()
#     trackid = pd.DataFrame(columns=['ID'])

    a = 384
    while a < 400:
        lat = lat.append(convertData(a,2,df,db2))
        a += 1
    z.lat = lat.Message

    a = 384
    x = 0
    while a < 400:
        newData = convertData(a,1,df,db2)
        lon = lon.append(newData)
        z.trackid[x: x+newData.shape[0]] = a
        x = x+newData.shape[0]
        a = a + 1

    z.lon = lon.Message

    a = 384
    while a < 400:
        relv = relv.append(convertData(a,4,df,db2))
        a += 1

    a = 384
    while a < 400:
        valid = valid.append(convertData(a,5,df,db2))
        a += 1

    z.valid = valid.Message

    a = 400
    while a < 416:
        if a == 401:
            filtered401 = df.loc[
                df.Bus == 1
            ]
            score = score.append(convertData(a,'SCORE',filtered401,db2))
        else:
            score = score.append(convertData(a,'SCORE',df,db2))
        a+= 1
    score = score.reset_index(drop = True)

    z.time = lon.Time
    z.relv = relv.Message
    z.theta = np.degrees(np.arctan(np.array(z.lat),np.array(z.lon)))
#     z.trackid = trackid.ID
#     print(trackid)
    z = z.reset_index(drop=True)


    z.score = score.Message

    return z

def findRelv(df, db2):
    """Input the dataframe and this function matches the radar data near the lead distance message. Uses naive algorithm.
    The average value from the radar data within 0.05 seconds of the lead distance message is put in the output df.
    The output relv df has columns=['time','lon','lat','relv','theta','trackid','valid','score'].
    This allows for further exploration of lead-associated radar data, or you can simply pull the relv if you like."""
    g_radar = radarPoints(df,db2)
    myLead = convertData(869,6,df,db2) #space gap
    myLead2 = myLead.where(myLead.Bus != 128).dropna()
    myLead2 = myLead.reset_index(drop=True)

    relvArray = pd.DataFrame(columns=['time','lon','lat','relv','theta','trackid','valid','score'])

    for x in range(0,len(myLead2)):
        temp_df = g_radar.loc[
            (abs(g_radar.time - myLead2.Time[x]) < 0.05) &
            (np.floor(g_radar.lon) == myLead2.Message[x])
        ]
        relvArray =  relvArray.append(np.mean(temp_df),ignore_index=True)
    return relvArray

# def interpolateMessage(nonGpsDF, GpsDf, featureName = None):
#     '''This function, used initially for synchronizing CAN messages to GPS data, takes both the GPS df
#     (interpolating to this time) and non-GPS df (synchronizes "Message" to Gpstime). The featureName
#     option is for when the nonGPS df has many columns that you want to input. This should be in a list
#     format if used.
#
#     Function returns the message as a numpy array interpolated to GPS df time measurements.'''
#     if featureName == None:
#         f = interpolate.interp1d(nonGpsDF.Time,nonGpsDF.Message)
#         my_new = f(GpsDf.Gpstime.where(
#             (GpsDf.Gpstime > int(nonGpsDF.Time.head(1)))&
#             (GpsDf.Gpstime < int(nonGpsDF.Time.tail(1))))
#                    )
#         return my_new
#     else:
#         my_newDf = []
#         for i in range(0,len(featureName)):
#             f = interpolate.interp1d(nonGpsDF.Time,nonGpsDF[featureName[i]])
#             my_new = f(GpsDf.Gpstime.where(
#                 (GpsDf.Gpstime > int(nonGpsDF.Time.head(1)))&
#                 (GpsDf.Gpstime < int(nonGpsDF.Time.tail(1))))
#                       )
#             my_newDf.append(my_new)
#         return my_newDf

def search_files(directory='.', extension=''):
    '''Search for files below directory that contain the extension.'''
    extension = extension.lower()
    matches = []
    for dirpath, dirnames, files in os.walk(directory):
        for name in files:
            if extension and name.lower().endswith(extension):
                matches.append(os.path.join(dirpath, name))
            elif not extension:
                matches.append(os.path.join(dirpath, name))
    return matches

def generateMasterArray(CAN,GPS,db,i24 = True):
    """This takes a CAN and GPS csv, loaded DBC file db, and outputs an array of relevant data for data analysis. i24 is a flag to filter out just
    general I-24 MOTION testbed area data (between Briley pkwy and i840 on I-24) . If set to false, the data from the drive will be from any GPS area."""

    leeVictory = [35.932315, -86.528873]
    samRidley = [35.980207, -86.576175]
    waldron = [35.995608, -86.596973]
    oldHickory = [36.014674, -86.620617]
    hickoryHollow = [36.038491, -86.647301]
    bellRd = [36.044731, -86.657844]
    haywood = [36.066515, -86.686374]
    harding = [36.082071, -86.697719]
    briley = [36.112280, -86.723168]
    i840 = [35.880067, -86.470954]
    GPS = pd.read_csv(GPS)
    CAN = pd.read_csv(CAN)
#     print('loaded data')
    #clean the GPS data
    #this is what we will use for time and absolute position
    #

    GPS.head(40) #check to see where the status goes to A permanently
    GPS = GPS.drop(index=[x for x in range(20)])
    GPS = GPS.where(GPS.Status == 'A')
    GPS = GPS.dropna()
    GPS = GPS.reset_index(drop=True)
#     print('pruned GPS')
    if i24 == True:
        try:
            GPS = GPS.loc[ #the gps on I-24
                    (GPS.Long > briley[1])&
                    (GPS.Long < i840[1]) &
                    (GPS.Lat < briley[0]) &
                    (GPS.Lat > i840[0])
                ]
            print('found I24 data')
        except:
            print('failed to filter GPS')
    startTime = int(GPS.Gpstime.head(1))
    stopTime = int(GPS.Gpstime.tail(1))

    #clean CAN data
    CAN = CAN.where(CAN.Bus != 128).dropna() #clean CAN data
    CAN = CAN.where(CAN.Bus != 130).dropna() #clean CAN data

    #get all of the CAN message series', make sure the CAN time and GPS time aren't an hour off
    sg = s.convertData(869,6,CAN,db)
#     print('testing GPS/CAN time sync')
    sg_new = interpolateToGPS(sg,GPS)
    if pd.isnull(max(sg_new)) or min(sg_new) ==252:
        print('hour does not match')
        CAN.Time = CAN.Time - 3600
    else:
        print(max(sg_new))
#         pt.plot(sg_new)

    #velocity
    v = s.convertData(180,1,CAN, db)
    #acceleration
    a = s.convertData(552,'ACCEL_X',CAN, db)
    #BSM features
    lapproach = s.convertData(1014,'L_APPROACHING',CAN,db)
    rapproach = s.convertData(1014,'R_APPROACHING',CAN,db)
    ladjacent = s.convertData(1014,'L_ADJACENT',CAN,db)
    radjacent = s.convertData(1014,'R_ADJACENT',CAN,db)
    #relative velocity and space gap
    relv = s.convertData(869,7,CAN,db)
    sg = s.convertData(869,6,CAN,db)

    print('converted CAN data')

    a_new = interpolateToGPS(a,GPS)
    v_new = interpolateToGPS(v,GPS)
    lapproach_new = interpolateToGPS(lapproach,GPS)
    rapproach_new = interpolateToGPS(rapproach,GPS)
    ladjacent_new = interpolateToGPS(ladjacent,GPS)
    radjacent_new = interpolateToGPS(radjacent,GPS)
    relv_new = interpolateToGPS(relv,GPS)
    sg_new = interpolateToGPS(sg,GPS)

    masterArray = pd.DataFrame(columns = ['Time','Velocity','Acceleration','SpaceGap','RelativeVelocity','LongitudeGPS','LatitudeGPS','L_Approach','R_Approach','L_Adjacent','R_Adjacent'])

    masterArray.Time = GPS.Gpstime
    masterArray.Velocity = v_new
    masterArray.Acceleration = a_new
    masterArray.LongitudeGPS = GPS.Long
    masterArray.LatitudeGPS = GPS.Lat
    masterArray.L_Approach = lapproach_new
    masterArray.R_Approach = rapproach_new
    masterArray.L_Adjacent = ladjacent_new
    masterArray.R_Adjacent = radjacent_new
    masterArray.RelativeVelocity = relv_new
    masterArray.SpaceGap = sg_new

    return masterArray

def interpolateToGPS(nonGpsDF, GpsDf, featureName = None):
    '''This function, used initially for synchronizing CAN messages to GPS data, takes both the GPS df
    (interpolating to this time) and non-GPS df (synchronizes "Message" to Gpstime). The featureName
    option is for when the nonGPS df has many columns that you want to input. This should be in a list
    format if used.

    Function returns the message as a numpy array interpolated to GPS df time measurements.'''
    if featureName == None:
        f = interpolate.interp1d(nonGpsDF.Time,nonGpsDF.Message)
        try:
            my_new = f(GpsDf.Gpstime.where(
                (GpsDf.Gpstime > int(nonGpsDF.Time.head(1)))&
                (GpsDf.Gpstime < int(np.floor(nonGpsDF.Time.tail(1)))))
                       )
        except:
            my_new = f(GpsDf.Gpstime.where(
            (GpsDf.Gpstime > int(nonGpsDF.Time.head(1)))&
            (GpsDf.Gpstime < int(np.floor(nonGpsDF.Time.tail(1)))))
                   )
        return my_new
    else:
        my_newDf = []
        for i in range(0,len(featureName)):
            try:
                f = interpolate.interp1d(nonGpsDF.Time,nonGpsDF[featureName[i]],fill_value='extrapolate')
                my_new = f(GpsDf.Gpstime.where(
                    (GpsDf.Gpstime > int(nonGpsDF.Time.head(1)))&
                    (GpsDf.Gpstime < int(np.floor(nonGpsDF.Time.tail(1)))))
                          )
                my_newDf.append(my_new)
            except:
                print('data missing in ' + str(featureName[i]))
        return my_newDf
