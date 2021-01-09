# -*- coding: utf-8 -*-
"""
Created on Thu May 21 08:09:46 2020

@author: Jiwoo Ahn
"""
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
suffix = '_RC1-RA3 RL'

SC.MaxAst(savepath, all_files, 'MaxAstAS5100'+suffix)
SC.MaxAstStage(savepath, all_files, 'MaxAstStageAS5100'+suffix)

#SC.MaxAsv(savepath, all_files, 'MaxAsvAS5100'+suffix)
#SC.MaxAsvStage(savepath, all_files, 'MaxAsvStageAS5100'+suffix)