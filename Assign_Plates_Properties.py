# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 14:30:26 2020

@author: Jiwoo Ahn
"""


import os
import sys
import St7API
import pandas as pd
import St7Toolbox_JA as St7Tbx
import tkinter as tk
from tkinter import filedialog

St7API.St7Init()

###################
# Initial Model name
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

Foldername = os.path.dirname(modelname) + "\\"
        
# Modified Model
fileOut = Foldername + 'RC1-RA2_S2C_Iter1.st7'
# Input material parameters
PlatePropertiesFile = Foldername + 'PlateProperties.csv'


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
fileOut_bt = fileOut.encode()

groupID, entTots = St7Tbx.get_model_info(modelname_bt, tempfolder_bt)

numPlates = entTots['Plates']
    
DF = pd.read_csv(PlatePropertiesFile)
DF = DF.fillna(0)

ret = St7Tbx.assign_plates_prop(modelname_bt, tempfolder_bt, fileOut_bt, DF, groupID, numPlates, True)

St7API.St7CloseFile(1)
St7API.St7Release()
print("API released")
