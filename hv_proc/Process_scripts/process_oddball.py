#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 17:06:57 2020

@author: stoutjd
"""


import mne, os, shutil
import numpy as np
import pyctf
# from hv_proc.Process_scripts.oddball_BIDSmarking_mod import process_single_dataset
from hv_proc.utilities.oddball_marker_summary import print_oddball_stats

from hv_proc.Process_scripts.trigger_utilities import (threshold_detect, 
                                                           parse_marks, 
                                                           detect_digital,
                                                           append_conditions)

from hv_proc.utilities.mrk_template_writer import main as write_mrk_file

def squash_max(filename, channel_name='UADC003-2104'):
    '''The tone stim data is outside of the nyquist frequency, therefore
    the amplitude is much smaller than the broadband noise stimuli.
    During processing this causes filter rolloff on the noise stimuli to 
    drift into the other stimuli.  To prevent the tone stimuli is processed 
    separately and noise epochs are zeroed'''
    raw = mne.io.read_raw_ctf(filename, preload=True, verbose=False)
    events = mne.find_events(raw, stim_channel='UPPT001', verbose=False)
    raw.pick_channels(ch_names=[channel_name])
    raw.filter(1,None, picks=channel_name, verbose=False)
    noise_events = events[events[:,2]==3]
    noise_trigger_times = [i[0] for i in noise_events]
    
    for i in noise_trigger_times:
        '''Blank values between 0 and 200 ms post PPT trigger
        for the static stimuli'''
        onset_index= i + 0 #int(i+ .02*raw.info['sfreq'])
        offset_index=int(i + .2*raw.info['sfreq'])
        raw._data[0,range(onset_index, offset_index)] = 0
    return raw

def return_psuedo_z_transformed(filename):
    '''Evaluate a z transform (psuedo) of the data using the mean and std from 
    the bottom 10% of data.
    '''
    
    raw = squash_max(filename)
    # raw = mne.io.read_raw_ctf(filename, preload=True)
    # raw.pick_channels(['UADC003-2104'])
    raw.notch_filter([60,120,180], picks=['UADC003-2104'])
    #raw.filter(1,None, picks=['UADC003-2104'])
    
    raw._data = np.abs(raw._data)
    hist = np.histogram(raw._data, bins=10)
    
    noise_mean = raw._data[raw._data < hist[1][1]].mean()
    noise_std = raw._data[raw._data < hist[1][1]].std()
    
    import copy
    fake_z = (copy.deepcopy(raw._data)-noise_mean) / noise_std
    raw._data = fake_z
    return raw

def transform_write_dsfile(filename, ch_name='UADC003'):
    '''Transform the analog channel and write it into the CTF dataset
    This should be performed on a copy of the dataset as it will permanently
    change the data'''
    raw=return_psuedo_z_transformed(filename)
    ds = pyctf.dsopen(filename)
    ch_idx=ds.channel[ch_name]
    stim_replace = raw._data * 100000 #/ ds.getChannelGain(ch_idx)
    ds.dsData.w[0,ch_idx,:] = stim_replace.astype(np.int32)[0,:].byteswap() 
    ds.close()
    
def copy_data(filename, full_path=False):
    '''Since the data will be modified in place and the trigger will be overwritten
    The data must be copied and deleted after processing
    
    Returns path of copied file'''
    if not os.path.exists('./tmp'): os.mkdir('./tmp')
    
    basename=os.path.basename(filename)
    proc_filename = os.path.join('./tmp', basename) 
    if full_path == True:
        proc_filename = os.path.join(os.path.dirname(filename), proc_filename)
    shutil.copytree(filename, proc_filename)
    return proc_filename

def delete_process_folder(proc_filename):
    '''Deletes the temporary folder created to process the data'''
    if proc_filename[:6] == './tmp/':
        print('Removing temporary folder: {}'.format(proc_filename))
        shutil.rmtree(proc_filename)
    else:
        raise Exception('''The folder does not start with tmp_, so it will not be
                        deleted''')    
                        
def copy_marker(filename, proc_filename):
    '''Copy the marker file from the process dataset to the original dataset'''
    orig_mrk = os.path.join(filename, 'MarkerFile.mrk')
    proc_mrk = os.path.join(proc_filename, 'MarkerFile.mrk')
    if os.path.exists(orig_mrk):
        os.remove(orig_mrk)
    shutil.copy(proc_mrk, orig_mrk)
    
def process_single_dataset(filename):
    response = threshold_detect(dsname=filename, mark='response', deadTime=0.5, 
                     derivThresh=0.5, channel='UADC005')

    ppt = detect_digital(filename, channel='UPPT001')
    
    dframe = append_conditions([response, ppt])

    dframe.loc[dframe['condition']=='1', 'condition'] = 'standard'
    dframe.loc[dframe['condition']=='2', 'condition'] = 'target'
    dframe.loc[dframe['condition']=='3', 'condition'] = 'distractor'
    
    #Add auditory delay to all auditory components
    auditory_delay = 0.048
    idxs = dframe[dframe.condition.isin(['standard', 'target', 'distractor'])].index
    dframe.loc[idxs, 'onset'] = dframe.loc[idxs, 'onset'] + auditory_delay
    
    dframe = parse_marks(dframe, marker_name='response_hit', lead_condition='target',
                         lag_condition='response', window=[0, 0.95], marker_on='lag')    
    
    dframe = parse_marks(dframe, marker_name='response_miss', lead_condition='target',
                         lag_condition='response', window=[0, 0.95], null_window=True, marker_on='lead')
    
    # =========================================================================
    # All codes are now derived from the PPT trigger w/added delay-no UADC used
    # =========================================================================
    
    # dframe = parse_marks(dframe, marker_name='beep', lead_condition='tonestim', 
    #                      lag_condition='noise', window=[-0.5, 0.5], 
    #                      null_window=True, marker_on='lead')
                        
    # dframe = parse_marks(dframe, marker_name='standard', lead_condition='beep', 
    #                      lag_condition='tone1', window=[-0.25, 0], marker_on='lag')
    
    # dframe = parse_marks(dframe, marker_name='target', lead_condition='beep', 
    #                     lag_condition='tone2', window=[-0.5, 0], marker_on='lag')
    
    # dframe = parse_marks(dframe, marker_name='distractor', lead_condition='noise',
    #                      lag_condition='static', window=[-0.5, 0], marker_on='lag')
    
    ############### Finalize dataframe and save to the Markerfile  ###########
    #Add response information to dataframe
    dframe.dropna(inplace=True)
    
    #Cleanup dataframe to only include the output_vars
    output_vars = ['standard', 'target', 'distractor',
                   'response','response_hit','response_miss']
    dframe = dframe[dframe.condition.isin(output_vars)]  
    

    
    dframe.dropna(inplace=True)
    write_mrk_file(dframe, ds_filename=filename, stim_column='condition')
    print(f'Completed: {filename}')


    
def main(filename=None, remove_process_folder=False):
    '''Process the oddball triggers.  This function replicates some of the 
    functionality in the cmdline portion. '''
    # proc_filename = copy_data(filename)
    # transform_write_dsfile(proc_filename)
    process_single_dataset(filename) 
    # copy_marker(filename, proc_filename)
    # if remove_process_folder == True:
    #     delete_process_folder(proc_filename)

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', help='Delete the temporary file created during processing',
                        action='store_true')
    parser.add_argument('filename', nargs='?',
                        help='Filename - must be last entry in commandline')
    parser.add_argument('-display', help='Display the output statistics from the processing',
                        action='store_true')
    parser.add_argument('-save_stats', help='''Write a csv dataframe to the current directory with
                        the name HASHID_oddball.csv''', action='store_true')
    args=parser.parse_args()

    # import sys
    filename=args.filename
    process_single_dataset(filename)
    # main(filename, remove_process_folder=args.d)

    # Write out the results to csv file.  Is called through the display function
    # Must set the display variable as true too
    if args.save_stats:
        save_stats = True
        args.display = True
    else:
        save_stats = False
    
    if args.display:
        print_oddball_stats(filename, write_csv=save_stats)
        if save_stats == True: print('Saving the stim dataframe to {}'.format(filename.split('_')[0]+'_oddball.csv'))
        
        
