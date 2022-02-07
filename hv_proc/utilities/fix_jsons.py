#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 27 12:02:52 2021

@author: jstout
"""

import os, glob
import pandas as pd
import json
import copy
from pathlib import Path
import logging
import nibabel as nb
from mne.transforms import apply_trans

from mne_bids import BIDSPath

logger = logging.Logger('HV')

# =============================================================================
# Helper functions
# =============================================================================

def get_anat_json_fname(subjid):
    '''Find the t1 filename.  There are either mprage or spgr files'''
    acq = 'mprage'
    tmp_ = Path(f'{subjid}/ses-01/anat/{subjid}_ses-01_acq-{acq}_run-01_T1w.json')
    if tmp_.exists():
        return tmp_
    elif Path(f'{subjid}/ses-01/anat/{subjid}_ses-01_acq-fspgr_run-01_T1w.json').exists():
        return Path(f'{subjid}/ses-01/anat/{subjid}_ses-01_acq-fspgr_run-01_T1w.json')
    else:
        logger.warning(f'T1w json not found for {subjid}')
        return None

def get_anat_json(row, megj_col='megjson'):
    '''Return a dictionary with all the keys with AnatomicalLandmark in the key
    name.  megj_col represents the column name in the dataframe for the meg
    json path'''
    with open(row[megj_col]) as w:
        json_out = json.load(w)
        anat_keys = {x:y for (x,y) in json_out.items() if 'AnatomicalLandmark' in x}
    return anat_keys

def write_anat_json(row, t1j_col='t1json', overwrite=False):
    '''Write the AnatomicalLandmark keys from the meg json to the mri json.
    Takes the dictionary pulled from the MEG json - (use get_anat_json)'''
    with open(row[t1j_col]) as w:
        json_in = json.load(w)
    #Check to see if the AnatomicalLandmarks are already present 
    anat_keys = {x:y for (x,y) in json_in.items() if 'AnatomicalLandmark' in x}
    if overwrite==False:
        assert anat_keys == {}

    #Retreive the anatomical keys from the meg json
    anat_keys = get_anat_json(row)
    #Convert to RAS
    anat_keys = convert_to_RAS(anat_keys)
    assert anat_keys != {}
    #Convert to Voxel Index
    vox_keys = ras2vox(row[t1j_col], anat_keys)
    
    json_out = json_in
    del json_in
    json_out.update(vox_keys)
    
    #Write json
    with open(row[t1j_col], 'w') as w:
        json.dump(json_out, w, indent='    ') 
    print(f'Succesfully converted: {row[t1j_col]}')

def confirm_update(row, t1j_col='t1json'):
    '''Return True if the AnatomicalLandmark entries are in the T1json'''
    with open(row[t1j_col]) as w:
        json_in = json.load(w)
    anat_keys = {x:y for (x,y) in json_in.items() if 'AnatomicalLandmark' in x}
    if anat_keys == {}:
        return False
    else:
        return True

def _lps_2_ras(vals):
    return -1*vals[0], -1*vals[1], vals[2]

def convert_to_RAS(anatomical):
    '''Check to see if LPS, then convert to RAS'''
    tmp_ = anatomical['AnatomicalLandmarkCoordinateSystemDescription']
    output = copy.copy(anatomical)
    if tmp_[0:3].upper()=='LPS':
        in_ = anatomical['AnatomicalLandmarkCoordinateSystemDescription']
        output['AnatomicalLandmarkCoordinateSystemDescription'] = \
            in_.replace('LPS','RAS')
        tmp_ = anatomical['AnatomicalLandmarkCoordinates']
        output['AnatomicalLandmarkCoordinates']['NAS'] = _lps_2_ras(tmp_['NAS'])
        output['AnatomicalLandmarkCoordinates']['LPA'] = _lps_2_ras(tmp_['LPA'])
        output['AnatomicalLandmarkCoordinates']['RPA'] = _lps_2_ras(tmp_['RPA'])
    return output

def ras2vox(t1_json, anat_keys): #t1_json, meg_json):
    '''Take RAS coordinate in mm and convert to voxel index according to 
    meg_bids spec
    Return a dictionary of the AnatomicalLandmarkCoordinates in vox'''
    t1_json = Path(t1_json)
    
    if t1_json.with_suffix('.nii').exists():
        t1_fname = t1_json.with_suffix('.nii')
    elif t1_json.with_suffix('.nii.gz').exists():
        t1_fname = t1_json.with_suffix('.nii.gz')
    else:
        logger.exception(f'''No associated .nii or .nii.gz file found in {t1_json.parent}
                         associated with {str(t1_json)}''')
    t1 = nb.load(t1_fname)
    t1_mgh = nb.MGHImage(t1.dataobj, t1.affine)
    
    ras_coords = convert_to_RAS(anat_keys)['AnatomicalLandmarkCoordinates']
    vox_coords = copy.deepcopy(ras_coords)
    for fid in vox_coords.keys():
        tmp_ = apply_trans(t1_mgh.header.get_ras2vox(), ras_coords[fid])
        vox_coords[fid] = list(tmp_)
    return {'AnatomicalLandmarkCoordinates':vox_coords}

def get_candidate_megjsons(subjid):
    cand_ = glob.glob(f'{subjid}/ses-01/meg/{subjid}_ses-01_task-*_run-01_coordsystem.json')
    cand_ = [i for i in cand_ if 'artifact' not in i]
    if len(cand_) == 0:
        return ''
    else:
        return cand_[0]

# =============================================================================
# Process the files
# =============================================================================

help_str = \
    '''Adds fiducial locations to the T1w json file in voxel ids.
    Must provide bids_root as an input to the function.  '''

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(help_str) 
        exit()
    else:
        bids_root = sys.argv[1]

    os.chdir(bids_root)

    subjects=glob.glob('sub-ON*')
    dframe = pd.DataFrame(subjects, columns=['subjids'])
    dframe['t1json']=dframe.subjids.apply(get_anat_json_fname) 
    dframe['megjson'] = dframe.subjids.apply(get_candidate_megjsons) #lambda x: f'{x}/ses-01/meg/{x}_ses-01_task-movie_run-01_coordsystem.json')
    
    ## Make a dataframe of just the meg entries
    meg = dframe[dframe.megjson.apply(os.path.exists)]
    
    for i,row in meg.iterrows():
        try:
            write_anat_json(row, overwrite=True)
        except BaseException as e:
            logger.exception(f'{row.subjids}: {e}') 
        
# # The errors are likely from gettting the wrong T1 json file 
# for i,row in meg.iterrows():
#     try:
#         confirm_update(row) 
#     except:
#         print('error')

