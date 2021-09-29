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

def main(filename, logfile, write_mrk_file=True):
    '''Main processing section for sternberg task analysis of the NIMH MEG
    healthy volunteer data.  This can be called by the command line, but is 
    mainly used upon import to the hv_process.py script.
    
    All triggers are converted to dataframes.  The logfile is imported and 
    time corrected to the projector onset.  
    
    encode4, encode6, probe_in, and probe_out, and response processing are
    calculated and saved to dataframes.
    
    All coded variables are concatenated into a dataframe, dframe.
    dframe is converted to a CTF marker file.
    '''
    ################ Code analog and digital MEG events  #####################
    response_l = threshold_detect(dsname=filename, mark='response_l', deadTime=0.5, 
                     derivThresh=0.5, channel='UADC006')
    
    response_r = threshold_detect(dsname=filename, mark='response_r', deadTime=0.5, 
                     derivThresh=0.5, channel='UADC007')    
    
    
    invert_boolean = check_analog_inverted(filename, ch_name='UADC016')
    projector = threshold_detect(dsname=filename, mark='projector', deadTime=0.5, 
                     derivThresh=0.5, channel='UADC016', invert=invert_boolean)
       
    ppt = detect_digital(filename, channel='UPPT001')
    
    
    ############  Process the log file and interpret conditions ##############
    #Load the log and only keep the encode and probe values
    logdata = psychopy_logfile_to_dframe(logfile)
    logdata = logdata[logdata.condition.str[0:5].isin(['Encod','Probe'])]
    logdata=logdata.reset_index(drop=True)  #Indices for probe are now encode+1
    
    #Correct Logfile timing to the projector
    tmp = logdata.copy(deep=True)
    tmp.condition = 'temp'
    tmp = append_conditions([tmp, projector])
    new_onsets = parse_marks(tmp, lead_condition='projector', lag_condition='temp',
                             append_result=False, marker_name='correct_onset', 
                             marker_on='lead', window=[-0.5, 0.5])
    
    #Corrected onsets timing must be the same size as original timing
    assert len(logdata) == len(new_onsets) 
    logdata.onset = new_onsets.onset #Set log onsets to projector corrected


    #Code the sternberg conditions
    encode_table = logdata.condition.str.split(' ', expand=True)
    logdata['Type'] = encode_table[0] + encode_table[1].apply(len).astype(str)
    logdata['Value'] = encode_table[1]
    
    encode_idxs = encode_table[encode_table[0]=='Encode'].index
    logdata['in_set']=False
    for encode_idx in encode_idxs:
        #If the probe value is in the encode set, set 'in_set' to True
        if logdata.loc[encode_idx+1, 'Value'] in logdata.loc[encode_idx, 'Value']:
            logdata.loc[encode_idx+1,'in_set'] = True
    
    col_set = ['trial', 'onset', 'condition', 'channel']
    #Code in and out of set probes
    in_set_dframe = logdata[logdata.in_set==True][col_set]
    in_set_dframe.condition = 'probe_in_set'
    
    #Encode variables were also set as False, so we must also filter for Probe1
    out_set_dframe = logdata[(logdata.in_set==False)&(logdata.Type=='Probe1')]
    out_set_dframe = out_set_dframe[col_set]
    out_set_dframe.condition = 'probe_not_in_set'
 
    #Code encode 4 and 6 variable working memory sets
    encode4 = logdata[logdata['Type']=='Encode4'][col_set]
    encode4.condition = 'encode4'
    encode6 = logdata[logdata['Type']=='Encode6'][col_set]
    encode6.condition = 'encode6'
    
    dframe = append_conditions([response_l, response_r, projector, ppt,  
                                in_set_dframe, out_set_dframe, 
                                encode4, encode6])
    
    #Code the probe 4 and probe 6 datasets
    probe4_1 = parse_marks(dframe, lead_condition='encode4', 
                           lag_condition='probe_in_set', marker_name='probe4',
                           marker_on='lag', append_result=False, window=[0,7])
    probe4_2 = parse_marks(dframe, lead_condition='encode4', 
                           lag_condition='probe_not_in_set', marker_name='probe4',
                           marker_on='lag', append_result=False, window=[0,7])
    probe4 = append_conditions([probe4_1, probe4_2]).dropna()
    
    probe6_1 = parse_marks(dframe, lead_condition='encode6', 
                           lag_condition='probe_in_set', marker_name='probe6',
                           marker_on='lag', append_result=False, window=[0,7])
    probe6_2 = parse_marks(dframe, lead_condition='encode6', 
                           lag_condition='probe_not_in_set', marker_name='probe6',
                           marker_on='lag', append_result=False, window=[0,7])
    probe6 = append_conditions([probe6_1, probe6_2]).dropna() 
    del probe4_1, probe4_2, probe6_1, probe6_2
    
    dframe = append_conditions([dframe, probe4, probe6]).dropna()
    
    
    ################## Response Processing ###################################
     
    response_window=[0.1, 2.0]
    #Probe is in memory set response processing
    response_hits = parse_marks(dframe, lead_condition='probe_in_set', 
                                lag_condition='response_l',
                               marker_name='response_hit',append_result=False, 
                               marker_on='lag', window=response_window)
    response_hits.dropna(inplace=True)

    response_misses =  parse_marks(dframe, lead_condition='probe_in_set',
                                   lag_condition='response_l',
                               marker_name='response_miss',append_result=False, 
                               marker_on='lead', null_window=True, window=response_window) 
    response_misses.dropna(inplace=True)

    #Probe is not in memory set processing    
    response_false_alarms = parse_marks(dframe, lead_condition='probe_not_in_set',
                                        lag_condition='response_l',
                               marker_name='response_false_alarm',append_result=False, 
                               marker_on='lag', null_window=False, window=response_window) 
    response_false_alarms.dropna(inplace=True)
    
    response_correct_rejections = parse_marks(dframe, lead_condition='probe_not_in_set',
                                              lag_condition='response_r',
                               marker_name='response_correct_rejection',append_result=False, 
                               marker_on='lag', null_window=False, window=response_window) 
    response_correct_rejections.dropna(inplace=True)
    
    
    ############### Finalize dataframe and save to the Markerfile  ###########
    #Add response information to dataframe
    dframe = append_conditions([dframe, response_hits, response_misses,
                                response_false_alarms, response_correct_rejections])
    dframe.dropna(inplace=True)
    
    #Select only certain outputs
    output_vars = ['encode6', 'encode4', 'probe_in_set', 'probe_not_in_set',
                   'probe4', 'probe6',
                   'response_l','response_r','response_correct_rejection',
                   'response_hit','response_miss','response_false_alarm']
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
    parser.add_argument('-print_stats_only', help='''Process and print stimuli/trigger counts
                        without writing the MarkerFile.mrk''', action='store_true')
    parser.description='''Process Sternberg file for HV protocol '''
    
    args = parser.parse_args()
    if not args.ds_filename:
        raise ValueError('No dataset filename provided')
    else:
        filename = args.ds_filename
    if args.logfile:
        log_file=args.logfile
    
    if args.print_stats_only:
        write_mrk_file=False
    else:
        write_mrk_file=True
    
    main(filename, log_file, write_mrk_file)

   
