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
 
def main(filename=None, logfile=None, write_mrk_file=True):
    '''Code for processing the healthy volunteer protocol go/nogo task
    This is typically called from the commandline call or through
    the hv_process.py command at the top of the package.
    
    Timing is adjusted for all visual stimuli to the projector onset.
    Response, logfile, parrallel port, and projector onset information are loaded
    into a dataframe and concatenated.
    
    Response information is coded as follows:
        response_hits - correct go responses
        response_misses - go stimuli that did not have a response
        response_false_alarms - nogo stimuli followed by a response (incorrect)
        response_correct_rejections - nogo stimuli followed by no response'''
        
    response = threshold_detect(dsname=filename, mark='response', deadTime=0.5, 
                     derivThresh=0.5, channel='UADC005')
    
    invert_boolean = check_analog_inverted(filename, ch_name='UADC016')
    projector = threshold_detect(dsname=filename, mark='projector', deadTime=0.5, 
                     derivThresh=0.5, channel='UADC016', invert=invert_boolean)
       
    ppt = detect_digital(filename, channel='UPPT001')
    
    logdata = psychopy_logfile_to_dframe(logfile)
    
    dframe = append_conditions([response, projector, ppt, logdata])

    #Correct parrallel port timing and add Go conditions
    dframe = parse_marks(dframe, marker_name='go', lead_condition='projector', 
                 lag_condition='1', window=[-0.5, 0.5], marker_on='lead')
    
    #Correct parrallel port timing for NoGo conditions
    dframe = parse_marks(dframe, marker_name='nogo', lead_condition='projector', 
                 lag_condition='2', window=[-0.5, 0.5], marker_on='lead')
    dframe.dropna(inplace=True)
    
    #Conditions in the log file need to be corrected to the projector timing
    for stim in ['triangle', 'diamond', 'pentagon', 'circle', 'square',
         'triangle_x', 'diamond_x', 'pentagon_x', 'circle_x', 'square_x']:
        sub_frame = dframe[dframe['condition'].isin([stim, 'projector'])]
        stim_idxs = dframe[dframe['condition']==stim].index
        tmp = parse_marks(sub_frame, marker_name='temp', lead_condition='projector', 
                         lag_condition=stim, window=[-0.5, 0.5], 
                         marker_on='lead')
        #Parsemarks creates lots of misses - those values must be dropped
        corrected_onset_times = tmp[tmp.condition=='temp'].dropna()['onset'].values
        #Corrected timings are then put back into the original log condition onsets
        dframe.loc[stim_idxs, 'onset'] = corrected_onset_times
        
    response_window=[0.1, 1.0]
    #Go response processing
    response_hits = parse_marks(dframe, lead_condition='go', lag_condition='response',
                               marker_name='response_hit',append_result=False, 
                               marker_on='lag', window=response_window)
    response_hits.dropna(inplace=True)

    response_misses =  parse_marks(dframe, lead_condition='go', lag_condition='response',
                               marker_name='response_miss',append_result=False, 
                               marker_on='lead', null_window=True, window=response_window) 
    response_misses.dropna(inplace=True)

    #Nogo response processing    
    response_false_alarms = parse_marks(dframe, lead_condition='nogo', lag_condition='response',
                               marker_name='response_false_alarm',append_result=False, 
                               marker_on='lag', null_window=False, window=response_window) 
    response_false_alarms.dropna(inplace=True)
    
    response_correct_rejections = parse_marks(dframe, lead_condition='nogo', lag_condition='response',
                               marker_name='response_correct_rejection',append_result=False, 
                               marker_on='lead', null_window=True, window=response_window) 
    response_correct_rejections.dropna(inplace=True)
    
    #Add response information to dataframe
    dframe = append_conditions([dframe, response_hits, response_misses,
                                response_false_alarms, response_correct_rejections])
    dframe.dropna(inplace=True)
    
    #Filter output conditions
    output_conditions = ['go','nogo',
                        'response', 'response_hit','response_correct_rejection',
                        'response_false_alarm','response_miss']
    dframe = dframe[dframe.condition.isin(output_conditions)]
    
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
    parser.description='''Process Go-Nogo file for HV protocol and create 
    a dataframe in the output folder'''
    
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
        
