#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 10:02:20 2020

@author: stoutjd
"""


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

# def clear_delay_columns(dframe):
#     drop_cols=dframe.columns[dframe.columns.str[0:5]=='delay']
#     dframe.drop(drop_cols, axis=1, inplace=True)
#     return dframe
        
# def test_clear_delay_columns():
#     dframe=pd.DataFrame(columns=['delay', 'delay_1>test', 'dont_drop'])
#     dframe=clear_delay_columns(dframe)
#     assert 'dont_drop' in dframe.columns
#     assert 'delay' not in dframe.columns
#     assert 'delay_1>test' not in dframe.columns

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
        
def print_oddball_stats(filename, write_csv=None):
    '''Load the datasets and by annotation and the parrallel port
    Combine  and calculate the delay'''
    dframe1=annot_dataframe(filename)
    dframe2=ppt_dataframe(filename)
    
    dframe_tot=pd.concat([dframe1, dframe2])
    dframe_tot = dframe_tot.sort_values('onset')
    dframe_tot.reset_index(inplace=True, drop=True)
    
    dframe_tot=calc_delay(dframe_tot, 'tone1', 'standard')
    dframe_tot=calc_delay(dframe_tot, 'tone2', 'target')
    dframe_tot=calc_delay(dframe_tot, 'static', 'distractor')
    # dframe_tot=
    # dframe_tot=
    
    
    if write_csv == True:
        import os
        basefilename=os.path.basename(filename)
        hash_id=basefilename.split('_')[0]
        print(hash_id)
        dframe_tot.to_csv(hash_id+'_oddball.csv', index=False)
    
    print('Value counts from dataset:')
    print('--------------------------')
    print(dframe_tot.description.value_counts())
    print('\n')
    summary = print_ave_delay(dframe_tot, return_dframe=True)
    print('\n')
    
    #Evaluate the counts on delay evaluation
    verify_values(summary, measure='count', col_name='delay_tone1>standard', 
                  expected=210, indicator='Warning')
    verify_values(summary, measure='count', col_name='delay_tone2>target',
                  expected=45, indicator='Warning')
    verify_values(summary, measure='count', col_name='delay_static>distractor', 
                  expected=45, indicator='Warning')
    
    #Evaluate the mean delay
    verify_values(summary, measure='mean', col_name='delay_tone1>standard', 
                  expected=0.07, fail_operator=np.greater, indicator='Warning')
    verify_values(summary, measure='mean', col_name='delay_tone2>target', 
                  expected=0.07, fail_operator=np.greater, indicator='Warning')    
    verify_values(summary, measure='mean', col_name='delay_static>distractor', 
                  expected=0.07, fail_operator=np.greater, indicator='Warning')    
    
if __name__=='__main__':
    import sys
    oddball_process(sys.argv[1])
