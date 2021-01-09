# -*- coding: utf-8 -*-
"""
Date: 21/05/2020

@author: Jiwoo Ahn
"""

import numpy as np
import pandas as pd
import os

'''
=================================================================================
Shear Model Outputs Comparison
=================================================================================
'''
  
    # Returns the maximum result (i.e. Compression check or steel area) of all stages
def MaxAst(savepath, all_files, filename):
    PlateID = pd.read_csv(all_files[0], header=0).iloc[:,0]
    df = pd.concat((pd.read_csv(f,header = 0) for f in all_files),axis=1,sort=False)
    
    col = df.columns.tolist()
    col = col[0:5]
    
    df = df.fillna(0)
    df = df.groupby(df.columns, axis=1).agg(np.max)
    df = df.reindex(columns=col)
    
    res_dict = {'asx_bot':df.iloc[:,1], 'asy_bot':df.iloc[:,2], 'asx_top':df.iloc[:,3], 'asy_top':df.iloc[:,4]}
    res_key = ['asx_bot', 'asy_bot', 'asx_top', 'asy_top']
    for i in res_key:
        res = pd.DataFrame(data={'TITLE':PlateID, i:res_dict[i]})
        fname = savepath + filename + "_" + i + ".txt"
        res.to_csv(fname, header=True, index=None, sep=" ")    
        
    filename = savepath + filename+".csv"
    df.to_csv(filename,index=False, header = True)


# Returns the maximum result (i.e. Compression check or steel area) of all stages
def MaxAstStage(savepath, all_files, filename):
    # extract load case names and number indices from .csv file
    LC = []
    numidx = []
    i =1
    for f in all_files:
        LC.append(os.path.basename(f.split('.')[0].replace('_results','')))
        numidx.append(i)
        i = i+1
    
    # read all results .csv files and compile into a dataframe based on result type (i.e. asx bottom)
    PlateID = pd.read_csv(all_files[0], header=0).iloc[:,0]
    asx_bot = pd.concat((pd.read_csv(f, header=0).iloc[:,1] for f in all_files),axis=1,sort=False)
    asy_bot = pd.concat((pd.read_csv(f, header=0).iloc[:,2] for f in all_files),axis=1,sort=False)
    asx_top = pd.concat((pd.read_csv(f, header=0).iloc[:,3] for f in all_files),axis=1,sort=False)
    asy_top = pd.concat((pd.read_csv(f, header=0).iloc[:,4] for f in all_files),axis=1,sort=False)
    
    # name columns according to load case name. Use = numidx to name columns according to load case number
    asx_bot.columns = numidx
    asy_bot.columns = numidx
    asx_top.columns = numidx
    asy_top.columns = numidx
    
    # find column index that corresponds to the maximum value for each row
    df3 = asx_bot.max(axis=1)
    df4 = asy_bot.max(axis=1)
    df5 = asx_top.max(axis=1)
    df6 = asy_top.max(axis=1) 

    r3 = []
    r4 = []
    r5 = []
    r6 = []

    # find column index that corresponds to the maximum value for each row
    for i in range(len(df3)):
        if df3.iloc[i] == 0:
            r3.append(0)
        else:
            r3.append(asx_bot.iloc[i].idxmax(axis=1))

        if df4.iloc[i] == 0:
            r4.append(0)
        else:
            r4.append(asy_bot.iloc[i].idxmax(axis=1))
            
        if df5.iloc[i] == 0:
            r5.append(0)
        else:
            r5.append(asx_top.iloc[i].idxmax(axis=1))

        if df6.iloc[i] == 0:
            r6.append(0)
        else:
            r6.append(asy_top.iloc[i].idxmax(axis=1))     

    res_dict = {'asx_bot':r3, 'asy_bot':r4, 'asx_top':r5, 'asy_top':r6}
    res_key = ['asx_bot', 'asy_bot', 'asx_top', 'asy_top']
    for i in res_key:
        res = pd.DataFrame(data={'TITLE':PlateID, i:res_dict[i]})
        fname = savepath + filename + "_" + i + ".txt"
        res.to_csv(fname, header=True, index=None, sep=" ")
    
    df = pd.DataFrame(data={'PlateNo':PlateID, 
                            'asx_bot':r3, 'asy_bot':r4,
                            'asx_top':r5, 'asy_top':r6})
    
    filename = savepath + filename + ".csv"    
    df.to_csv(filename, header = True,index=False)
    

# Returns the maximum result (i.e. Compression check or steel area) of all stages
def MaxAsv(savepath, all_files, filename):
    PlateID = pd.read_csv(all_files[0], header=0).iloc[:,0]
    df = pd.concat((pd.read_csv(f,header = 0) for f in all_files),axis=1,sort=False)
    col = df.columns.tolist()
    col = col[0:2]
    df = df.fillna(0)
    df = df.groupby(df.columns, axis=1).agg(np.max)
    df = df.reindex(columns=col)
    
    res = pd.DataFrame(data={'TITLE':PlateID, 'Asv':df.iloc[:,1]})
    fname = savepath + filename + "_" + 'Asv' + ".txt"
    res.to_csv(fname, header=True, index=None, sep=" ")
    
    filename = savepath + filename+".csv"
    df.to_csv(filename,index=False, header = True)
    
# Returns the stage index with the maximum result from all stages
def MaxAsvStage(savepath, all_files, filename):
    # extract load case names and number indices from .csv file
    LC = []
    numidx = []
    i =1
    for f in all_files:
        LC.append(os.path.basename(f.split('.')[0].replace('_results','')))
        numidx.append(i)
        i = i+1
    
    # read all results .csv files and compile into a dataframe based on result type (i.e. asx bottom)
    PlateID = pd.read_csv(all_files[0], header=0).iloc[:,0]
    asv = pd.concat((pd.read_csv(f, header=0).iloc[:,1] for f in all_files),axis=1,sort=False)
    
    # name columns according to load case name. Use = numidx to name columns according to load case number
    asv.columns = numidx
    
    ashear_bins = [0, 0.001, 559, 993, 1257, 2234, 5027, 8936, 13963, 1000000]
    ashear_labels =['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
    
    for x in numidx:
        asv[x] = pd.cut(asv[x], bins = ashear_bins, include_lowest=True, labels = ashear_labels)
        
    
    cat_columns = asv.select_dtypes(['category']).columns
    asv[cat_columns] = asv[cat_columns].apply(lambda x: x.cat.codes)

     # find column index that corresponds to the maximum value for each row
    df1 = asv.max(axis=1)
    
    r1 = []

    # find column index that corresponds to the maximum value for each row
    for i in range(len(df1)):
        if df1.iloc[i] == 0:
            r1.append(0)
        else:
            r1.append(asv.iloc[i].idxmax(axis=1))
    
    res = pd.DataFrame(data={'TITLE':PlateID, 'Asv':r1})
    fname = savepath + filename + "_" + 'Asv' + ".txt"
    res.to_csv(fname, header=True, index=None, sep=" ")
        
    df = pd.DataFrame(data={'PlateNo':PlateID, 'Asv':r1})
    
    filename = savepath + filename + ".csv"    
    df.to_csv(filename,index=False, header=True)
    

'''
=================================================================================
Sandwich Model Outputs Comparison
=================================================================================
'''

# Returns the maximum result (i.e. Compression check or steel area) of all stages
def MaxResult(savepath, all_files, filename):
    PlateID = pd.read_csv(all_files[0], header=0).iloc[:,0]
    df = pd.concat((pd.read_csv(f,header = 0) for f in all_files),axis=1,sort=False)
    col = df.columns.tolist()
    col = col[0:8]
    df = df.fillna(0)
    df = df.groupby(df.columns, axis=1).agg(np.max)
    df = df.reindex(columns=col)
    
    res_key = ['comp_bot', 'comp_top', 'asx_bot', 'asy_bot', 'asx_top', 'asy_top', 'ashear']
    
    for i in range(7):
        res = pd.DataFrame(data={'TITLE':PlateID, res_key[i]:df.iloc[:,i+1]})
        fname = savepath + filename + "_" + res_key[i] + ".txt"
        res.to_csv(fname, header=True, index=None, sep=" ")
        
    fname = savepath + filename+".csv"
    #df = df.reindex(columns=res_key)
    df.to_csv(fname,index=False)
    return df
# Returns the stage index with the maximum result from all stages
def MaxResultStage(savepath, all_files, filename):
    # extract load case names and number indices from .csv file
    LC = []
    numidx = []
    i =1
    for f in all_files:
        LC.append(os.path.basename(f.split('.')[0].replace('_results','')))
        numidx.append(i)
        i = i+1
    
    # read all results .csv files and compile into a dataframe based on result type (i.e. asx bottom)
    PlateID = pd.read_csv(all_files[0], header=0).iloc[:,0]
    comp_bot = pd.concat((pd.read_csv(f, header=0).iloc[:,1] for f in all_files),axis=1,sort=False)
    comp_top = pd.concat((pd.read_csv(f, header=0).iloc[:,2] for f in all_files),axis=1,sort=False)
    asx_bot = pd.concat((pd.read_csv(f, header=0).iloc[:,3] for f in all_files),axis=1,sort=False)
    asy_bot = pd.concat((pd.read_csv(f, header=0).iloc[:,4] for f in all_files),axis=1,sort=False)
    asx_top = pd.concat((pd.read_csv(f, header=0).iloc[:,5] for f in all_files),axis=1,sort=False)
    asy_top = pd.concat((pd.read_csv(f, header=0).iloc[:,6] for f in all_files),axis=1,sort=False)
    ashear = pd.concat((pd.read_csv(f, header=0).iloc[:,7] for f in all_files),axis=1,sort=False)
    
    # name columns according to load case name. Use = numidx to name columns according to load case number
    comp_bot.columns = numidx
    comp_top.columns = numidx
    asx_bot.columns = numidx
    asy_bot.columns = numidx
    asx_top.columns = numidx
    asy_top.columns = numidx
    ashear.columns = numidx
    
    # find column index that corresponds to the maximum value for each row
    df1 = comp_bot.max(axis=1)
    df2 = comp_top.max(axis=1)
    df3 = asx_bot.max(axis=1)
    df4 = asy_bot.max(axis=1)
    df5 = asx_top.max(axis=1)
    df6 = asy_top.max(axis=1)
    df7 = ashear.max(axis=1)
    
    r1 = []
    r2 = []
    r3 = []
    r4 = []
    r5 = []
    r6 = []
    r7 = []

    # find column index that corresponds to the maximum value for each row
    for i in range(len(df1)):
        if df1.iloc[i] == 0:
            r1.append(0)
        else:
            r1.append(comp_bot.iloc[i].idxmax(axis=1))
        
        if df2.iloc[i] == 0:
            r2.append(0)
        else:
            r2.append(comp_top.iloc[i].idxmax(axis=1))
            
        if df3.iloc[i] == 0:
            r3.append(0)
        else:
            r3.append(asx_bot.iloc[i].idxmax(axis=1))

        if df4.iloc[i] == 0:
            r4.append(0)
        else:
            r4.append(asy_bot.iloc[i].idxmax(axis=1))
            
        if df5.iloc[i] == 0:
            r5.append(0)
        else:
            r5.append(asx_top.iloc[i].idxmax(axis=1))

        if df6.iloc[i] == 0:
            r6.append(0)
        else:
            r6.append(asy_top.iloc[i].idxmax(axis=1))     
            
        if df7.iloc[i] == 0:
            r7.append(0)
        else:
            r7.append(ashear.iloc[i].idxmax(axis=1))    
    
    res_dict = {'comp_bot':r1, 'comp_top':r2,
                            'asx_bot':r3, 'asy_bot':r4,
                            'asx_top':r5, 'asy_top':r6,
                            'ashear':r7}
    res_key = ['comp_bot', 'comp_top', 'asx_bot', 'asy_bot', 'asx_top', 'asy_top', 'ashear']
    
    
    for i in res_key:
        res = pd.DataFrame(data={'TITLE':PlateID, i:res_dict[i]})
        fname = savepath + filename + "_" + i + ".txt"
        res.to_csv(fname, header=True, index=None, sep=" ")
    
    df = pd.DataFrame(data={'Plate ID':PlateID,
                            'comp_bot':r1, 'comp_top':r2,
                            'asx_bot':r3, 'asy_bot':r4,
                            'asx_top':r5, 'asy_top':r6,
                            'ashear':r7})
    filename = savepath + filename + ".csv"    
    df.to_csv(filename,index=False)

# Returns the maximum bar size of all stages
def MaxBarSize(savepath, all_files, filename):
    # extract load case names and number indices from .csv file
    LC = []
    numidx = []
    i =0
    for f in all_files:
        LC.append(os.path.basename(f.split('.')[0].replace('_results','')))
        numidx.append(i)
        i = i+1
    
    # read all results .csv files and compile into a dataframe based on result type (i.e. asx bottom)
    PlateID = pd.read_csv(all_files[0], header=0, engine='python').iloc[:,0]
    comp_bot = pd.concat((pd.read_csv(f, header=0, engine='python').iloc[:,1] for f in all_files),axis=1,sort=False)
    comp_top = pd.concat((pd.read_csv(f, header=0, engine='python').iloc[:,2] for f in all_files),axis=1,sort=False)
    asx_bot = pd.concat((pd.read_csv(f, header=0, engine='python').iloc[:,3] for f in all_files),axis=1,sort=False)
    asy_bot = pd.concat((pd.read_csv(f, header=0, engine='python').iloc[:,4] for f in all_files),axis=1,sort=False)
    asx_top = pd.concat((pd.read_csv(f, header=0, engine='python').iloc[:,5] for f in all_files),axis=1,sort=False)
    asy_top = pd.concat((pd.read_csv(f, header=0, engine='python').iloc[:,6] for f in all_files),axis=1,sort=False)
    ashear = pd.concat((pd.read_csv(f, header=0, engine='python').iloc[:,7] for f in all_files),axis=1,sort=False)
    
    # name columns according to load case name. Use = numidx to name columns according to load case number
    comp_bot.columns = numidx
    comp_top.columns = numidx
    asx_bot.columns = numidx
    asy_bot.columns = numidx
    asx_top.columns = numidx
    asy_top.columns = numidx
    ashear.columns = numidx
    """
    comp_bot.columns = LC
    comp_top.columns = LC
    asx_bot.columns = LC
    asy_bot.columns = LC
    asx_top.columns = LC
    asy_top.columns = LC
    ashear.columns = LC
    """
    
    crush_bins = [0, 21.6, 10000]
    crush_labels = ['a', 'b']
    
    ast_bins = [0, 0.001, 754, 1340, 2094, 3016, 4105, 5362, 6786, 8378, 10179, 12566, 1000000]
    ast_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']
    
    ashear_bins = [0, 0.001, 559, 993, 1257, 2234, 5027, 8936, 13963, 1000000]
    ashear_labels =['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
    
    for x in numidx:
        comp_bot[x] = pd.cut(comp_bot[x], bins = crush_bins, include_lowest=True, labels = crush_labels)
        comp_top[x] = pd.cut(comp_top[x], bins = crush_bins, include_lowest=True, labels = crush_labels)
        asx_bot[x] = pd.cut(asx_bot[x], bins = ast_bins, include_lowest=True, labels = ast_labels)
        asy_bot[x] = pd.cut(asy_bot[x], bins = ast_bins, include_lowest=True, labels = ast_labels)
        asx_top[x] = pd.cut(asx_top[x], bins = ast_bins, include_lowest=True, labels = ast_labels)
        asy_top[x] = pd.cut(asy_top[x], bins = ast_bins, include_lowest=True, labels = ast_labels)
        ashear[x] = pd.cut(ashear[x], bins = ashear_bins, include_lowest=True, labels = ashear_labels)
        
    cat_columns = comp_bot.select_dtypes(['category']).columns
    comp_bot[cat_columns] = comp_bot[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = comp_top.select_dtypes(['category']).columns
    comp_top[cat_columns] = comp_top[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = asx_bot.select_dtypes(['category']).columns
    asx_bot[cat_columns] = asx_bot[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = asy_bot.select_dtypes(['category']).columns
    asy_bot[cat_columns] = asy_bot[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = asx_top.select_dtypes(['category']).columns
    asx_top[cat_columns] = asx_top[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = asy_top.select_dtypes(['category']).columns
    asy_top[cat_columns] = asy_top[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = ashear.select_dtypes(['category']).columns
    ashear[cat_columns] = ashear[cat_columns].apply(lambda x: x.cat.codes)
    
    
    # find column index that corresponds to the maximum value for each row
    df1 = comp_bot.max(axis=1)
    df2 = comp_top.max(axis=1)
    df3 = asx_bot.max(axis=1)
    df4 = asy_bot.max(axis=1)
    df5 = asx_top.max(axis=1)
    df6 = asy_top.max(axis=1)
    df7 = ashear.max(axis=1)
    
    res_dict = {'comp_bot':df1, 'comp_top':df2,
                            'asx_bot':df3, 'asy_bot':df4,
                            'asx_top':df5, 'asy_top':df6,
                            'ashear':df7}
    res_key = ['comp_bot', 'comp_top', 'asx_bot', 'asy_bot', 'asx_top', 'asy_top', 'ashear']
    
    
    for i in res_key:
        res = pd.DataFrame(data={'TITLE':PlateID, i:res_dict[i]})
        fname = savepath + filename + "_" + i + ".txt"
        res.to_csv(fname, header=True, index=None, sep=" ")
        
    df = pd.DataFrame(data={'Plate ID':PlateID,
                            'comp_bot':df1, 'comp_top':df2,
                            'asx_bot':df3, 'asy_bot':df4,
                            'asx_top':df5, 'asy_top':df6,
                            'ashear':df7})
    
    filename = savepath + filename+".csv"   
    df.to_csv(filename,index=False)
    
    
# Returns the stage index with the maximum bar size from all stages
def MaxBarSizeStage(savepath, all_files,filename):    
    # extract load case names and number indices from .csv file
    LC = []
    numidx = []
    i =1
    for f in all_files:
        LC.append(os.path.basename(f.split('.')[0].replace('_results','')))
        numidx.append(i)
        i = i+1
    
    # read all results .csv files and compile into a dataframe based on result type (i.e. asx bottom)
    PlateID = pd.read_csv(all_files[0], header=0).iloc[:,0]
    comp_bot = pd.concat((pd.read_csv(f, header=0).iloc[:,1] for f in all_files),axis=1,sort=False)
    comp_top = pd.concat((pd.read_csv(f, header=0).iloc[:,2] for f in all_files),axis=1,sort=False)
    asx_bot = pd.concat((pd.read_csv(f, header=0).iloc[:,3] for f in all_files),axis=1,sort=False)
    asy_bot = pd.concat((pd.read_csv(f, header=0).iloc[:,4] for f in all_files),axis=1,sort=False)
    asx_top = pd.concat((pd.read_csv(f, header=0).iloc[:,5] for f in all_files),axis=1,sort=False)
    asy_top = pd.concat((pd.read_csv(f, header=0).iloc[:,6] for f in all_files),axis=1,sort=False)
    ashear = pd.concat((pd.read_csv(f, header=0).iloc[:,7] for f in all_files),axis=1,sort=False)
    
    # name columns according to load case name. Use = numidx to name columns according to load case number
    comp_bot.columns = numidx
    comp_top.columns = numidx
    asx_bot.columns = numidx
    asy_bot.columns = numidx
    asx_top.columns = numidx
    asy_top.columns = numidx
    ashear.columns = numidx
    """
    comp_bot.columns = LC
    comp_top.columns = LC
    asx_bot.columns = LC
    asy_bot.columns = LC
    asx_top.columns = LC
    asy_top.columns = LC
    ashear.columns = LC
    """
    
    crush_bins = [0, 21.6, 10000]
    crush_labels = ['a', 'b']
    
    ast_bins = [0, 0.001, 754, 1340, 2094, 3016, 4105, 5362, 6786, 8378, 10179, 12566, 1000000]
    ast_labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']
    
    ashear_bins = [0, 0.001, 559, 993, 1257, 2234, 5027, 8936, 13963, 1000000]
    ashear_labels =['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
    
    for x in numidx:
        comp_bot[x] = pd.cut(comp_bot[x], bins = crush_bins, include_lowest=True, labels = crush_labels)
        comp_top[x] = pd.cut(comp_top[x], bins = crush_bins, include_lowest=True, labels = crush_labels)
        asx_bot[x] = pd.cut(asx_bot[x], bins = ast_bins, include_lowest=True, labels = ast_labels)
        asy_bot[x] = pd.cut(asy_bot[x], bins = ast_bins, include_lowest=True, labels = ast_labels)
        asx_top[x] = pd.cut(asx_top[x], bins = ast_bins, include_lowest=True, labels = ast_labels)
        asy_top[x] = pd.cut(asy_top[x], bins = ast_bins, include_lowest=True, labels = ast_labels)
        ashear[x] = pd.cut(ashear[x], bins = ashear_bins, include_lowest=True, labels = ashear_labels)
        
    cat_columns = comp_bot.select_dtypes(['category']).columns
    comp_bot[cat_columns] = comp_bot[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = comp_top.select_dtypes(['category']).columns
    comp_top[cat_columns] = comp_top[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = asx_bot.select_dtypes(['category']).columns
    asx_bot[cat_columns] = asx_bot[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = asy_bot.select_dtypes(['category']).columns
    asy_bot[cat_columns] = asy_bot[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = asx_top.select_dtypes(['category']).columns
    asx_top[cat_columns] = asx_top[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = asy_top.select_dtypes(['category']).columns
    asy_top[cat_columns] = asy_top[cat_columns].apply(lambda x: x.cat.codes)
    
    cat_columns = ashear.select_dtypes(['category']).columns
    ashear[cat_columns] = ashear[cat_columns].apply(lambda x: x.cat.codes)
       
    df1 = comp_bot.max(axis=1)
    df2 = comp_top.max(axis=1)
    df3 = asx_bot.max(axis=1)
    df4 = asy_bot.max(axis=1)
    df5 = asx_top.max(axis=1)
    df6 = asy_top.max(axis=1)
    df7 = ashear.max(axis=1)
    
    r1 = []
    r2 = []
    r3 = []
    r4 = []
    r5 = []
    r6 = []
    r7 = []

    # find column index that corresponds to the maximum value for each row
    for i in range(len(df1)):
        if df1.iloc[i] == 0:
            r1.append(0)
        else:
            r1.append(comp_bot.iloc[i].idxmax(axis=1))
        
        if df2.iloc[i] == 0:
            r2.append(0)
        else:
            r2.append(comp_top.iloc[i].idxmax(axis=1))
            
        if df3.iloc[i] == 0:
            r3.append(0)
        else:
            r3.append(asx_bot.iloc[i].idxmax(axis=1))

        if df4.iloc[i] == 0:
            r4.append(0)
        else:
            r4.append(asy_bot.iloc[i].idxmax(axis=1))
            
        if df5.iloc[i] == 0:
            r5.append(0)
        else:
            r5.append(asx_top.iloc[i].idxmax(axis=1))

        if df6.iloc[i] == 0:
            r6.append(0)
        else:
            r6.append(asy_top.iloc[i].idxmax(axis=1))     
            
        if df7.iloc[i] == 0:
            r7.append(0)
        else:
            r7.append(ashear.iloc[i].idxmax(axis=1))           
                       
    res_dict = {'comp_bot':r1, 'comp_top':r2,
                            'asx_bot':r3, 'asy_bot':r4,
                            'asx_top':r5, 'asy_top':r6,
                            'ashear':r7}
    res_key = ['comp_bot', 'comp_top', 'asx_bot', 'asy_bot', 'asx_top', 'asy_top', 'ashear']
    
    
    for i in res_key:
        res = pd.DataFrame(data={'TITLE':PlateID, i:res_dict[i]})
        fname = savepath + filename + "_" + i + ".txt"
        res.to_csv(fname, header=True, index=None, sep=" ")
            
    df = pd.DataFrame(data={'Plate ID':PlateID,
                            'comp_bot':r1, 'comp_top':r2,
                            'asx_bot':r3, 'asy_bot':r4,
                            'asx_top':r5, 'asy_top':r6,
                            'ashear':r7})
    
    filename = savepath + filename + ".csv"    
    df.to_csv(filename,index=False)