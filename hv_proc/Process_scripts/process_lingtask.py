#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 10:53:43 2025

@author: jstout
"""

import sys
import mne
import nih2mne
from nih2mne.utilities.trigger_utilities import (parse_marks, detect_digital,
                    check_analog_inverted, threshold_detect, append_conditions, correct_to_projector, add_event_offset)
from nih2mne.utilities.markerfile_write import main as write_markerfile
import os, os.path as op
import copy
import pandas as pd
import glob

# Data from pre-042225 have timing issues
# Data from 042225-051325 require logfiles to extract the block label and word order
# Data from 051325+ should have block label in the UADC channel


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-meg_fname')
    parser.add_argument('-logfile', default=None)
    args = parser.parse_args()
    
    meg_fname = args.meg_fname 
    if args.logfile != None:
        logfile = args.logfile
    else:
        meghash = op.basename(meg_fname).split('_')[0]
        topdir = op.dirname(op.dirname(meg_fname))
        toplogdir = op.join(topdir, 'logfiles')
        assert op.exists(toplogdir), "Provide a path to a logfile or have a folder of logfiles at the level of the meg folders"
        logfiles = glob.glob(op.join(toplogdir, meghash, f'{meghash}_LingTask*.csv'))
        assert op.exists(op.join(toplogdir, meghash)), f"{meghash} does not have a folder in {toplogdir}"
        _tmp = [i for i in logfiles if not i.endswith('Latencies.csv')]
        assert len(_tmp)==1, f"Found too many logfiles {_tmp}"
        logfile = _tmp[0]
    
    conv_csv_fname = op.join(op.dirname(__file__), 'lingtask_masterlist_mod.csv')


#### Setup ###      !!!!!!!!!!!!!!! REMOVE meg_fname !!!!!!!!!!!!!!  
# conv_csv_fname = '/home/jstout/src/hv_procV4/lingtask_masterlist_mod.csv'


block_offset_delay = 0.3499
auditory_delay = 0.018



"""
meg_fname = '/fast2/NEW_HV_PROT_Dsets/20250423/UAVMPOPZ_poeppel_20250423_004.ds'
raw = mne.io.read_raw_ctf(meg_fname, preload=True, system_clock='ignore')
raw.pick_types(misc=True)
logfile = '/fast2/NEW_HV_PROT_Dsets/logfiles/UAVMPOPZ/UAVMPOPZ_LingTask_Seq1_04232025_093403.csv'
"""

# Load and add auditory delay
dig_dframe = detect_digital(filename=meg_fname, channel='UPPT001')
aud_idxs = dig_dframe.query('condition != "120"').index
dig_dframe.loc[aud_idxs, 'onset'] += auditory_delay

# Set active stim marker
dig_dframe.loc[aud_idxs][::2]
dig_dframe['trigactive']=int(0)
stim_idxs = dig_dframe.loc[aud_idxs].loc[::2,'trigactive'].index
dig_dframe.loc[stim_idxs, 'trigactive']=int(1)

log_dframe = pd.read_csv(logfile, index_col=0)

# Copy stim words from the logfile to the dataframe
assert len(log_dframe)==len(stim_idxs) , "The logfile size does not match the size of the UPPT001 trigger"
_tmp = log_dframe['word'].values
dig_dframe.loc[stim_idxs, 'word'] = [f'word={i}' for i in _tmp]
dig_dframe.loc[stim_idxs, 'condition'] = log_dframe['trig1'].values

# Set the blockID from the logfile
dig_dframe.loc[stim_idxs, 'blockID'] = [int(str(i)[0]) for i in log_dframe.trig1.values]
dig_dframe.loc[stim_idxs+1, 'blockID'] = [int(str(i)[0]) for i in log_dframe.trig1.values]

# Add word order
word_order = copy.deepcopy(dig_dframe.loc[stim_idxs])
for idx, row in word_order.iterrows():
    block=str(row.condition)[0]
    word_index = str(row.condition)[1]
    word_order.loc[idx,'condition']=f'c{block}_w{word_index}'
    

# Compute block transitions
block_transitions={} #pd.DataFrame(columns=['condition', 'onset'])
for idx, row in dig_dframe.iterrows():
    dframe_idx = len(block_transitions)
    if idx+1 == len(dig_dframe):
        block_transitions['BLOCK'+str(int(row.blockID))+'_offset']=row.onset + block_offset_delay
        continue
    if idx==0:
        block_transitions['BLOCK'+str(int(row.blockID))+'_onset']=row.onset
        continue
    if dig_dframe.loc[idx+1,'condition']=='120':
        block_transitions['BLOCK'+str(int(row.blockID))+'_offset']=row.onset + block_offset_delay
    if dig_dframe.loc[idx-1, 'condition']=='120':
        block_transitions['BLOCK'+str(int(row.blockID))+'_onset']=row.onset

block_dframe = pd.DataFrame(block_transitions.items(), columns=['condition', 'onset'])
block_dframe['trial']=0
block_dframe['channel']='logfile'        

# Eliminate the non-audio triggers
stim_active = dig_dframe.query('trigactive==1').index
dig_dframe = dig_dframe.loc[stim_active]
dig_dframe['condition'] = dig_dframe['word']

final_dframe = append_conditions([dig_dframe, block_dframe, word_order])

#%% Test against issues in the data
blockval_list = ["BLOCK1_onset", "BLOCK2_onset","BLOCK2_onset","BLOCK3_onset",
               "BLOCK4_onset", "BLOCK5_onset",
               "BLOCK1_offset", "BLOCK2_offset", "BLOCK3_offset", 
               "BLOCK4_offset", "BLOCK5_offset",]
test_len = len( final_dframe.query(f'condition in {blockval_list}'))
assert test_len == 10, "Number of blocks not correct"

# Correct number of block conditions
assert final_dframe.query('condition.str.startswith("c1_")').__len__() == 240
assert final_dframe.query('condition.str.startswith("c2_")').__len__() == 240
assert final_dframe.query('condition.str.startswith("c3_")').__len__() == 240
assert final_dframe.query('condition.str.startswith("c4_")').__len__() == 240
assert final_dframe.query('condition.str.startswith("c5_")').__len__() == 240

# Correct number of words indexs
assert final_dframe.query('condition.str.endswith("_w1")').__len__() == 300
assert final_dframe.query('condition.str.endswith("_w2")').__len__() == 300
assert final_dframe.query('condition.str.endswith("_w3")').__len__() == 300
assert final_dframe.query('condition.str.endswith("_w4")').__len__() == 300

#%% Write Out

write_markerfile(final_dframe, ds_filename=meg_fname)

print('Passed tests - Wrote markerfile')
print(f"{meg_fname}")
