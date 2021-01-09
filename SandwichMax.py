# -*- coding: utf-8 -*-
"""
Created on Thu May 21 08:09:46 2020

@author: Jiwoo Ahn
"""

import numpy as np
import pandas as pd
import os
import glob
from pathlib import Path
from tkinter import filedialog
from tkinter import *
root = Tk()

# Make it almost invisible - no decorations, 0 size, top left corner.
root.overrideredirect(True)
root.geometry('0x0+0+0')

# Show window again and lift it to top so it can get focus,
# otherwise dialogs will end up behind the terminal.
root.deiconify()
root.lift()
root.focus_force()
# File dialog to pick folder directory where the results .csv files are saved
folderpath = filedialog.askdirectory()
savepath = str(Path(folderpath).parents[0]) + "\\"
# Get rid of the top-level instance once to make it actually invisible.
root.destroy()
# Read all .csv files in specified folder
all_files = sorted(glob.glob(folderpath + '/'+'*.csv'), key=lambda x: int(os.path.basename(x).split('.')[0].split('_')[1]))

# Returns the maximum result (i.e. Compression check or steel area) of all stages
def MaxResult(savepath, all_files, filename):
    df = pd.concat((pd.read_csv(f,header = 0) for f in all_files),axis=1,sort=False)
    col = df.columns.tolist()[0:8]
    df = df.fillna(0)
    df = df.groupby(df.columns, axis=1, sort=False).agg(np.max)
    fname = savepath + filename+".csv"
    df.to_csv(fname,index=False)
    return df, col
# File name suffix
suffix = '_RC1-RA2'

# Compares the Crushing (MPa), Ast (mm2) and Asv (mm2/m2) and gives you the highest value
res = MaxResult(savepath, all_files, 'MaxResults'+suffix)