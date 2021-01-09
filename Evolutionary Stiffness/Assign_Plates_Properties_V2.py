# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 14:30:26 2020

@author: Jiwoo Ahn
"""


import os
import sys
import St7API
import pandas as pd
import St7Toolbox_JA_V2 as St7Tbx

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
modelname = filedialog.askopenfilename(title = 'Select Strand7 Model', filetypes=[('Strand7 Model (.st7)', '*.st7')])
# Get rid of the top-level instance once to make it actually invisible.
root.destroy()

Foldername = os.path.dirname(modelname) + "\\"

# USER INPUTS HERE
# ___________________________________________________________________________


itr_label = os.path.basename(modelname).split('.')[0].split('_')[-1]
iteration_no = int(itr_label[-1])+1
fileOut = modelname.replace(itr_label, itr_label[:-1]+str(iteration_no))


"""
iteration_no = 2

fileOut = Foldername + 'AC1-AA1&AA3_S2B_Iter' + str(iteration_no) + '.st7'

#fileOut = Foldername + 'RC1-RA2_S2C_Iter' + str(iteration_no) + '.st7'
"""
# ___________________________________________________________________________

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

# Input material parameters
PlatePropertiesFile = Foldername + 'PlateProperties.csv'
DF = pd.read_csv(PlatePropertiesFile)
DF = DF.fillna(0)

ret = St7Tbx.assign_plates_prop(modelname_bt, tempfolder_bt, fileOut_bt, DF, groupID, numPlates, True, 27, iteration_no)

St7API.St7CloseFile(1)
St7API.St7Release()
print("API released")


St7API.St7Init()

filename = os.path.splitext(fileOut)[0]
resultfile = fileOut.split('st7')[0] + 'NLA'
resultfile_bt = resultfile.encode()


ret2 = St7Tbx.export_ES_Inputs(modelname_bt, tempfolder_bt, filename,
                                          resultfile_bt, groupID, numPlates, 0.4,
                                          ResultAxis='Local')

St7API.St7CloseFile(1)
St7API.St7CloseResultFile(1)
St7API.St7Release()

print ("Iteration " + str(iteration_no) + " complete")