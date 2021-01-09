# -*- coding: utf-8 -*-

import os
import sys
import ctypes
import St7API
import pandas as pd
import re
import numpy as np

def explain_error(ErrorCode):
    """
    Returns St7API error code in a string

    Parameters
    ----------
    ErrorCode : INTEGER
        Result of API action that is different from 0

    Raises
    ------
    Exception
        If the exception is found in the API list, the explanation is returned
        Otrherwise unknown error

    Returns
    -------
    ErrorCode : INTEGER
        Returns the input code

    """

    ErrorString = ctypes.create_string_buffer(St7API.kMaxStrLen)
        
	# Attempt to get API error string
    iErr = St7API.St7GetAPIErrorString(ErrorCode, ErrorString,
                                       St7API.kMaxStrLen)

	# If that failed, attempt to retrieve a solver error string
    if iErr:
        iErr = St7API.St7GetSolverErrorString(ErrorCode, ErrorString,
                                              St7API.kMaxStrLen)

    if not iErr:
        raise Exception('%s (%d)' % (ErrorString.value, ErrorCode))
    else:
        raise Exception('An unknown error occured (%d)' % ErrorCode)

    return ErrorCode


def get_model_info(modelname_bt, tempfolder_bt, GroupsToKeep='ALL'):
    """
    Looks at the Model information and returns the Id of the groups we want the
    Beams parameters to be changed

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    GroupsToKeep : LIST
        List of Parent Groups to keep
        default not assigned and all groups kept

    Returns
    -------
    groupID : LIST
        List of integer of the groups to modify
    enTots: DICT
        Total number of 'Nodes', 'Beams', 'Plates', 'Bricks'
    """
   
    # Opening Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)
    
    # Create variables to store the info
    # model title, author name, group numbers and names
    modTitle = ctypes.create_string_buffer(St7API.kMaxStrLen) 
    modAuth = ctypes.create_string_buffer(St7API.kMaxStrLen)
    numgroups = ctypes.c_long()
    groupname = ctypes.create_string_buffer(St7API.kMaxStrLen)
    groupparentId = ctypes.c_long()
    
    # Getting Title, Author and number of groups
    ret = St7API.St7GetTitle(1, St7API.TITLEModel, modTitle, St7API.kMaxStrLen)
    if ret != 0 :
        explain_error(ret)

    ret = St7API.St7GetTitle(1, St7API.TITLEAuthor, modAuth, St7API.kMaxStrLen)
    if ret != 0:
        explain_error(ret)

    ret = St7API.St7GetNumGroups(1, numgroups)
    if ret != 0:
        explain_error(ret)

    print('Title:  ' + modTitle.value.decode())
    print('Author: ' + modAuth.value.decode())
    print('Number of groups: %d' %numgroups.value)
    
    # Store the information about the groups
    groupID = []
    groupname_List = []
    if GroupsToKeep != 'ALL':
        for ind in range(1, numgroups.value+1):
        	St7API.St7GetGroupIDName(1, ind, groupname, St7API.kMaxStrLen)
        	St7API.St7GetGroupParent(1, ind, groupparentId)
        	if groupname.value.decode() in GroupsToKeep:
        	    groupID.append(ind)
        	    groupname_List.append(groupname.value.decode())
        
        print('Considering groups: ')
        for ind, item in enumerate(groupID):
            print('Name: %s ID: %d' % (groupname_List[ind], item))
    else:
        print('Considering ALL groups')
        for ind in range(1, numgroups.value+1):
        	groupID.append(ind)
    
    EntTypes = ((St7API.tyNODE, 'Nodes'), (St7API.tyBEAM, 'Beams'),
            (St7API.tyPLATE, 'Plates'), (St7API.tyBRICK, 'Bricks'))

    nEnt = ctypes.c_int()
    entTots = {}
    print('Entity Totals')
    for (entTy, entName) in EntTypes:
        ret = St7API.St7GetTotal(1, entTy, nEnt)
        if ret != 0:
            explain_error(ret)
            St7API.St7Release()
            print('Cannot get number of ' + entName)
            sys.exit(1)
        else:
            entTots[entName] = nEnt.value
            print('%s %d' %(entName, nEnt.value))

    St7API.St7CloseFile(1)

    return groupID, entTots

def assign_plates_results(modelname_bt, tempfolder_bt, fileOut_bt, DF):

    print('Start assigning post-processing results to plates as heat source')
    
    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)
    
    # Variables to store information
    NumLoadCases = ctypes.c_long()
    PlateNum = ctypes.c_long()
    LoadCaseID = ctypes.c_long()
    CaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)
    LoadCaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)

    
    # Get first column of dataframe, containing Plate IDs
    PlateID = DF.iloc[:,0]
    PlateID = pd.to_numeric(PlateID, errors='coerce')
    ResultNames = DF.columns[1:]
    ResultIDs = []
    
    # Add load cases
    for i in ResultNames:
        CaseName = i
        St7API.St7NewLoadCase(1, CaseName.encode())
        
    # Get total number of load cases
    St7API.St7GetNumLoadCase(1, NumLoadCases)
    # Match load case ID with load case name
    for j in range(1, NumLoadCases.value+1):
        St7API.St7GetLoadCaseName(1, j, LoadCaseName, St7API.kMaxStrLen)
        if LoadCaseName.value.decode() in ResultNames:
            ResultIDs.append(j)
    
    for k in range(len(ResultIDs)):
        
        LoadCaseID = ResultIDs[k]
        print('Assigning ' + str(ResultNames[k]))
        for ind, platePos in enumerate(PlateID):
            PlateNum = int(platePos)
            ResultVal = ctypes.c_double(DF.iloc[ind, k+1])
            
            St7API.St7SetPlateHeatSource1(1, PlateNum, LoadCaseID, ResultVal)
    
    # Saving the new model
    ret = St7API.St7SaveFileTo(1, fileOut_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7CloseFile(1)
        print('Cannot open file')
        St7API.St7Release()
        sys.exit(1)
    
    
    print('Complete')
    St7API.St7CloseFile(1)

    return ret

def assign_plates_prop(modelname_bt, tempfolder_bt, fileOut_bt, DF, groupID,
                       numPlates, solvebool):
    """
    Assign Properties to Plates

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    fileOut_bt : BYTE
        Encoded Output model name
    DF : DATAFRAME
        Pandas DataFrame with properties description with columns:
        'Property Name', 'PlateType', 'Material', 'Modulus E1', 'Modulus E2',
        'Modulus E3', 'Poisson I12', 'Poisson I23', 'Poisson I31',
        'Shear Modulus G12', 'Shear Modulus G23', 'Shear Modulus G31',
        'Thermal Expansion A1', 'Thermal Expansion A2', 'Thermal Expansion A3',
        'Damping Ratio', 'Density', 'Viscous Damping', 'Specific Heat',
        'Conductivity K1', 'Conductivity K2', 'Modulus', 'Poisson Ratio',
        'Thermal Expansion', 'Conductivity', 'Membrane Thickness',
        'Membrane Bending'
    groupID : LIST
        List of integer of the groups to modify
    numPlates : INTEGER
        Number of plates

    Returns
    -------
    ret : INTEGER
        Return code final API

    """
    
    print('Start assigning properties to plates')
    
    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)
    
    
    EsPlates = DF['Property Name']
    print('%d plates will be assigned new properties' % len(EsPlates))

    # Variables to store information
    LongArray4 = ctypes.c_long * 4
    DblArray18 = ctypes.c_double * 18
    DblArray8 = ctypes.c_double * 8
    DblArray2 =ctypes.c_double *2
    numProperties = LongArray4()
    LastProperties = LongArray4()
    OrthoArray = DblArray18()
    IsoArray = DblArray8()
    ThickArray = DblArray2()
    
    # Dictionnary of Strand7 key words
    plateTypeDict = {'2D Plane Stress': St7API.kPlateTypePlaneStress,
                     '2D Plane Strain': St7API.kPlateTypePlaneStrain,
                     'Axisymmetric': St7API.kPlateTypeAxisymmetric,
                     'Plate/Shell': St7API.kPlateTypePlateShell,
                     'Shear Panel': St7API.kPlateTypeShearPanel,
                     '3D Membrane': St7API.kPlateTypeMembrane,
                     'Load Patch': St7API.kPlateTypeLoadPatch}
    
    MaterialDict = {'Isotropic': St7API.kMaterialTypeIsotropic,
                    'Orthotropic': St7API.kMaterialTypeOrthotropic,
                    'Anisotropic': St7API.kMaterialTypeAnisotropic,
                    'Laminate': St7API.kMaterialTypeLaminate,
                    'Rubber': St7API.kMaterialTypeRubber}
    
    
    # Get the number of properties already assigned
    ret = St7API.St7GetTotalProperties(1, numProperties, LastProperties)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot retrieve properties')
        sys.exit(1)

    for ind, ID in enumerate(EsPlates):
        
        plateID = int(ID)
        propNum = plateID + numPlates
        propName = str(propNum).encode()
        
        try:
            plateType = plateTypeDict[DF.loc[ind, 'PlateType']]
        except KeyError:
            print(DF.loc[ind, 'PlateType'] + ' not found in Plate type list')
        try:
            MaterialType = MaterialDict[DF.loc[ind, 'Material']]
        except KeyError:
            print(DF.loc[ind, 'Material'] + ' not found in material list')
        
        St7API.St7NewPlateProperty(1, propNum, plateType, MaterialType, propName)
            
        if MaterialType == St7API.kMaterialTypeOrthotropic:
            OrthoArray[St7API.ipPlateOrthoModulus1] = DF.loc[ind, 'Modulus E1']
            OrthoArray[St7API.ipPlateOrthoModulus2] = DF.loc[ind, 'Modulus E2']
            OrthoArray[St7API.ipPlateOrthoModulus3] = DF.loc[ind, 'Modulus E3']
            OrthoArray[St7API.ipPlateOrthoShear12] = DF.loc[ind, 'Shear Modulus G12']
            OrthoArray[St7API.ipPlateOrthoShear23] = DF.loc[ind, 'Shear Modulus G23']
            OrthoArray[St7API.ipPlateOrthoShear31] = DF.loc[ind, 'Shear Modulus G31']
            OrthoArray[St7API.ipPlateOrthoPoisson12] = DF.loc[ind, 'Poisson I12']
            OrthoArray[St7API.ipPlateOrthoPoisson23] = DF.loc[ind, 'Poisson I23']
            OrthoArray[St7API.ipPlateOrthoPoisson31] = DF.loc[ind, 'Poisson I31']
            OrthoArray[St7API.ipPlateOrthoDensity] = DF.loc[ind, 'Density']
            OrthoArray[St7API.ipPlateOrthoAlpha1] = DF.loc[ind, 'Thermal Expansion A1']
            OrthoArray[St7API.ipPlateOrthoAlpha2] = DF.loc[ind, 'Thermal Expansion A2']
            OrthoArray[St7API.ipPlateOrthoAlpha3] = DF.loc[ind, 'Thermal Expansion A3']
            OrthoArray[St7API.ipPlateOrthoViscosity] = DF.loc[ind, 'Viscous Damping']
            OrthoArray[St7API.ipPlateOrthoDampingRatio] = DF.loc[ind, 'Damping Ratio']
            OrthoArray[St7API.ipPlateOrthoConductivity1] = DF.loc[ind, 'Conductivity K1']
            OrthoArray[St7API.ipPlateOrthoConductivity2] = DF.loc[ind, 'Conductivity K2']
            OrthoArray[St7API.ipPlateOrthoSpecificHeat] = DF.loc[ind, 'Specific Heat']
            St7API.St7SetPlateOrthotropicMaterial(1, propNum, OrthoArray)
    
        if MaterialType == St7API.kMaterialTypeIsotropic:
            IsoArray[St7API.ipPlateIsoModulus] = DF.loc[ind, 'Modulus']
            IsoArray[St7API.ipPlateIsoPoisson] = DF.loc[ind, 'Poisson Ratio']
            IsoArray[St7API.ipPlateIsoDensity] = DF.loc[ind, 'Density']
            IsoArray[St7API.ipPlateIsoAlpha] = DF.loc[ind, 'Thermal Expansion']
            IsoArray[St7API.ipPlateIsoViscosity] = DF.loc[ind, 'Viscous Damping']
            IsoArray[St7API.ipPlateIsoDampingRatio] = DF.loc[ind, 'Damping Ratio']
            IsoArray[St7API.ipPlateIsoConductivity] = DF.loc[ind, 'Conductivity']
            IsoArray[St7API.ipPlateIsoSpecificHeat] = DF.loc[ind,'Specific Heat']
            St7API.St7SetPlateIsotropicMaterial(1, propNum, IsoArray)
    
        ThickArray[0] = DF.loc[ind, 'Membrane Thickness']
        ThickArray[1] = DF.loc[ind, 'Membrane Bending']
        St7API.St7SetPlateThickness(1, propNum, ThickArray)
        St7API.St7SetElementProperty(1, St7API.tyPLATE, plateID, propNum)
    
    ret = St7API.St7SaveFileTo(1, fileOut_bt)
    
    # Saving the new model

    if ret != 0:
        explain_error(ret)
        St7API.St7CloseFile(1)
        print('Cannot open file')
        St7API.St7Release()
        sys.exit(1)
    
    print('Plate properties assigned')
    St7API.St7CloseFile(1)
    
    if solvebool == True:
        # Open new model and solve and save
        modelname = modelname_bt.decode()
        Foldername = os.path.dirname(modelname) + "\\"
        Foldername_bt = Foldername.encode()
        St7API.St7OpenFile(1, fileOut_bt, Foldername_bt)
        St7API.St7RunSolver(1, St7API.stNonlinearStaticSolver, St7API.smNormalCloseRun, St7API.btTrue)
        St7API.St7SaveFile(1)
        St7API.St7CloseFile(1)
    
    return ret

def modify_beam_stiffnessTab(modelname_bt, tempfolder_bt, fileOut_bt, DF,
                             groupID, numBeams):
    """
    Modify Beam Stiffness Parameters

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    fileOut_bt : BYTE
        Encoded Saved Model file name
    DF : DATAFRAME
        Pandas Dataframe with new beams parameters, columns name must match:
        'SA1', 'SA2', 'Area', 'I11', 'I22', 'J', 'Mass'
    groupID : LIST
        List of integer of the groups to modify
    numBeams : INTEGER
        Total number of Beams

    Returns
    -------
    ret : INTEGER
        Return code API

    """

    print('Start modifying stiffness parameters for %d beams' % numBeams)

    # Opening Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)

    # Set API storage values
    DblArray7 = ctypes.c_double * 7
    BeamSecFactor = DblArray7()
    GroupBeam = ctypes.c_long()
    Beam_SectionFactors = ['SA1', 'SA2', 'Area', 'I11', 'I22', 'J', 'Mass']
    
    # Select Beams ID
    BeamNum = []
    for ind in range(1, numBeams + 1):
    	St7API.St7GetElementGroup(1, St7API.tyBEAM, ind, GroupBeam)
    	if GroupBeam.value in groupID:
    		BeamNum.append(ind)
    print('%d beams will be modified' % len(BeamNum))

    if len(BeamNum) > len(DF):
        print('Number of properties not matching number of beams')
        print('Model has %d beams and the csv contains %d properties'
              % (len(BeamNum), len(DF)))
        St7API.St7CloseFile(1)
        St7API.St7Release()
        sys.exit(1)
    if len(DF) > len(BeamNum):
        print('Number of properties not matching number of beams')
        print('Model has %d plates and the csv contains %d properties'
              % (len(BeamNum), len(DF)))
        print('Only the first %d will be considered' % len(BeamNum))

    # Modify Beams
    for ind, beamPos in enumerate(BeamNum):
        St7API.St7GetBeamSectionFactor7(1, beamPos, BeamSecFactor)
        for colname in DF.columns:
            BeamSecFactor[
                Beam_SectionFactors.index(colname)] = DF.iloc[
                    ind, list(DF.columns).index(colname)]
        St7API.St7SetBeamSectionFactor7(1, beamPos, BeamSecFactor)
    
    # Saving Model in the new file
    ret = St7API.St7SaveFileTo(1, fileOut_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7CloseFile(1)
        print('Cannot open file')
        St7API.St7Release()
        sys.exit(1)
    
    St7API.St7CloseFile(1)
    
    print('Done')

    return ret

def export_beam_shearinputs(modelname_bt, tempfolder_bt, resultfile_bt,
                          groupID, numBeams, ResultAxis='Local'):
    """
    Extract Beam Force information for a combined result file

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    resultfile_bt : BYTE
        Encoded Result file name
    groupID : LIST
        List of integer of the groups to modify
    numBeams : INTEGER
        Total number of Beams
    ResultAxis: STRING
        DEFAULT is 'Local'.
        Define axis the data is extracted on Local, Global, Principal

    Returns
    -------
    ret : INTEGER
        Return code API

    """
    print('Start extract beam results')

    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)
        
    modelname = modelname_bt.decode()
    Foldername = os.path.dirname(modelname) + "\\"
    
    # Open Result file
    numPrimary = ctypes.c_long()
    numSecondary = ctypes.c_long()
    CaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)

    
    ret = St7API.St7OpenResultFile(1, resultfile_bt, ''.encode(), True,
    	numPrimary, numSecondary)
    
    if ret != 0:
        explain_error(ret)
        print('Not able to open result file')
        St7API.St7CloseFile(1)
        print('Releasing API')
        St7API.St7Release()

    print('%d primary case(s) found' % numPrimary.value)

    CaseName_list = []
    for ind in range(1, numPrimary.value + 1):
        St7API.St7GetResultCaseName(1, ind, CaseName, St7API.kMaxStrLen)
        CaseName_list.append(CaseName.value.decode())
        print(CaseName.value.decode())

    # Set API storage values
    GroupBeam = ctypes.c_long()
    DblArrayRes = ctypes.c_double * 12
    BeamRes = DblArrayRes()
    numColumns = ctypes.c_long()
    
    BeamPropID = ctypes.c_long()
    
    DblArray = ctypes.c_double * St7API.kNumBeamSectionData
    PropSectionData = DblArray()
    PropIntegers = ctypes.c_long()
    PropBeamMaterial = ctypes.c_double()
    
    # Select Beams ID
    BeamNum = []
    for ind in range(1, numBeams + 1):
    	St7API.St7GetElementGroup(1, St7API.tyBEAM, ind, GroupBeam)
    	if GroupBeam.value in groupID:
    		BeamNum.append(ind)
    print('%d beams will be extracted' % len(BeamNum))

    # dictionnary matching axis to ResultSubType
    subtype = {'Local': St7API.stBeamLocal,
               'Principal': St7API.stBeamPrincipal,
               'Global': St7API.stBeamGlobal}

    # Get Cases data from model
    for ind, casename in enumerate(CaseName_list):
        print('Start extracting data for case number %d %s'
              % (ind+1, casename))

        # List to store data   
        BeamId = []
        BeamEnd = []
        ShearForce1 = []
        BendingMoment1 = []
        ShearForce2 = []
        BendingMoment2 = []
        AxialForce = []
        Torque = []
        Depth = []
    
        for beamPos in BeamNum:
            St7API.St7GetBeamResultEndPos(1, St7API.rtBeamForce,
                                          subtype[ResultAxis.capitalize()],
                                          beamPos, ind+1, numColumns, BeamRes)
            
            St7API.St7GetElementProperty(1, St7API.tyBEAM, beamPos, BeamPropID)
            
            St7API.St7GetBeamPropertyData(1, BeamPropID.value, PropIntegers, PropSectionData, PropBeamMaterial)
            
            for endpos in [1, 2]:
                # from Strand7 API user manual
                # Beam Results section page 1073
                indpos = (endpos - 1) * numColumns.value
                BeamId.append(beamPos)
                BeamEnd.append(endpos)
                ShearForce1.append(BeamRes[indpos + St7API.ipBeamSF1])
                BendingMoment1.append(BeamRes[indpos + St7API.ipBeamBM1])
                ShearForce2.append(BeamRes[indpos + St7API.ipBeamSF2])
                BendingMoment2.append(BeamRes[indpos + St7API.ipBeamBM2])
                AxialForce.append(BeamRes[indpos + St7API.ipBeamAxialF])
                Torque.append(BeamRes[indpos + St7API.ipBeamTorque])
                Depth.append(PropSectionData[St7API.ipD2])
                
        # Create a dataframe to store the output data
        DF = pd.DataFrame(data={'BeamId': BeamId,
                                'Depth (m)' : Depth,
                                'Shear Force (MN)': ShearForce2,
                                'Bending Moment (MN.m)': BendingMoment2,
                                'Axial Force (MN)': AxialForce,
                                },
                          columns=['BeamId', 
                                   'Depth (m)',
                                   'Shear Force (MN)',
                                   'Bending Moment (MN.m)',
                                   'Axial Force (MN)'])
                
        stgname = casename.split("[")[1].split(']')[0]
        x = re.search('Reset',stgname) 
        
        if x:
            print('skipped reset stage')
        else:
            csvOutFile = Foldername + 'shearinput_' + stgname + '.csv'
            print('Saved in csv file ' + csvOutFile)
            DF.to_csv(csvOutFile, index=False)
    
    ret = St7API.St7CloseResultFile(1)
    if ret == 0:
        print('Result File closed')
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')

    return ret

def export_beam_shearinputs_mid(modelname_bt, tempfolder_bt, resultfile_bt,
                          groupID, numBeams, ResultAxis='Local'):
    """
    Extract Beam Force information for a combined result file

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    resultfile_bt : BYTE
        Encoded Result file name
    groupID : LIST
        List of integer of the groups to modify
    numBeams : INTEGER
        Total number of Beams
    ResultAxis: STRING
        DEFAULT is 'Local'.
        Define axis the data is extracted on Local, Global, Principal

    Returns
    -------
    ret : INTEGER
        Return code API

    """
    print('Start extract beam results')

    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)
        
    modelname = modelname_bt.decode()
    Foldername = os.path.dirname(modelname) + "\\"
    
    # Open Result file
    numPrimary = ctypes.c_long()
    numSecondary = ctypes.c_long()
    CaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)

    
    ret = St7API.St7OpenResultFile(1, resultfile_bt, ''.encode(), True,
    	numPrimary, numSecondary)
    
    if ret != 0:
        explain_error(ret)
        print('Not able to open result file')
        St7API.St7CloseFile(1)
        print('Releasing API')
        St7API.St7Release()

    print('%d primary case(s) found' % numPrimary.value)

    CaseName_list = []
    for ind in range(1, numPrimary.value + 1):
        St7API.St7GetResultCaseName(1, ind, CaseName, St7API.kMaxStrLen)
        CaseName_list.append(CaseName.value.decode())
        print(CaseName.value.decode())

    # Set API storage values
    GroupBeam = ctypes.c_long()
    DblArrayRes = ctypes.c_double * 12
    BeamRes = DblArrayRes()
    numColumns = ctypes.c_long()
    
    BeamPropID = ctypes.c_long()
    
    DblArray = ctypes.c_double * St7API.kNumBeamSectionData
    PropSectionData = DblArray()
    PropIntegers = ctypes.c_long()
    PropBeamMaterial = ctypes.c_double()
    
    # Select Beams ID
    BeamNum = []
    for ind in range(1, numBeams + 1):
    	St7API.St7GetElementGroup(1, St7API.tyBEAM, ind, GroupBeam)
    	if GroupBeam.value in groupID:
    		BeamNum.append(ind)
    print('%d beams will be extracted' % len(BeamNum))

    # dictionnary matching axis to ResultSubType
    subtype = {'Local': St7API.stBeamLocal,
               'Principal': St7API.stBeamPrincipal,
               'Global': St7API.stBeamGlobal}

    # Get Cases data from model
    for ind, casename in enumerate(CaseName_list):
        print('Start extracting data for case number %d %s'
              % (ind+1, casename))

        # List to store data   
        BeamId = []
        ShearForce2 = []
        BendingMoment2 = []
        AxialForce = []
        Depth = []
    
        for beamPos in BeamNum:
            
            St7API.St7GetBeamResultEndPos(1, St7API.rtBeamForce,
                                          subtype[ResultAxis.capitalize()],
                                          beamPos, ind+1, numColumns, BeamRes)
            
            St7API.St7GetElementProperty(1, St7API.tyBEAM, beamPos, BeamPropID)
            
            St7API.St7GetBeamPropertyData(1, BeamPropID.value, PropIntegers, PropSectionData, PropBeamMaterial)
            
            BeamId.append(beamPos)
            
            Vav = []
            BMav = []
            Nav = []
            Dav = []
            
            for endpos in [1, 2]:
                # from Strand7 API user manual
                # Beam Results section page 1073
                indpos = (endpos - 1) * numColumns.value

                Vav.append(BeamRes[indpos + St7API.ipBeamSF2])
                BMav.append(BeamRes[indpos + St7API.ipBeamBM2])
                Nav.append(BeamRes[indpos + St7API.ipBeamAxialF])
                Dav.append(PropSectionData[St7API.ipD2])
            
            ShearForce2.append(np.average(Vav))
            BendingMoment2.append(np.average(BMav))
            AxialForce.append(np.average(Nav))
            Depth.append(np.average(Dav))
        
        
        # Create a dataframe to store the output data
        DF = pd.DataFrame(data={'BeamId': BeamId,
                                'Depth (m)' : Depth,
                                'Shear Force (MN)': ShearForce2,
                                'Bending Moment (MN.m)': BendingMoment2,
                                'Axial Force (MN)': AxialForce,
                                },
                          columns=['BeamId', 
                                   'Depth (m)',
                                   'Shear Force (MN)',
                                   'Bending Moment (MN.m)',
                                   'Axial Force (MN)'])
                
        stgname = casename.split("[")[1].split(']')[0]
        x = re.search('Reset',stgname) 
        
        if x:
            print('skipped reset stage')
        else:
            csvOutFile = Foldername + 'shearinput_' + stgname + '.csv'
            print('Saved in csv file ' + csvOutFile)
            DF.to_csv(csvOutFile, index=False)
    
    ret = St7API.St7CloseResultFile(1)
    if ret == 0:
        print('Result File closed')
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')

    return ret
    
def export_beam_forceData(modelname_bt, tempfolder_bt, resultfile_bt,
                          groupID, numBeams, ResultAxis='Local'):
    """
    Extract Beam Force information for a combined result file

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    resultfile_bt : BYTE
        Encoded Result file name
    groupID : LIST
        List of integer of the groups to modify
    numBeams : INTEGER
        Total number of Beams
    ResultAxis: STRING
        DEFAULT is 'Local'.
        Define axis the data is extracted on Local, Global, Principal

    Returns
    -------
    ret : INTEGER
        Return code API

    """
    print('Start extract beam results')

    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)
        
    modelname = modelname_bt.decode()
    Foldername = os.path.dirname(modelname) + "\\"
    
    # Open Result file
    numPrimary = ctypes.c_long()
    numSecondary = ctypes.c_long()
    CaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)

    
    ret = St7API.St7OpenResultFile(1, resultfile_bt, ''.encode(), True,
    	numPrimary, numSecondary)
    
    if ret != 0:
        explain_error(ret)
        print('Not able to open result file')
        St7API.St7CloseFile(1)
        print('Releasing API')
        St7API.St7Release()

    print('%d primary case(s) found' % numPrimary.value)

    CaseName_list = []
    for ind in range(1, numPrimary.value + 1):
        St7API.St7GetResultCaseName(1, ind, CaseName, St7API.kMaxStrLen)
        CaseName_list.append(CaseName.value.decode())
        print(CaseName.value.decode())

    # Set API storage values
    GroupBeam = ctypes.c_long()
    DblArrayRes = ctypes.c_double * 12
    BeamRes = DblArrayRes()
    numColumns = ctypes.c_long()
    
    # Select Beams ID
    BeamNum = []
    for ind in range(1, numBeams + 1):
    	St7API.St7GetElementGroup(1, St7API.tyBEAM, ind, GroupBeam)
    	if GroupBeam.value in groupID:
    		BeamNum.append(ind)
    print('%d beams will be extracted' % len(BeamNum))

    # dictionnary matching axis to ResultSubType
    subtype = {'Local': St7API.stBeamLocal,
               'Principal': St7API.stBeamPrincipal,
               'Global': St7API.stBeamGlobal}

    # Get Cases data from model
    for ind, casename in enumerate(CaseName_list):
        print('Start extracting data for case number %d %s'
              % (ind+1, casename))

        # List to store data   
        BeamId = []
        BeamEnd = []
        ShearForce1 = []
        BendingMoment1 = []
        ShearForce2 = []
        BendingMoment2 = []
        AxialForce = []
        Torque = []
    
        for beamPos in BeamNum:
            St7API.St7GetBeamResultEndPos(1, St7API.rtBeamForce,
                                          subtype[ResultAxis.capitalize()],
                                          beamPos, ind+1, numColumns, BeamRes)
            for endpos in [1, 2]:
                # from Strand7 API user manual
                # Beam Results section page 1073
                indpos = (endpos - 1) * numColumns.value
                BeamId.append(beamPos)
                BeamEnd.append(endpos)
                ShearForce1.append(BeamRes[indpos + St7API.ipBeamSF1])
                BendingMoment1.append(BeamRes[indpos + St7API.ipBeamBM1])
                ShearForce2.append(BeamRes[indpos + St7API.ipBeamSF2])
                BendingMoment2.append(BeamRes[indpos + St7API.ipBeamBM2])
                AxialForce.append(BeamRes[indpos + St7API.ipBeamAxialF])
                Torque.append(BeamRes[indpos + St7API.ipBeamTorque])
        
        # Create a dataframe to store the output data
        DF = pd.DataFrame(data={'BeamId': BeamId,
                                'End': BeamEnd,
                                'Shear Force 1 (MN)': ShearForce1,
                                'Bending Moment 1 (MN.m)': BendingMoment1,
                                'Shear Force 2 (MN)': ShearForce2,
                                'Bending Moment 2 (MN.m)': BendingMoment2,
                                'Axial Force (MN)': AxialForce,
                                'Torque (MN.m)': Torque
                                },
                          columns=['BeamId','End', 'Shear Force 1 (MN)',
                                   'Bending Moment 1 (MN.m)',
                                   'Shear Force 2 (MN)',
                                   'Bending Moment 2 (MN.m)',
                                   'Axial Force (MN)', 'Torque (MN.m)'])
                
        stgname = casename.split("[")[1].split(']')[0]
        x = re.search('Reset',stgname) 
        
        if x:
            print('skipped reset stage')
        else:
            csvOutFile = Foldername + 'beamresults_' + stgname + '.csv'
            print('Saved in csv file ' + csvOutFile)
            DF.to_csv(csvOutFile, index=False)
    
    ret = St7API.St7CloseResultFile(1)
    if ret == 0:
        print('Result File closed')
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')

    return ret

def export_shearinputs(modelname_bt, tempfolder_bt, resultfile_bt,
                                 groupID, numPlates, minthickness, ResultAxis='Local',
                                 ResultLocation='Centroid',
                                 PlateSurf='Midplane'):
    """
    Extract Beam Force information for a combined result file

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    resultfile_bt : BYTE
        Encoded Result file name
    groupID : LIST
        List of integer of the groups to modify
    numPlates : INTEGER
        Total number of Plates
    ResultAxis: STRING, optional
        Define axis the data is extracted on Local or Global
        DEFAULT is 'Local'.
    ResultLocation: STRING, optional
        Result sampling location
        DEFAULT is 'Centroid'
        Centroid, Gauss, NodeAverageSame, NodeAverageAll, NodeAverageSame
    PlateSurf : STRING, optional
        Plate Surface to extract data
        DEFAULT is 'Midplane
        Midplane, Zplus or Zminus

    Returns
    -------
    ret : INTEGER
        Return code API

    """
    
    print('Start extract plate results')

    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)

    modelname = modelname_bt.decode()
    Foldername = os.path.dirname(modelname) + "\\"
    
    # Open Result file
    numPrimary = ctypes.c_long()
    numSecondary = ctypes.c_long()
    CaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)
    
    ret = St7API.St7OpenResultFile(1, resultfile_bt, ''.encode(), True,
    	numPrimary, numSecondary)
    
    if ret != 0:
        explain_error(ret)
        print('Not able to open result file')
        St7API.St7CloseFile(1)
        print('Releasing API')
        St7API.St7Release()

    print('%d primary case(s) found' % numPrimary.value)

    CaseName_list = []
    for ind in range(1, numPrimary.value + 1):
        St7API.St7GetResultCaseName(1, ind, CaseName, St7API.kMaxStrLen)
        CaseName_list.append(CaseName.value.decode())
        print(CaseName.value.decode())

    # Set API storage values
    GroupPlate = ctypes.c_long()
    DblArrayRes = ctypes.c_double * 6
    ForceRes = DblArrayRes()
    MomentRes = DblArrayRes()
    StressRes = DblArrayRes()
    DblArrayRes2 = ctypes.c_double * 11
    CombinedRes = DblArrayRes2()
    numPoints = ctypes.c_long()
    numColumns = ctypes.c_long()
    numPoints2 = ctypes.c_long()
    numColumns2 = ctypes.c_long()
    PlateArea = ctypes.c_double()
    PlateThickness = ctypes.c_double()
    PlatePropID = ctypes.c_long()
    
    # Select Plates ID
    PlateNum = []
    
    for ind in range(1, numPlates+1):
    	St7API.St7GetElementGroup(1, St7API.tyPLATE, ind, GroupPlate)
    	if GroupPlate.value in groupID:
    		PlateNum.append(ind)
    print('%d plates will be extracted' % len(PlateNum))

    # dictionnary for options
    subtype = {'Local': St7API.stPlateLocal,
               'Global': St7API.stPlateGlobal}
    
    sampleLocation = {'Centroid': St7API.AtCentroid,
                      'Gauss': St7API.AtGaussPoints,
                      'Nodesaveragenever': St7API.AtNodesAverageNever,
                      'Nodesaverageall': St7API.AtNodesAverageAll,
                      'Nodesaveragesame': St7API.AtNodesAverageSame}
    
    PlateSurface = {'Midplane': St7API.psPlateMidPlane,
                    'Zplus': St7API.psPlateZPlus,
                    'Zminus': St7API.psPlateZMinus}
    
    StgNames = []
        
    for ind, casename in enumerate(CaseName_list):
        print('Start extracting data for case number %d %s' % (ind, casename))
    
        PlateId = []
        PlateT = []
        PlateA = []
        ForceXX = []
        ForceYY = []
        ForceXY = []
        ForceXZ = []
        ForceYZ = []
        MomentXX = []
        MomentYY = []
        MomentXY = []
        StressXX = []
        StressYY = []
        StressXY = []
        Angle11xx = []
        
        for platePos in PlateNum:
          
            # Extract plate thickness
            St7API.St7GetElementProperty(1, St7API.tyPLATE, platePos, PlatePropID)
            St7API.St7GetPlateThickness(1, PlatePropID.value, PlateThickness)
            
            if PlateThickness.value > minthickness:
            
                # Extract plate forces
                St7API.St7GetPlateResultArray(1, St7API.rtPlateForce,
                                              subtype[ResultAxis.capitalize()],
                                              platePos, ind+1,
                                              sampleLocation[
                                                      ResultLocation.capitalize()
                                                      ],
                                              PlateSurface[PlateSurf.capitalize()],
                                              1, numPoints, numColumns, ForceRes)
                # Extract plate moments
                St7API.St7GetPlateResultArray(1, St7API.rtPlateMoment,
                                              subtype[ResultAxis.capitalize()],
                                              platePos, ind+1,
                                              sampleLocation[
                                                      ResultLocation.capitalize()
                                                      ],
                                              PlateSurface[PlateSurf.capitalize()],
                                              1, numPoints, numColumns, MomentRes)
                # Extract plate stresses
                St7API.St7GetPlateResultArray(1, St7API.rtPlateStress,
                                              subtype[ResultAxis.capitalize()],
                                              platePos, ind+1,
                                              sampleLocation[
                                                      ResultLocation.capitalize()
                                                      ],
                                              PlateSurface[PlateSurf.capitalize()],
                                              1, numPoints, numColumns, StressRes)
                # Extract principal axis angle
                St7API.St7GetPlateResultArray(1, St7API.rtPlateStress,
                                              St7API.stPlateCombined,
                                              platePos, ind+1,
                                              sampleLocation[
                                                      ResultLocation.capitalize()
                                                      ],
                                              PlateSurface[PlateSurf.capitalize()],
                                              1, numPoints2, numColumns2, CombinedRes) 
                # Extract plate area
                St7API.St7GetElementData(1, St7API.tyPLATE,platePos, PlateArea)
                
                PlateId.append(platePos)
                PlateT.append(PlateThickness.value)
                PlateA.append(PlateArea.value)
                    
                for ptpos in range(0, numPoints.value):
                    
                    indpos = ptpos * numColumns.value
                    indpos2 = ptpos * numColumns2.value

                    ForceXX.append(ForceRes[indpos + St7API.ipPlateLocalxx])
                    ForceYY.append(ForceRes[indpos + St7API.ipPlateLocalyy])
                    ForceXY.append(ForceRes[indpos + St7API.ipPlateLocalxy])
                    ForceXZ.append(ForceRes[indpos + St7API.ipPlateLocalxz])
                    ForceYZ.append(ForceRes[indpos + St7API.ipPlateLocalyz])
                    MomentXX.append(MomentRes[indpos + St7API.ipPlateLocalxx])
                    MomentYY.append(MomentRes[indpos + St7API.ipPlateLocalyy])
                    MomentXY.append(MomentRes[indpos + St7API.ipPlateLocalxy])
                    StressXX.append(StressRes[indpos + St7API.ipPlateLocalxx])
                    StressYY.append(StressRes[indpos + St7API.ipPlateLocalyy])
                    StressXY.append(StressRes[indpos + St7API.ipPlateLocalxy])
                    Angle11xx.append(CombinedRes[indpos2 + St7API.ipPlateCombPrincipalAngle])
                    

        # Create a dataframe to store the output data
        if subtype[ResultAxis.capitalize()] == St7API.stPlateLocal:
            DF = pd.DataFrame(data={'PlateId': PlateId,
                                    'Plate Thickness (m)': PlateT,
                                    'Force (xx) (MN/m)': ForceXX,
                                    'Force (yy) (MN/m)': ForceYY,
                                    'Force (xy) (MN/m)': ForceXY,
                                    'Force (xz) (MN/m)': ForceXZ,
                                    'Force (yz) (MN/m)': ForceYZ,
                                    'Moment (xx) (MN.m/m)': MomentXX,
                                    'Moment (yy) (MN.m/m)': MomentYY,
                                    'Moment (xy) (MN.m/m)': MomentXY,
                                    'Stress (xx) (MPa)': StressXX,
                                    'Stress (yy) (MPa)': StressYY,
                                    'Stress (xy) (MPa)': StressXY,
                                    'Angle 11-xx (°)': Angle11xx},
                columns=['PlateId', 'Plate Thickness (m)', 'Force (xx) (MN/m)', 'Force (yy) (MN/m)',
                         'Force (xy) (MN/m)', 'Force (xz) (MN/m)',
                         'Force (yz) (MN/m)', 'Moment (xx) (MN.m/m)',
                         'Moment (yy) (MN.m/m)', 'Moment (xy) (MN.m/m)',
                         'Stress (xx) (MPa)', 'Stress (yy) (MPa)', 'Stress (xy) (MPa)', 'Angle 11-xx (°)'])

        
        stgname = casename.replace(' ', '').replace(':', '_').replace('Increment[', '').replace(']','')
        stgname = 'shearinputs_' + stgname
        
        x = re.search('Reset',stgname) 
        
        if (x):
            print('skipped reset stage')
        else:
            csvOutFile = Foldername + stgname + '.csv'
            print('Saved in csv file ' + csvOutFile)
            DF.to_csv(csvOutFile, index=False)
            
            StgNames.append(stgname+'.csv')
    
    ret = St7API.St7CloseResultFile(1)
    if ret == 0:
        print('Result File closed')
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')

    return ret

def export_cwinputs(modelname_bt, tempfolder_bt, resultfile_bt,
                                 groupID, numPlates, minthickness, ResultAxis='Local',
                                 ResultLocation='Centroid'):
    """
    Extract Beam Force information for a combined result file

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    resultfile_bt : BYTE
        Encoded Result file name
    groupID : LIST
        List of integer of the groups to modify
    numPlates : INTEGER
        Total number of Plates
    ResultAxis: STRING, optional
        Define axis the data is extracted on Local or Global
        DEFAULT is 'Local'.
    ResultLocation: STRING, optional
        Result sampling location
        DEFAULT is 'Centroid'
        Centroid, Gauss, NodeAverageSame, NodeAverageAll, NodeAverageSame
    PlateSurf : STRING, optional
        Plate Surface to extract data
        DEFAULT is 'Midplane
        Midplane, Zplus or Zminus

    Returns
    -------
    ret : INTEGER
        Return code API

    """
    
    print('Start extract plate results')

    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)

    modelname = modelname_bt.decode()
    Foldername = os.path.dirname(modelname) + "\\"
    
    # Open Result file
    numPrimary = ctypes.c_long()
    numSecondary = ctypes.c_long()
    CaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)
    
    ret = St7API.St7OpenResultFile(1, resultfile_bt, ''.encode(), True,
    	numPrimary, numSecondary)
    
    if ret != 0:
        explain_error(ret)
        print('Not able to open result file')
        St7API.St7CloseFile(1)
        print('Releasing API')
        St7API.St7Release()

    print('%d primary case(s) found' % numPrimary.value)

    CaseName_list = []
    for ind in range(1, numPrimary.value + 1):
        St7API.St7GetResultCaseName(1, ind, CaseName, St7API.kMaxStrLen)
        CaseName_list.append(CaseName.value.decode())
        print(CaseName.value.decode())

    # Set API storage values
    GroupPlate = ctypes.c_long()
    DblArrayRes = ctypes.c_double * 11
    CombinedRes = DblArrayRes()
    CombinedResZ = DblArrayRes()
    CombinedResZn = DblArrayRes()
    numPoints = ctypes.c_long()
    numColumns = ctypes.c_long()

    PlateThickness = ctypes.c_double()
    PlatePropID = ctypes.c_long()
    
    # Select Plates ID
    PlateNum = []
    
    for ind in range(1, numPlates+1):
    	St7API.St7GetElementGroup(1, St7API.tyPLATE, ind, GroupPlate)
    	if GroupPlate.value in groupID:
    		PlateNum.append(ind)
    print('%d plates will be extracted' % len(PlateNum))

    # dictionnary for options
    subtype = {'Local': St7API.stPlateLocal,
               'Global': St7API.stPlateGlobal}
    
    sampleLocation = {'Centroid': St7API.AtCentroid,
                      'Gauss': St7API.AtGaussPoints,
                      'Nodesaveragenever': St7API.AtNodesAverageNever,
                      'Nodesaverageall': St7API.AtNodesAverageAll,
                      'Nodesaveragesame': St7API.AtNodesAverageSame}
    
    StgNames = []
        
    for ind, casename in enumerate(CaseName_list):
        print('Start extracting data for case number %d %s' % (ind, casename))
    
        PlateId = []
        
        r1 = []
        r2 = []
        r3 = []
        r4 = []
        r5 = []
        r6 = []
        r7 = []
        r8 = []
        r9 = [] 
        
        for platePos in PlateNum:
          
            # Extract plate thickness
            St7API.St7GetElementProperty(1, St7API.tyPLATE, platePos, PlatePropID)
            St7API.St7GetPlateThickness(1, PlatePropID.value, PlateThickness)
            
            if PlateThickness.value > minthickness:
            
                # Extract principal axis angle
                St7API.St7GetPlateResultArray(1, St7API.rtPlateStress,
                                              St7API.stPlateCombined,
                                              platePos, ind+1,
                                              sampleLocation[ResultLocation.capitalize()],
                                              St7API.psPlateMidPlane,
                                              1, numPoints, numColumns, CombinedRes) 
                
                St7API.St7GetPlateResultArray(1, St7API.rtPlateStress,
                                              St7API.stPlateCombined,
                                              platePos, ind+1,
                                              sampleLocation[ResultLocation.capitalize()],
                                              St7API.psPlateZPlus,
                                              1, numPoints, numColumns, CombinedResZ)

                St7API.St7GetPlateResultArray(1, St7API.rtPlateStress,
                                              St7API.stPlateCombined,
                                              platePos, ind+1,
                                              sampleLocation[ResultLocation.capitalize()],
                                              St7API.psPlateZMinus,
                                              1, numPoints, numColumns, CombinedResZn)                               
                

                PlateId.append(platePos)
                    
                for ptpos in range(0, numPoints.value):
                    
                    indpos = ptpos * numColumns.value
                    
                    r1.append(CombinedResZn[indpos + St7API.ipPlateCombPrincipal11])
                    r2.append(CombinedResZn[indpos + St7API.ipPlateCombPrincipal22])
                    r3.append(CombinedResZn[indpos + St7API.ipPlateCombPrincipalAngle])
                    
                    r4.append(CombinedRes[indpos + St7API.ipPlateCombPrincipal11])
                    r5.append(CombinedRes[indpos + St7API.ipPlateCombPrincipal22])
                    r6.append(CombinedRes[indpos + St7API.ipPlateCombPrincipalAngle])
                    
                    r7.append(CombinedResZ[indpos + St7API.ipPlateCombPrincipal11])
                    r8.append(CombinedResZ[indpos + St7API.ipPlateCombPrincipal22])
                    r9.append(CombinedResZ[indpos + St7API.ipPlateCombPrincipalAngle])
                    

        # Create a dataframe to store the output data
        if subtype[ResultAxis.capitalize()] == St7API.stPlateLocal:
            DF = pd.DataFrame(data=({'PlateId' : PlateId, 's11(z-)' : r1, 's22(z-)' : r2, 'angle11-xx(z-)' : r3,
                                     's11(mid)' : r4, 's22(mid)' : r5, 'angle11-xx(mid)' : r6,
                                     's11(z+)' : r7, 's22(z+)' : r8, 'angle11-xx(z+)' : r9}),
                              columns=['PlateId','s11(z-)','s22(z-)','angle11-xx(z-)', 
                                       's11(mid)','s22(mid)','angle11-xx(mid)',
                                       's11(z+)','s22(z+)','angle11-xx(z+)'])

        stgname = casename.replace(' ', '').replace(':', '_').replace('Increment[', '').replace(']','')
        stgname = 'cwinputs_' + stgname
        
        x = re.search('Reset',stgname) 
        
        if (x):
            print('skipped reset stage')
        else:
            csvOutFile = Foldername + stgname + '.csv'
            print('Saved in csv file ' + csvOutFile)
            DF.to_csv(csvOutFile, index=False)
            
            StgNames.append(stgname+'.csv')
    
    ret = St7API.St7CloseResultFile(1)
    if ret == 0:
        print('Result File closed')
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')

    return ret


def export_plate_forceMomentData(modelname_bt, tempfolder_bt, resultfile_bt,
                                 groupID, numPlates, minthickness, ResultAxis='Local',
                                 ResultLocation='Centroid',
                                 PlateSurf='Midplane'):
    """
    Extract Beam Force information for a combined result file

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    resultfile_bt : BYTE
        Encoded Result file name
    groupID : LIST
        List of integer of the groups to modify
    numPlates : INTEGER
        Total number of Plates
    ResultAxis: STRING, optional
        Define axis the data is extracted on Local or Global
        DEFAULT is 'Local'.
    ResultLocation: STRING, optional
        Result sampling location
        DEFAULT is 'Centroid'
        Centroid, Gauss, NodeAverageSame, NodeAverageAll, NodeAverageSame
    PlateSurf : STRING, optional
        Plate Surface to extract data
        DEFAULT is 'Midplane
        Midplane, Zplus or Zminus

    Returns
    -------
    ret : INTEGER
        Return code API

    """
    
    print('Start extract plate results')

    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)

    modelname = modelname_bt.decode()
    Foldername = os.path.dirname(modelname) + "\\"
    
    # Open Result file
    numPrimary = ctypes.c_long()
    numSecondary = ctypes.c_long()
    CaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)
    
    ret = St7API.St7OpenResultFile(1, resultfile_bt, ''.encode(), True,
    	numPrimary, numSecondary)
    
    if ret != 0:
        explain_error(ret)
        print('Not able to open result file')
        St7API.St7CloseFile(1)
        print('Releasing API')
        St7API.St7Release()

    print('%d primary case(s) found' % numPrimary.value)

    CaseName_list = []
    for ind in range(1, numPrimary.value + 1):
        St7API.St7GetResultCaseName(1, ind, CaseName, St7API.kMaxStrLen)
        CaseName_list.append(CaseName.value.decode())
        print(CaseName.value.decode())

    # Set API storage values
    GroupPlate = ctypes.c_long()
    DblArrayRes = ctypes.c_double * 6
    ForceRes = DblArrayRes()
    MomentRes = DblArrayRes()
    numPoints = ctypes.c_long()
    numColumns = ctypes.c_long()
    PlateArea = ctypes.c_double()
    PlateThickness = ctypes.c_double()
    PlatePropID = ctypes.c_long()
    
    # Select Plates ID
    PlateNum = []
    
    for ind in range(1, numPlates+1):
    	St7API.St7GetElementGroup(1, St7API.tyPLATE, ind, GroupPlate)
    	if GroupPlate.value in groupID:
            PlateNum.append(ind)
    print('%d plates will be extracted' % len(PlateNum))

    # dictionnary for options
    subtype = {'Local': St7API.stPlateLocal,
               'Global': St7API.stPlateGlobal}
    
    sampleLocation = {'Centroid': St7API.AtCentroid,
                      'Gauss': St7API.AtGaussPoints,
                      'Nodesaveragenever': St7API.AtNodesAverageNever,
                      'Nodesaverageall': St7API.AtNodesAverageAll,
                      'Nodesaveragesame': St7API.AtNodesAverageSame}
    
    PlateSurface = {'Midplane': St7API.psPlateMidPlane,
                    'Zplus': St7API.psPlateZPlus,
                    'Zminus': St7API.psPlateZMinus}
    
    StgNames = []

    for ind, casename in enumerate(CaseName_list):
        print('Start extracting data for case number %d %s' % (ind, casename))
    
        PlateId = []
        PlateT = []
        PlateA = []
        ForceXX = []
        ForceYY = []
        ForceZZ = []
        ForceXY = []
        ForceXZ = []
        ForceYZ = []
        MomentXX = []
        MomentYY = []
        MomentZZ = []
        MomentXY = []
        MomentYZ = []
        MomentZX = []
        PropertyID = []
        
        for platePos in PlateNum:
            # Extract plate forces
            St7API.St7GetPlateResultArray(1, St7API.rtPlateForce,
                                          subtype[ResultAxis.capitalize()],
                                          platePos, ind+1,
                                          sampleLocation[
                                                  ResultLocation.capitalize()
                                                  ],
                                          PlateSurface[PlateSurf.capitalize()],
                                          1, numPoints, numColumns, ForceRes)
            # Extract plate moments
            St7API.St7GetPlateResultArray(1, St7API.rtPlateMoment,
                                          subtype[ResultAxis.capitalize()],
                                          platePos, ind+1,
                                          sampleLocation[
                                                  ResultLocation.capitalize()
                                                  ],
                                          PlateSurface[PlateSurf.capitalize()],
                                          1, numPoints, numColumns, MomentRes)
            # Extract plate thickness
            St7API.St7GetElementProperty(1, St7API.tyPLATE, platePos, PlatePropID)
            St7API.St7GetPlateThickness(1, PlatePropID.value, PlateThickness)

            # Extract plate area
            St7API.St7GetElementData(1, St7API.tyPLATE,platePos, PlateArea)
            
            if PlateThickness.value > minthickness:
                
                for ptpos in range(0, numPoints.value):
                        
                        indpos = ptpos * numColumns.value
                        PropertyID.append(PlatePropID.value)
                        PlateId.append(platePos)
                        PlateT.append(PlateThickness.value)
                        PlateA.append(PlateArea.value)
                        
                        if subtype[ResultAxis.capitalize()] == St7API.stPlateLocal:
                            ForceXX.append(ForceRes[indpos + St7API.ipPlateLocalxx])
                            ForceYY.append(ForceRes[indpos + St7API.ipPlateLocalyy])
                            ForceXY.append(ForceRes[indpos + St7API.ipPlateLocalxy])
                            ForceXZ.append(ForceRes[indpos + St7API.ipPlateLocalxz])
                            ForceYZ.append(ForceRes[indpos + St7API.ipPlateLocalyz])
                            MomentXX.append(MomentRes[indpos + St7API.ipPlateLocalxx])
                            MomentYY.append(MomentRes[indpos + St7API.ipPlateLocalyy])
                            MomentXY.append(MomentRes[indpos + St7API.ipPlateLocalxy])
                
                        elif subtype[ResultAxis.capitalize()] == St7API.stPlateGlobal:
                            ForceXX.append(ForceRes[indpos + St7API.ipPlateGlobalXX])
                            ForceYY.append(ForceRes[indpos + St7API.ipPlateGlobalYY])
                            ForceZZ.append(ForceRes[indpos + St7API.ipPlateGlobalZZ])
                            ForceXY.append(ForceRes[indpos + St7API.ipPlateGlobalXY])
                            ForceXZ.append(ForceRes[indpos + St7API.ipPlateGlobalZX])
                            ForceYZ.append(ForceRes[indpos + St7API.ipPlateGlobalYZ])
                            MomentXX.append(MomentRes[indpos + St7API.ipPlateGlobalXX])
                            MomentYY.append(MomentRes[indpos + St7API.ipPlateGlobalYY])
                            MomentZZ.append(MomentRes[indpos + St7API.ipPlateGlobalZZ])
                            MomentXY.append(MomentRes[indpos + St7API.ipPlateGlobalXY])
                            MomentYZ.append(MomentRes[indpos + St7API.ipPlateGlobalYZ])
                            MomentZX.append(MomentRes[indpos + St7API.ipPlateGlobalZX])

        
        # Create a dataframe to store the output data
        if subtype[ResultAxis.capitalize()] == St7API.stPlateLocal:
            DF = pd.DataFrame(data={'PlateId': PlateId,
                                    'Plate Thickness (m)': PlateT,
                                    'Force (xx) (MN/m)': ForceXX,
                                    'Force (yy) (MN/m)': ForceYY,
                                    'Force (xy) (MN/m)': ForceXY,
                                    'Force (xz) (MN/m)': ForceXZ,
                                    'Force (yz) (MN/m)': ForceYZ,
                                    'Moment (xx) (MN.m/m)': MomentXX,
                                    'Moment (yy) (MN.m/m)': MomentYY,
                                    'Moment (xy) (MN.m/m)': MomentXY,
                                    'Plate Area (m2)': PlateA,
                                    'Property ID' : PropertyID
                                    },
                columns=['PlateId', 'Plate Thickness (m)', 'Force (xx) (MN/m)', 'Force (yy) (MN/m)',
                         'Force (xy) (MN/m)', 'Force (xz) (MN/m)',
                         'Force (yz) (MN/m)', 'Moment (xx) (MN.m/m)',
                         'Moment (yy) (MN.m/m)', 'Moment (xy) (MN.m/m)', 'Plate Area (m2)', 'Property ID'])
        
        elif subtype[ResultAxis.capitalize()] == St7API.stPlateGlobal:
            DF = pd.DataFrame(data={'PlateId': PlateId,
                                    'Force (XX) (MN/m)': ForceXX,
                                    'Force (YY) (MN/m)': ForceYY,
                                    'Force (ZZ) (MN/m)': ForceZZ,
                                    'Force (XY) (MN/m)': ForceXY,
                                    'Force (YZ) (MN/m)': ForceYZ,
                                    'Force (ZX) (MN/m)': ForceXZ,
                                    'Moment (XX) (MN.m/m)': MomentXX,
                                    'Moment (YY) (MN.m/m)': MomentYY,
                                    'Moment (ZZ) (MN.m/m)': MomentZZ,
                                    'Moment (XY) (MN.m/m)': MomentXY,
                                    'Moment (YZ) (MN.m/m)': MomentYZ,
                                    'Moment (ZX) (MN.m/m)': MomentZX
                                    },
                columns=['PlateId', 'Force (XX) (MN/m)', 'Force (YY) (MN/m)',
                         'Force (ZZ) (MN/m)', 'Force (XY) (MN/m)',
                         'Force (YZ) (MN/m)', 'Force (ZX) (MN/m)',
                         'Moment (XX) (MN.m/m)', 'Moment (YY) (MN.m/m)',
                         'Moment (ZZ) (MN.m/m)', 'Moment (XY) (MN.m/m)',
                         'Moment (YZ) (MN.m/m)', 'Moment (ZX) (MN.m/m)'])
        
        
        stgname = casename.replace(' ', '').replace(':', '_').replace('Increment[', '').replace(']','')
        stgname = 'sandwichinputs_' + stgname
        
        x = re.search('Reset',stgname) 
        
    
        if (x):
            print('skipped reset stage')
        else:
            csvOutFile = Foldername + stgname + '.csv'
            print('Saved in csv file ' + csvOutFile)
            DF.to_csv(csvOutFile, index=False)
            
            StgNames.append(stgname+'.csv')
    
    DF2 = pd.DataFrame(StgNames)
    DF2.to_csv(Foldername + 'Stage Names.csv', index=False, header=False)
    
    ret = St7API.St7CloseResultFile(1)
    if ret == 0:
        print('Result File closed')
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')

    return ret

def export_ES_Inputs(modelname_bt, tempfolder_bt, resultfile_bt,
                                 groupID, numPlates, minthickness, ResultAxis='Local',
                                 ResultLocation='Centroid',
                                 PlateSurf='Midplane'):
    """
    Extract Beam Force information for a combined result file

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    resultfile_bt : BYTE
        Encoded Result file name
    groupID : LIST
        List of integer of the groups to modify
    numPlates : INTEGER
        Total number of Plates
    ResultAxis: STRING, optional
        Define axis the data is extracted on Local or Global
        DEFAULT is 'Local'.
    ResultLocation: STRING, optional
        Result sampling location
        DEFAULT is 'Centroid'
        Centroid, Gauss, NodeAverageSame, NodeAverageAll, NodeAverageSame
    PlateSurf : STRING, optional
        Plate Surface to extract data
        DEFAULT is 'Midplane
        Midplane, Zplus or Zminus

    Returns
    -------
    ret : INTEGER
        Return code API

    """
    
    print('Start extract plate results')

    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)

    modelname = modelname_bt.decode()
    Foldername = os.path.dirname(modelname) + "\\"
    
    # Open Result file
    numPrimary = ctypes.c_long()
    numSecondary = ctypes.c_long()
    CaseName = ctypes.create_string_buffer(St7API.kMaxStrLen)
    
    ret = St7API.St7OpenResultFile(1, resultfile_bt, ''.encode(), True,
    	numPrimary, numSecondary)
    
    if ret != 0:
        explain_error(ret)
        print('Not able to open result file')
        St7API.St7CloseFile(1)
        print('Releasing API')
        St7API.St7Release()

    print('%d primary case(s) found' % numPrimary.value)

    CaseName_list = []
    for ind in range(1, numPrimary.value + 1):
        St7API.St7GetResultCaseName(1, ind, CaseName, St7API.kMaxStrLen)
        CaseName_list.append(CaseName.value.decode())
        print(CaseName.value.decode())

    # Set API storage values
    GroupPlate = ctypes.c_long()
    DblArrayRes = ctypes.c_double * 6
    ForceRes = DblArrayRes()
    MomentRes = DblArrayRes()
    numPoints = ctypes.c_long()
    numColumns = ctypes.c_long()
    DblArrayT = ctypes.c_double * 2
    PlateThickness = DblArrayT()
    PlateArea = ctypes.c_double()
    PlatePropID = ctypes.c_long()
    
    # Select Plates ID
    PlateNum = []
    
    for ind in range(1, numPlates+1):
    	St7API.St7GetElementGroup(1, St7API.tyPLATE, ind, GroupPlate)
    	if GroupPlate.value in groupID:
            PlateNum.append(ind)
    print('%d plates will be extracted' % len(PlateNum))

    # dictionnary for options
    subtype = {'Local': St7API.stPlateLocal,
               'Global': St7API.stPlateGlobal}
    
    sampleLocation = {'Centroid': St7API.AtCentroid,
                      'Gauss': St7API.AtGaussPoints,
                      'Nodesaveragenever': St7API.AtNodesAverageNever,
                      'Nodesaverageall': St7API.AtNodesAverageAll,
                      'Nodesaveragesame': St7API.AtNodesAverageSame}
    
    PlateSurface = {'Midplane': St7API.psPlateMidPlane,
                    'Zplus': St7API.psPlateZPlus,
                    'Zminus': St7API.psPlateZMinus}
    
    StgNames = []

    for ind, casename in enumerate(CaseName_list):
        print('Start extracting data for case number %d %s' % (ind, casename))
    
        PlateId = []
        PlateT = []
        PlateA = []
        ForceXX = []
        ForceYY = []
        ForceZZ = []
        ForceXY = []
        ForceXZ = []
        ForceYZ = []
        MomentXX = []
        MomentYY = []
        MomentZZ = []
        MomentXY = []
        MomentYZ = []
        MomentZX = []
        PropertyID = []
        
        for platePos in PlateNum:
            # Extract plate forces
            St7API.St7GetPlateResultArray(1, St7API.rtPlateForce,
                                          subtype[ResultAxis.capitalize()],
                                          platePos, ind+1,
                                          sampleLocation[
                                                  ResultLocation.capitalize()
                                                  ],
                                          PlateSurface[PlateSurf.capitalize()],
                                          1, numPoints, numColumns, ForceRes)
            # Extract plate moments
            St7API.St7GetPlateResultArray(1, St7API.rtPlateMoment,
                                          subtype[ResultAxis.capitalize()],
                                          platePos, ind+1,
                                          sampleLocation[
                                                  ResultLocation.capitalize()
                                                  ],
                                          PlateSurface[PlateSurf.capitalize()],
                                          1, numPoints, numColumns, MomentRes)
            # Extract plate thickness
            St7API.St7GetElementProperty(1, St7API.tyPLATE, platePos, PlatePropID)
            St7API.St7GetPlateThickness(1, PlatePropID.value, PlateThickness)

            # Extract plate area
            St7API.St7GetElementData(1, St7API.tyPLATE,platePos, PlateArea)
            
            if PlateThickness[1] > minthickness:
                
                for ptpos in range(0, numPoints.value):
                        
                        indpos = ptpos * numColumns.value
                        PropertyID.append(PlatePropID.value)
                        PlateId.append(platePos)
                        PlateT.append(PlateThickness[1])
                        PlateA.append(PlateArea.value)
                        
                        if subtype[ResultAxis.capitalize()] == St7API.stPlateLocal:
                            ForceXX.append(ForceRes[indpos + St7API.ipPlateLocalxx])
                            ForceYY.append(ForceRes[indpos + St7API.ipPlateLocalyy])
                            ForceXY.append(ForceRes[indpos + St7API.ipPlateLocalxy])
                            ForceXZ.append(ForceRes[indpos + St7API.ipPlateLocalxz])
                            ForceYZ.append(ForceRes[indpos + St7API.ipPlateLocalyz])
                            MomentXX.append(MomentRes[indpos + St7API.ipPlateLocalxx])
                            MomentYY.append(MomentRes[indpos + St7API.ipPlateLocalyy])
                            MomentXY.append(MomentRes[indpos + St7API.ipPlateLocalxy])
                
                        elif subtype[ResultAxis.capitalize()] == St7API.stPlateGlobal:
                            ForceXX.append(ForceRes[indpos + St7API.ipPlateGlobalXX])
                            ForceYY.append(ForceRes[indpos + St7API.ipPlateGlobalYY])
                            ForceZZ.append(ForceRes[indpos + St7API.ipPlateGlobalZZ])
                            ForceXY.append(ForceRes[indpos + St7API.ipPlateGlobalXY])
                            ForceXZ.append(ForceRes[indpos + St7API.ipPlateGlobalZX])
                            ForceYZ.append(ForceRes[indpos + St7API.ipPlateGlobalYZ])
                            MomentXX.append(MomentRes[indpos + St7API.ipPlateGlobalXX])
                            MomentYY.append(MomentRes[indpos + St7API.ipPlateGlobalYY])
                            MomentZZ.append(MomentRes[indpos + St7API.ipPlateGlobalZZ])
                            MomentXY.append(MomentRes[indpos + St7API.ipPlateGlobalXY])
                            MomentYZ.append(MomentRes[indpos + St7API.ipPlateGlobalYZ])
                            MomentZX.append(MomentRes[indpos + St7API.ipPlateGlobalZX])

        
        # Create a dataframe to store the output data
        if subtype[ResultAxis.capitalize()] == St7API.stPlateLocal:
            DF = pd.DataFrame(data={'PlateId': PlateId,
                                    'Plate Thickness (m)': PlateT,
                                    'Force (xx) (MN/m)': ForceXX,
                                    'Force (yy) (MN/m)': ForceYY,
                                    'Force (xy) (MN/m)': ForceXY,
                                    'Moment (xx) (MN.m/m)': MomentXX,
                                    'Moment (yy) (MN.m/m)': MomentYY,
                                    'Moment (xy) (MN.m/m)': MomentXY,
                                    'Plate Area (m2)': PlateA,
                                    'Property ID' : PropertyID
                                    },
                columns=['PlateId', 'Plate Thickness (m)', 'Force (xx) (MN/m)', 'Force (yy) (MN/m)',
                         'Force (xy) (MN/m)', 'Moment (xx) (MN.m/m)',
                         'Moment (yy) (MN.m/m)', 'Moment (xy) (MN.m/m)', 'Plate Area (m2)', 'Property ID'])
        
        elif subtype[ResultAxis.capitalize()] == St7API.stPlateGlobal:
            DF = pd.DataFrame(data={'PlateId': PlateId,
                                    'Force (XX) (MN/m)': ForceXX,
                                    'Force (YY) (MN/m)': ForceYY,
                                    'Force (ZZ) (MN/m)': ForceZZ,
                                    'Force (XY) (MN/m)': ForceXY,
                                    'Force (YZ) (MN/m)': ForceYZ,
                                    'Force (ZX) (MN/m)': ForceXZ,
                                    'Moment (XX) (MN.m/m)': MomentXX,
                                    'Moment (YY) (MN.m/m)': MomentYY,
                                    'Moment (ZZ) (MN.m/m)': MomentZZ,
                                    'Moment (XY) (MN.m/m)': MomentXY,
                                    'Moment (YZ) (MN.m/m)': MomentYZ,
                                    'Moment (ZX) (MN.m/m)': MomentZX
                                    },
                columns=['PlateId', 'Force (XX) (MN/m)', 'Force (YY) (MN/m)',
                         'Force (ZZ) (MN/m)', 'Force (XY) (MN/m)',
                         'Force (YZ) (MN/m)', 'Force (ZX) (MN/m)',
                         'Moment (XX) (MN.m/m)', 'Moment (YY) (MN.m/m)',
                         'Moment (ZZ) (MN.m/m)', 'Moment (XY) (MN.m/m)',
                         'Moment (YZ) (MN.m/m)', 'Moment (ZX) (MN.m/m)'])
        
        
        stgname = casename.replace(' ', '').replace(':', '_').replace('Increment[', '').replace(']','')
        stgname = 'ES_Inputs_' + stgname
        
        x = re.search('Reset',stgname) 
        
    
        if (x):
            print('skipped reset stage')
        else:
            csvOutFile = Foldername + stgname + '.csv'
            print('Saved in csv file ' + csvOutFile)
            DF.to_csv(csvOutFile, index=False)
            
            StgNames.append(stgname+'.csv')
    
    ret = St7API.St7CloseResultFile(1)
    if ret == 0:
        print('Result File closed')
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')

    return ret

def export_platenodes(modelname_bt, tempfolder_bt, groupID, numNodes, numPlates, minthickness):
    print('Start extract node co-ordinates and plate vertices')

    # Open Model
    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    if ret != 0:
        explain_error(ret)
        St7API.St7Release()
        print('Cannot open file')
        sys.exit(1)

    modelname = modelname_bt.decode()

    # Set API storage values
    XYZType = ctypes.c_double * 3
    NodeXYZ = XYZType()
    PlateType = ctypes.c_long * 20
    PlateNodes = PlateType()
    GroupPlate = ctypes.c_long()
    PlateThickness = ctypes.c_double()
    PlatePropID = ctypes.c_long()
    groupname = ctypes.create_string_buffer(St7API.kMaxStrLen)
    GroupNum = ctypes.c_long()
    
    # Select Plates 
    NodeX = []
    NodeY = []
    NodeZ = []
    N1 = []
    N2 = []
    N3 = []
    N4 = []
    PlateID = []
    GroupID = []
    
    for ind in range(1, numNodes+1):
        St7API.St7GetNodeXYZ(1, ind, NodeXYZ)
        NodeX.append(NodeXYZ[0])
        NodeY.append(NodeXYZ[1])
        NodeZ.append(NodeXYZ[2])
        
    for ind in range(1, numPlates+1):
    	
        St7API.St7GetElementProperty(1, St7API.tyPLATE, ind, PlatePropID)
        St7API.St7GetPlateThickness(1, PlatePropID.value, PlateThickness)
        St7API.St7GetElementGroup(1, St7API.tyPLATE, ind, GroupPlate)
        St7API.St7GetEntityGroup(1, St7API.tyPLATE, ind, GroupNum)
        St7API.St7GetGroupIDName(1, GroupNum.value, groupname,St7API.kMaxStrLen)
        
        if GroupPlate.value in groupID and PlateThickness.value > minthickness:
            
            St7API.St7GetElementConnection(1, St7API.tyPLATE, ind, PlateNodes)
            N1.append(PlateNodes[1])
            N2.append(PlateNodes[2])
            N3.append(PlateNodes[3])
            if PlateNodes[0] == 3:
                N4.append(" ")
            else:
                N4.append(PlateNodes[4])
            PlateID.append(ind)
            GroupID.append(groupname.value.decode())
            
            
    print('%d nodes will be extracted' % len(NodeX))
    print('%d plates will be extracted' % len(N1))
    
    DF = pd.DataFrame(list(zip(NodeX,NodeY,NodeZ)))
    DF.to_csv('{}_Nodes.csv'.format(os.path.splitext(modelname)[0]), index=False, header=False)
    DF2 = pd.DataFrame(list(zip(N1,N2,N3,N4,PlateID,GroupID)))
    DF2.to_csv('{}_Plates.csv'.format(os.path.splitext(modelname)[0]), index=False, header=False)
    
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')

    return ret

def run_solver(modelname_bt, tempfolder_bt, logfilename_bt, resultfile_bt,
               solverType='NonLinearStatic', runMode='Normal',
               schemeType='Direct Sparse', nodeOrdering='AMD',
               startNodeNum=1, nonLinGeo=True, nonLinMaterial=True):
    """
    Run Solver function

    Parameters
    ----------
    modelname_bt : BYTE
        Encoded Input Model file name
    tempfolder_bt : BYTE
        Encoded Temporary folder location
    logfilename_bt : BYTE
        Encoded Log file name
    resultfile_bt : BYTE
        Encoded Result file name
    solverType : STRING, optional
        DEFAULT is 'NonLinearStatic'.
        LinearStatic - Linear static solver.
        LinearBuckling - Linear buckling solver.
        NonLinearStatic - Nonlinear static solver.
        NaturalFrequency - Natural frequency solver.
        Harmonic - Harmonic response solver.
        Spectral - Spectral response solver.
        LinearDynamic - Linear transient dynamic solver.
        NonLinearDynamic - Nonlinear transient dynamic solver.
        SteadyHeat - Steady heat solver.
        TransientHeat - Transient heat solver.
        LoadInfluence - Load influence solver.
        QuasiStatic - Quasi static solver. 
    runMode : STRING, optional
        Solver progress mode
        DEFAULT is 'Normal'
        Normal - Full solver dialog is displayed, process waits for manual termination.
        NormalClose - Full solver dialog is displayed, process terminates on completion.
        Progress - Solver progress bar is displayed, process terminates on completion.
        Background - No solver dialog is created, process terminates on completion
    schemeType : STRING, optional
        Scheme used for the solution of the linear system arising from the
        Finite Element model
        DEFAULT is 'Direct Sparse'.
        Skyline - Skyline, works best with Tree and Geometry ordering
        Direct Sparse - Direct Sparse
        Iterative - Iterative PCG
    nodeOrdering : TYPE, optional
        Node number re-ordering strategy used by the solver
        DEFAULT is 'AMD'.
        None - no reordering.
        Tree - Tree ordering.
        Geometry - Geometry.
        AMD - AMD.
    startNodeNum : INTEGER, optional
        Starting node number for the Tree type re-ordering strategy
        DEFAULT is 1.
    nonLinGeo : BOOLEAN, optional
        State of the Nonlinear geometry option for Nonlinear analyses
        DEFAULT is True.
    nonLinMaterial : BOOLEAN, optional
        State of the Nonlinear material option for Nonlinear analyses
        DEFAULT is True.

    Returns
    -------
    ret : INTEGER
        Return code API

    """

    ret = St7API.St7OpenFile(1, modelname_bt, tempfolder_bt)
    
    if ret != 0:
    	explain_error(ret)
    	print('Releasing API')
    	St7API.St7Release()

    schemeOptions = {'Skyline': St7API.stSkyline,
                     'Direct Sparse': St7API.stSparse,
                     'Iterative': St7API.stIterativePCG}
    
    sortOptions = {'None': St7API.rnNone, 'Tree': St7API.rnTree,
                   'Geometry': St7API.rnGeometry, 'AMD': St7API.rnAMD}
    
    runModeOptions = {'Normal': St7API.smNormalRun,
                      'NormalClose': St7API.smNormalCloseRun,
                      'Progress': St7API.smProgressRun,
                      'Background': St7API.smBackgroundRun}
    
    solverOptions = {'LinearStatic': St7API.stLinearStaticSolver,
                     'LinearBuckling': St7API.stLinearBucklingSolver,
                     'NonLinearStatic': St7API.stNonlinearStaticSolver,
                     'NaturalFrequency': St7API.stNaturalFrequencySolver,
                     'Harmonic': St7API.stHarmonicResponseSolver,
                     'Spectral': St7API.stSpectralResponseSolver,
                     'LinearDynamic': St7API.stLinearTransientDynamicSolver,
                     'NonLinearDynamic': St7API.stNonlinearTransientDynamicSolver,
                     'SteadyHeat': St7API.stSteadyHeatSolver,
                     'TransientHeat': St7API.stTransientHeatSolver,
                     'LoadInfluence': St7API.stLoadInfluenceSolver,
                     'QuasiStatic': St7API.stQuasiStaticSolver}
    
    ret = St7API.St7SetSolverScheme(1, schemeOptions[schemeType])
    if ret != 0:
        explain_error(ret)
        print('Releasing API')
        St7API.St7Release()
    else:
        print('Scheme Option: %s' % schemeType)

    ret = St7API.St7SetSolverSort(1, sortOptions[nodeOrdering])
    if ret != 0:
         explain_error(ret)
         print('Releasing API')
         St7API.St7Release()
    else:
        print('Node Sorting Option: %s' % nodeOrdering)
    
    if nodeOrdering == 'Tree':
        ret = St7API.St7SetSolverTreeStartNumber(1, startNodeNum)
        if ret != 0:
            explain_error(ret)
            print('Releasing API')
            St7API.St7Release()
        else:
            print('Starting at node %d' % startNodeNum)
    
    if nonLinGeo:
        ret = St7API.St7SetSolverNonlinearGeometry(1, St7API.btTrue)
        if ret != 0:
            explain_error(ret)
            print('Releasing API')
            St7API.St7Release()
        else:
            print('Non Linear Geometry set as True')
    
    if nonLinMaterial:
        St7API.St7SetSolverNonlinearMaterial(1, St7API.btTrue)
        if ret != 0:
            explain_error(ret)
            print('Releasing API')
            St7API.St7Release()
        else:
            print('Non Linear Material set as True')
    
    St7API.St7SetResultLogFileName(1, logfilename_bt)
    St7API.St7SetResultFileName(1, resultfile_bt)
    
    ret = St7API.St7RunSolver(1, solverOptions[solverType],
                              runModeOptions[runMode], St7API.btTrue)
    if ret != 0:
        explain_error(ret)
        print('Releasing API')
        St7API.St7Release()
    else:
        print('Solver executed')
    
    ret = St7API.St7CloseFile(1)
    if ret == 0:
        print('Model File closed')
   
    return ret