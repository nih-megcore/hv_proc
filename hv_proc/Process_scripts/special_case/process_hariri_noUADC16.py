#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 08:59:50 2020

@author: stoutjd
"""
  
from hv_proc.Process_scripts.trigger_utilities import check_analog_inverted
from hv_proc.Process_scripts.trigger_utilities import (threshold_detect, 
                                                           parse_marks, 
                                                           detect_digital,
                                                           append_conditions)

from hv_proc.utilities import mrk_template_writer
import pandas as pd
import numpy as np
    
def psychopy_logfile_to_dframe(log_file, trial=0):
    dframe=pd.read_csv(log_file, sep='\t', skiprows=2, 
                       names=['onset','DataTxt','Interface'], engine='python')
    tmp_dframe=dframe.Interface.str.split(':', expand=True)
    dframe['condition']=tmp_dframe[0]
    dframe['channel'] = 'logfile'
    dframe['trial']=trial
    dframe=dframe[dframe.condition != 'Keypress'].reset_index(drop=True)
    return dframe[['trial','onset', 'condition', 'channel']]

def coded_frame(dframe, boolean_condition, condition_output_name):
    '''Helper function to cut down on repeating lines of code'''
    col_set = ['trial', 'onset', 'condition', 'channel']
    tmp=dframe[boolean_condition].copy()
    tmp = tmp[col_set]
    tmp.condition = condition_output_name
    return tmp

def main(filename, logfile, write_mrk_file=True):
    '''Main processing function for the NIMH healhty volunteer protocol 
    hariri hammer datasets.  This will pull triggers from the analog channels to 
    extract the subject responses and projector.  The log file is incorporated
    into the processing to determine correct/incorrect responses.  All trigger
    codes are compiled into pandas dataframes and exported to the CTF marker 
    file.
    
    This function is typically called from the commandline or through the 
    hv_process.py function.
    '''
    ################ Code analog and digital MEG events  #####################
    response_l = threshold_detect(dsname=filename, mark='response_l', deadTime=0.5, 
                     derivThresh=0.5, channel='UADC006')
    
    response_r = threshold_detect(dsname=filename, mark='response_r', deadTime=0.5, 
                     derivThresh=0.5, channel='UADC007')    
    
    
    # invert_boolean = check_analog_inverted(filename, ch_name='UADC016')
    # projector = threshold_detect(dsname=filename, mark='projector', deadTime=0.5, 
    #                  derivThresh=0.4, channel='UADC016', invert=invert_boolean)
       
    ppt = detect_digital(filename, channel='UPPT001')
    
    #Remove the response PPT trigger 
    idxs = ppt[ppt.index %3 != 2].index
    ppt = ppt.loc[idxs]
    
    
    ############  Process the log file and interpret conditions ##############
    #Load the log and only keep the encode and probe values
    logdata = psychopy_logfile_to_dframe(logfile)
    logdata=logdata[logdata.condition != 'Correct key pressed']
    logdata=logdata[logdata.condition != 'Fixation']
    logdata=logdata[logdata.condition != 'StartFixation']

    logdata=logdata.reset_index(drop=True)  #Indices for probe are now encode+1
    
    #Correct Logfile timing to the projector
    tmp = logdata.copy(deep=True)
    tmp.condition = 'log_timing'
    tmp = append_conditions([tmp, ppt])
    tmp.loc[tmp.channel == 'UPPT001', 'condition'] = 'ppt_timing'
    new_onsets = parse_marks(tmp, lead_condition='ppt_timing', lag_condition='log_timing',
                             append_result=False, marker_name='correct_onset', 
                             marker_on='lead', window=[-0.5, 0.5])
    new_onsets.dropna(inplace=True)
    
    #Corrected onsets timing must be the same size as original timing
    assert len(logdata) == len(new_onsets) 
    logdata.onset = new_onsets.onset #Set log onsets to projector corrected


    #Code the hariri hammer conditions
    #encode table splits into 4 columns that can be used to determine correct response
    encode_table = logdata.condition.str.split(' ', expand=True)
    logdata['Type'] = encode_table[0] 
    logdata.loc[logdata.Type=='LeftStim', 'Type'] = 'Probe'
    logdata['Gender'] = encode_table[1].str[3:]
    logdata.loc[~logdata.Gender.isin(['Male', 'Fem']), 'Gender']=None
    # Code the choice stim to be both
    logdata['Emotion'] = encode_table[1].str[0:3]
    logdata.loc[~logdata.Emotion.isin(['Hap','Sad']), 'Emotion'] = None
       
    #Determine the correct side for the response by comparing encode and probe
    encode_idxs = encode_table[encode_table[0]=='TopStim'].index
    logdata['correct_response_side']=None
    for encode_idx in encode_idxs:
        #Determine the correct response side from the TopStim
        if encode_table.loc[encode_idx, 1][0:3] == encode_table.loc[encode_idx+1, 1][0:3]:
            logdata.loc[encode_idx+1,'correct_response_side'] = 'probe_left_correct'
        if encode_table.loc[encode_idx, 1][0:3] == encode_table.loc[encode_idx+1, 3][0:3]:
            logdata.loc[encode_idx+1,'correct_response_side'] = 'probe_right_correct'
        copy_vars = ['Emotion', 'Gender']
        logdata.loc[encode_idx+1, copy_vars] = logdata.loc[encode_idx, copy_vars]        
    
    
    col_set = ['trial', 'onset', 'condition', 'channel']
    # Set the expected correct probe response.  
    expected_response = logdata[logdata.Type=='Probe'].copy()
    expected_response.loc[:,'condition'] = expected_response.correct_response_side
    expected_response = expected_response[col_set]
    
    
    ################### Create DataFrames for Logfile Variables ##############
    # Encode Face
    boolean_condition = (logdata.Type=='TopStim') & (logdata.Gender.isin(['Fem', 'Male']))
    encode_face = coded_frame(logdata, boolean_condition, 'encode_face')
    
    # Encode Shape
    boolean_condition = (logdata.Type=='TopStim') & (logdata.Emotion.isna())
    encode_shape = coded_frame(logdata, boolean_condition, 'encode_shape')
    
    # Encode Hap
    boolean_condition = (logdata.Type=='TopStim') & (logdata.Emotion == 'Hap')
    encode_happy = coded_frame(logdata, boolean_condition, 'encode_happy') 
    
    # Encode Sad
    boolean_condition = (logdata.Type=='TopStim') & (logdata.Emotion == 'Sad')
    encode_sad = coded_frame(logdata, boolean_condition, 'encode_sad')
    
    # Encode Female
    boolean_condition = (logdata.Type=='TopStim') & (logdata.Gender == 'Fem')  
    encode_female = coded_frame(logdata, boolean_condition, 'encode_female')
    
    # Encode Male
    boolean_condition = (logdata.Type=='TopStim') & (logdata.Gender == 'Male')  
    encode_male = coded_frame(logdata, boolean_condition, 'encode_male')
    
    # Probe Shape
    boolean_condition = (logdata.Type=='Probe') & (logdata.Gender.isna())  
    probe_shape = coded_frame(logdata, boolean_condition, 'probe_shape')
    
    # Probe Face
    boolean_condition = (logdata.Type=='Probe') & (logdata.Gender.isin(['Male','Fem']))  
    probe_face = coded_frame(logdata, boolean_condition, 'probe_face')
    
    # Probe match_gender
    boolean_condition = (logdata.Type=='Probe') & (logdata.Gender == 'Fem')
    probe_match_female = coded_frame(logdata, boolean_condition, 'probe_match_female')

    boolean_condition = (logdata.Type=='Probe') & (logdata.Gender == 'Male')
    probe_match_male = coded_frame(logdata, boolean_condition, 'probe_match_male')
    
    # Probe match_emotion
    boolean_condition = (logdata.Type=='Probe') & (logdata.Emotion == 'Sad')
    probe_match_sad = coded_frame(logdata, boolean_condition, 'probe_match_sad')

    boolean_condition = (logdata.Type=='Probe') & (logdata.Emotion == 'Hap')
    probe_match_happy = coded_frame(logdata, boolean_condition, 'probe_match_happy')
    
    # Concatenate all logfile conditions
    dframe = append_conditions([response_l, response_r, expected_response,
                encode_shape, encode_face, encode_sad, encode_happy, 
                   encode_female, encode_male, probe_shape, probe_face, 
                   probe_match_happy, probe_match_sad ])
    
  
    ################## Response Processing ###################################
    response_window=[0.1, 1.5]
    response_hits_l = parse_marks(dframe, lead_condition='probe_left_correct', 
                                lag_condition='response_l',
                               marker_name='response_hit',append_result=False, 
                               marker_on='lag', window=response_window)
    response_hits_r = parse_marks(dframe, lead_condition='probe_right_correct', 
                                lag_condition='response_r',
                               marker_name='response_hit',append_result=False, 
                               marker_on='lag', window=response_window)
    response_hits = append_conditions([response_hits_l, response_hits_r])
    response_hits.dropna(inplace=True)
    
    response_misses_l =  parse_marks(dframe, lead_condition='probe_left_correct',
                                   lag_condition='response_l',
                               marker_name='response_miss',append_result=False, 
                               marker_on='lead', null_window=True, window=response_window) 
    response_misses_r =  parse_marks(dframe, lead_condition='probe_right_correct',
                                   lag_condition='response_r',
                               marker_name='response_miss',append_result=False, 
                               marker_on='lead', null_window=True, window=response_window) 
    response_misses = append_conditions([response_misses_l, response_misses_r])     
    response_misses.dropna(inplace=True)    
   
    ############### Finalize dataframe and save to the Markerfile  ###########
    #Add response information to dataframe
    dframe = append_conditions([dframe, response_hits, response_misses]) 
    dframe.dropna(inplace=True)
    
    #Cleanup dataframe to only include the output_vars
    output_vars = ['encode_shape', 'encode_face', 
                   'encode_sad', 'encode_happy', 
                   'encode_female', 'encode_male',
                   'probe_shape', 'probe_face', 
                   'probe_match_happy', 'probe_match_sad',
                   'response_l','response_r','response_hit','response_miss']
    dframe = dframe[dframe.condition.isin(output_vars)]    
    
    if write_mrk_file:
        mrk_template_writer.main(dframe, ds_filename=filename, stim_column='condition')
    else:
        summary=dframe.condition.value_counts()
        print(summary)
        
    
if __name__=='__main__':  
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-logfile', help='Logfile from psychopy')
    parser.add_argument('-ds_filename', help='CTF filename - generally a folder ending in .ds')
    parser.add_argument('-print_stats_only', help='''Process and return the value counts from the dataframe. 
                        Does not write the MarkerFile.mrk''', action='store_true')
    parser.description='''Process Hariri file for HV protocol and create 
    a MarkerFile.mrk in the dataset'''
    
    args = parser.parse_args()
    if not args.ds_filename:
        raise ValueError('No dataset filename provided')
    else:
        filename = args.ds_filename
    
    logfile = None
    if args.logfile:
        log_file=args.logfile
    if args.print_stats_only:
        write_mrk_file=False
    else:
        write_mrk_file=True
    main(filename=filename, logfile=log_file, write_mrk_file=write_mrk_file)
    
    
    
