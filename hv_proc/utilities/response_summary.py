#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 10:02:20 2020

@author: stoutjd
"""

import os
import mne, glob, copy
import pandas as pd
import numpy as np

def convert_annotations_to_dframe(annot):
    '''Code snippet pulled from mne python mne.annotations._annotations_to_csv()'''
    df = pd.DataFrame(dict(onset=annot.onset, duration=annot.duration,
                           description=annot.description)) 
    return df

def annot_dataframe(filename):
    '''Loads the filename and returns a dataframe'''
    raw = mne.io.read_raw_ctf(filename, verbose=False) 
    annot = raw.annotations
    dataframe = convert_annotations_to_dframe(annot)
    return dataframe

def ppt_dataframe(filename):
    '''Load the parrallel port into a dataframe'''
    raw = mne.io.read_raw_ctf(filename, verbose=False) 
    raw.get_data(picks=['UPPT001'])
    events = mne.event.find_events(raw, stim_channel='UPPT001', verbose=False)
    dframe=pd.DataFrame(events, columns=['Sample', 'duration', 'description'])
    dframe['onset']=dframe.Sample/raw.info['sfreq']
    dframe=dframe.drop('Sample', axis=1)
    return dframe

def calc_delay(dframe, lead_name, lag_name, max_delay=0.5):
    '''Calculate the delay between a leading stimulus and a lagging time
    This will not work in reverse'''
    delay_dframe = dframe[dframe.description.isin([lead_name,lag_name]) ].copy()
    delay_dframe.reset_index(inplace=True)
    lead_idxs = delay_dframe[delay_dframe.description==lead_name].index
    lag_idxs = delay_dframe[delay_dframe.description==lag_name].index
    
    delay_column='delay_'+str(lead_name)+'>'+str(lag_name)
    
    for idx in delay_dframe.index:
        if idx in lead_idxs:
            if idx+1 in lag_idxs:
                delay_val=delay_dframe.loc[idx+1, 'onset'] - delay_dframe.loc[idx, 'onset']
                if delay_val < max_delay:
                    delay_dframe.loc[idx+1, delay_column]=delay_val
    #Load the values into the original idices of the dataframe
    dframe.loc[delay_dframe['index'].values, delay_column] =  delay_dframe[delay_column].values   
    return dframe      

def print_ave_delay(dframe, return_dframe=False):
    '''Print the summary information on the delay columns'''
    delay_cols=dframe.columns[dframe.columns.str[0:5]=='delay']
    print('Average delays are in seconds rounded to 3 sig digits')
    print('-----------------------------------------------------')
    summary=dframe.loc[:,delay_cols].agg([np.mean, np.std, np.min, np.max]).round(3)
    summary.loc['count']=dframe.loc[:,delay_cols].count().astype(int)
    print(summary)
    if return_dframe==True:
        return summary
    
def verify_values(summary_dframe, measure=None, col_name=None, expected=None,
                  fail_operator=np.not_equal, indicator='Error'):
    '''Check that the values are appropriate
    Indicator can be an Error or Warning
    Operator will provide the boolean logic.  Provide a function - typically numpy
    operators: np.equal, np.less, np.greater, np.greater_equal... etc'''
    actual_val=summary_dframe.loc[measure, col_name]
    if fail_operator(actual_val, expected):
        if indicator=='Error':
            raise ValueError('{}_{} does not match expected'.format(measure, col_name))
        if indicator=='Warning':
            print('WARNING: ({}) {} does not match expected values:\n Found {} - Expected {}'\
                  .format(measure, col_name, actual_val, expected))


def print_response_stats(dframe):
    print('Value counts from dataset:')
    print('--------------------------')
    print(dframe.description.value_counts())
    print('\n')
    print_ave_delay(dframe, return_dframe=False)
    print('\n')



###########  Task specific analysis  ###################    
pd.options.display.max_columns=7

def print_airpuff_stats(filename):
    '''Print the trigger counts for the airpuff task'''
    dframe = annot_dataframe(filename)    
    print('Value counts from dataset:')
    print('--------------------------')
    print(dframe.description.value_counts())
    print('\n')

    
def print_gonogo_stats(filename):
    '''Return the response statistics for the go nogo task'''
    dframe = annot_dataframe(filename)
    dframe = calc_delay(dframe, 'go', 'response_hit', max_delay=1.0)
    dframe = calc_delay(dframe, 'nogo', 'response_false_alarm', max_delay=1.0)
    print_response_stats(dframe)

def print_hariri_stats(filename, return_dframe=False):
    '''Return the response statistics for the hariri task'''
    dframe = annot_dataframe(filename)
    delay_val = 2.0
    dframe = calc_delay(dframe, 'probe_shape', 'response_hit', 
                        max_delay=delay_val)
    dframe = calc_delay(dframe, 'probe_face', 'response_hit', 
                        max_delay=delay_val)
    dframe = calc_delay(dframe, 'probe_match_happy', 'response_hit',
                        max_delay=delay_val)
    dframe = calc_delay(dframe, 'probe_match_sad', 'response_hit', 
                        max_delay=delay_val)
    print_response_stats(dframe)
    if return_dframe:
        return dframe

def make_project_response_stats(bids_root=None, 
    outfname=None, task=None):
    '''Loop over file list and extract response times - 
    Compile the results into a dataframe and save to csv'''
    dframe_list=[]
    fnames=glob.glob(f'{bids_root}/sub-*/ses-01/meg/*{task}*.ds')
    stats_list = []
    for fname in fnames:
        subjid=os.path.basename(fname).split('sub-')[-1].split('_')[0]
        dframe=print_hariri_stats(fname, return_dframe=True)
        summary=print_ave_delay(dframe, return_dframe=True)
        summaryT=summary.transpose()
        summaryT=summaryT.reset_index().rename(columns=dict(index='condition'))
        summaryT['subject']=subjid
        stats_list.append(summaryT)
    all_stats=pd.concat(stats_list)
    all_stats.reset_index(drop=True)
    if not os.path.splitext(outfname)[-1] == '.csv':
        outfname=outfname+'.csv'
    all_stats.to_csv(outfname, index=False)

def print_sternberg_stats(filename):
    '''Print the response statistics for the sternberg task'''
    dframe = annot_dataframe(filename)
    delay_val = 2.0
    dframe = calc_delay(dframe, 'probe4', 'response_hit', 
                        max_delay=delay_val)
    dframe = calc_delay(dframe, 'probe6', 'response_hit', 
                        max_delay=delay_val)
    print_response_stats(dframe)
    
def print_oddball_stats(filename):
    '''Load the datasets and by annotation and the parrallel port
    Combine  and calculate the delay'''
    dframe=annot_dataframe(filename)
    delay_val = 0.7
    dframe=calc_delay(dframe, 'target', 'resp_correct',
                          max_delay=delay_val)
    print_response_stats(dframe)
    
# if __name__=='__main__':
#     import sys
#     oddball_process(sys.argv[1])
