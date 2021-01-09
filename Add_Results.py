# -*- coding: utf-8 -*-

import os
import St7API
import St7Toolbox_JA as St7Tbx
import pandas as pd

import tkinter as tk
from tkinter import filedialog

St7API.St7Init()

###################
# SET YOUR PARAMETERS HERE
root = tk.Tk()
root.withdraw()
root.overrideredirect(True)
root.geometry('0x0+0+0')
root.deiconify()
root.lift()
root.focus_force()
modelname = filedialog.askopenfilename(title = 'Open Strand7 Model', filetypes= (("Strand7 Model","*.st7"),("all files","*.*")))
root.destroy()

root = tk.Tk()
root.withdraw()
root.overrideredirect(True)
root.geometry('0x0+0+0')
root.deiconify()
root.lift()
root.focus_force()
PlateResultsFile = filedialog.askopenfilename(title = 'Open .csv containing results', filetypes= (("csv files","*.csv"),("all files","*.*")))
root.destroy()

DF = pd.read_csv(PlateResultsFile)
DF = DF.fillna(0)

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
fileOut = modelname[:-4] + '_results.st7'
fileOut_bt = fileOut.encode()

# Call function to get the model information
ret = St7Tbx.assign_plates_results(modelname_bt, tempfolder_bt, fileOut_bt, DF)

# Close Strand7 Model
St7API.St7CloseFile(1)
St7API.St7CloseResultFile(1)
St7API.St7Release()
