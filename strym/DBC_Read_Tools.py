#!/usr/bin/env python
# coding: utf-8

# Author : George Gunter, Matthew Nice - Vanderbilt University
# Contact: gunter.gl@gmail.com, matthew.nice@vanderbilt.edu, rahulbhadani@email.arizona.edu
# with some modifications by Rahul Bhadani

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
pt.style.use('seaborn')
import csv
import pandas as pd
import cantools
import matplotlib.animation as animation
from matplotlib import style



def initializeDBC_Cantools(fileName):
    db = cantools.database.Database()
    with open('newToyotacode.dbc','r') as fin:
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
    Data = a[['Time','Message']]
    if Data.empty:
        print("warning: dataframe empty. message not in dataframe.")

    return Data

def Reformat_Can_Data(can_data_file_Path,newName):
    #NOTE: This is written specifically for the kind of data that is written in this folder, it may not
    #reformat other files correctly.
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



def CleanData(df):
    """Drop the data rows in the dataframe that have NA in them."""
    clean = df.dropna(axis=0,how='any') #drop na data from rows with any NA values. these rows are deleted from the dataframe.
    #clean = df[df.notna()] #define dataframe as the subset of the dataframe that is not NA. not sure if this should be used instead of the former.
    x = df.loc[df['MessageID'] == address]
    if address > 0: #check if address parameter is in use
        if len(x['Message'].values[1]) != 16: #check if length of data is 16 (8 bytes)
            print("Message not 8 bytes")
            fullbytes = x.copy()
            fullbytes['Message'] = x['Message'].str.ljust(16,'0') #copy the data ljust'ed into new dataframe e.g. '00ff032a' --> '00ff032a00000000'
            df.update(fullbytes) #update the dataframe with correct data size
            return df
    return clean




def convertData(messageNameID,attribute, df, db):
    """Finds the data for a message and returns a dataframe with time and integer hex for the signal you want.

    messageNameID is the string or integer that represents your message.
    attribute is the string or integer that represents your signal."""

    message = findMessageInfo(messageNameID,db) #locate and store the message for use
    #print(message)
    messageData = ExtractChffrData(messageNameID,df,db) #extract the time and hex data for the relevant message

    if type(attribute) is str:
        attribute = getSignalID(messageNameID, attribute, db) #get the signal int ID if a string was used, for decoding the message below

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

    if message != "not in DBC" and message.signals != []: #if the message is in the DBC
        messageData['Message'] = messageData['Message'].apply(lambda x: bytes.fromhex(x)) #transfrom the message's hexidecimal data into byte format
        #e.g. 0000000069118ec4 --> b'\x00\x00\x00\x00\x69\x11\x8e\xc4'
        #decode_message from cantools needs this byte format to work correctly db.decode_message(36,b'\x03\xfe\x01\x00\x42\x08\x80\xe5')
        #decode_message returns a dictionary of the signal values that make up the data value
        #the line below takes that dictionary and makes it into a list, then picks out the signal in the list that is relevant
        #since this is done in an anonymous function, it is applied to all data values in the dataframe.
        decimalData['Message'] = messageData['Message'].apply(lambda x: list(db.decode_message(messageNameID,x).values())[attribute])
    else:#if the message is not in the DBC, decode the hexidecimal into integer value, but can't actually decode signals without DBC
        decimalData['Message'] = messageData['Message'].apply(lambda x: int(x,16))
        converted = "not in DBC"
        print("No delineation of signals, scale, or offset; message just decoded from hex to int.")

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
