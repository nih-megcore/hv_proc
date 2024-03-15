#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 10:18:55 2020

@author: stoutjd
"""

from hv_proc.Process_scripts.trigger_utilities import *
from hv_proc.utilities.mrk_template_writer import main as mrk_file_writer

def airpuff_triggers_to_dframe(filename):
    invert_trigger = check_analog_inverted(filename, ch_name='UADC001')
    airpuff=threshold_detect(dsname=filename, channel='UADC001', mark='Trigger',
                          invert=invert_trigger)
    ppt = detect_digital(filename, channel='UPPT001')
    dframe = append_conditions([ppt, airpuff])
    
    dframe = parse_marks(dframe, marker_name='stim', lead_condition='1', 
                         lag_condition='Trigger', marker_on='lag', window=[0, 0.5]) 
    
    #Adjust time lag from stim to airpuff
    airpuff_lag = 0.042   
    airpuff_indices = dframe[dframe['condition']=='stim'].index
    dframe.loc[airpuff_indices, 'onset'] += airpuff_lag
    
    #Calculate the timing of the expected missed stim
    missed_stims = dframe[dframe['condition']=='2'].copy(deep=True)
    missed_stims['condition'] = 'missingstim'
    missed_stims['onset']+=airpuff_lag
    dframe = append_conditions([dframe, missed_stims])
    
    final_outputs = ['stim', 'missingstim']
    dframe=dframe[dframe.condition.isin(final_outputs)]
    return dframe


def main(filename, write_mrk_file=True):
    dframe = airpuff_triggers_to_dframe(filename)
    if write_mrk_file == True:
        mrk_file_writer(dframe=dframe, ds_filename=filename, mrk_output_file=None, 
                    stim_column='condition')
    else:
        print(dframe.condition.value_counts())
    

if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Process airpuff data for the healthy volunteer protocol')
    parser.add_argument('-filename', help='Airpuff dataset')
    parser.add_argument('-dont_save_mrk', 
                        help='''Default is to save the marker file.  Set this to
                        ignore the default and print the number of outputs''',
                        action='store_true')
    args=parser.parse_args()
    if not args.filename:
        raise ValueError('No input filename provided')
    if args.dont_save_mrk:
        main(args.filename, write_mrk_file=False)
    else:
        main(args.filename)
                        

    

     