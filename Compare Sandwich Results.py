# -*- coding: utf-8 -*-
"""
Created on Thu May 21 08:09:46 2020

@author: Jiwoo Ahn
"""

# Ignore this stuff ----------------------------------------------------------------------------------

import ComparisonToolbox as SC
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
savepath = str(Path(folderpath).parents[1]) + "\\"

# Get rid of the top-level instance once to make it actually invisible.
root.destroy()

# Read all .csv files in specified folder
all_files = sorted(glob.glob(folderpath + '/'+'*.csv'), key=lambda x: int(os.path.basename(x).split('.')[0].split('_')[1]))

# Ignore this stuff ----------------------------------------------------------------------------------

# File name suffix
suffix = '_RC1-RA1 FS'

# Compares the Crushing (MPa), Ast (mm2) and Asv (mm2/m2) and gives you the highest value
res = SC.MaxResult(savepath, all_files, 'MaxResults'+suffix)

# Compares the Crushing (MPa), Ast (mm2) and Asv (mm2/m2) and gives you the load combination that has the highest value
#SC.MaxResultStage(savepath, all_files, 'MaxResultsStage'+suffix)

# Ast (mm2) and Asv (mm2/m2) and gives you the highest bar size
SC.MaxBarSize(savepath, all_files, 'MaxBarSize'+suffix)

# Ast (mm2) and Asv (mm2/m2) and gives you the stage with the highest bar size
#SC.MaxBarSizeStage(savepath, all_files, 'MaxBarSizeStage'+suffix)
