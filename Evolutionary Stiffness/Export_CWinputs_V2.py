# -*- coding: utf-8 -*-

import os
import St7API
import St7Toolbox_JA_V2 as St7Tbx

import tkinter as tk
from tkinter import filedialog

St7API.St7Init()

###################
# SET YOUR PARAMETERS HERE

# Modify to your own model location
# If you are using relative path, set them with respect to your script
# Example of full path If you use the fullpath, you can add r in front of it
# it sets the string as a raw string, \0 will be considered as a string and
# not as a special character (for example as in url %20 means \ )
# modelname = r'O:/PSM3700/Eng/Tools/Model.st7'
root = tk.Tk()
root.withdraw()


# Make it almost invisible - no decorations, 0 size, top left corner.
root.overrideredirect(True)
root.geometry('0x0+0+0')

# Show window again and lift it to top so it can get focus,
# otherwise dialogs will end up behind the terminal.
root.deiconify()
root.lift()
root.focus_force()
# File dialog to pick folder directory where the results .csv files are saved
modelname = filedialog.askopenfilename(title = 'Select Strand7 Model', filetypes=[('Strand7 Model (.st7)', '*.st7')])

# Get rid of the top-level instance once to make it actually invisible.
root.destroy()
#modelname = r'C:\Users\Christine\Documents\PSM\Models\PLATES.st7'

# If you want to keep a specific group, speicifes here parent
# If you want to consider all the groups, set it to ALL or remove from function
# GroupsToKeep = ['Model\LINING'] # a specific group
GroupsToKeep = 'ALL' #to keep them all

# Set which axis user wants to export the results
# Choose between Local and Global
ResultAxis = 'Local'


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
                                         GroupsToKeep)
numPlates = numElem['Plates']
ret = St7Tbx.export_cwinputs(modelname_bt, tempfolder_bt,
                                          resultfile_bt, groupID, numPlates, 0.4,
                                          ResultAxis='Local')
St7API.St7CloseFile(1)
St7API.St7CloseResultFile(1)
St7API.St7Release()
