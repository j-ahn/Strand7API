# -*- coding: utf-8 -*-
"""
Export_PlateNodes.py

Example - Export node co-ordinates and plate vertices

Created on 26/05/2020

@author: Jiwoo Ahn
"""

import os
import sys
import ctypes
import St7API
import pandas as pd
import re
import os
import St7API
import St7Toolbox_JA as St7Tbx

import tkinter as tk
from tkinter import filedialog

St7API.St7Init()


# Tkinter open file dialog
root = tk.Tk()
root.withdraw()
root.overrideredirect(True)
root.geometry('0x0+0+0')
root.deiconify()
root.lift()
root.focus_force()
# File dialog to pick folder directory where the results .csv files are saved
modelname = filedialog.askopenfilename()
# Get rid of the top-level instance once to make it actually invisible.
root.destroy()

# If you want to keep a specific group, speicifes here parent
# If you want to consider all the groups, set it to ALL or remove from function
# GroupsToKeep = ['Model\LINING'] # a specific group
GroupsToKeep = 'ALL' #to keep them all

# Modify if you want your temporary folder to be elsewhere
# Strand7API requirement
tempfolder = os.getenv('TEMP')
if not os.path.exists(tempfolder):
    tempfolder = os.getenv('TMP')
    if not os.path.exists(tempfolder):
        tempfolder = input('Enter temporary folder path: ')

#Encoding Names
modelname_bt = modelname.encode()
tempfolder_bt = tempfolder.encode()
resultfile = modelname.split('st7')[0] + 'NLA'
resultfile_bt = resultfile.encode()

# Call function to get the model information
groupID, numElem = St7Tbx.get_model_info(modelname_bt, tempfolder_bt,
                                         GroupsToKeep=GroupsToKeep)
numPlates = numElem['Plates']
numNodes = numElem['Nodes']
ret = St7Tbx.export_platenodes(modelname_bt, tempfolder_bt, groupID, numNodes, numPlates, 0.4)

St7API.St7CloseFile(1)
St7API.St7CloseResultFile(1)
St7API.St7Release()
