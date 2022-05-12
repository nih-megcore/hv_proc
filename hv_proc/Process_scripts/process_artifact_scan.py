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

def main(filename=None, logfile=None, write_mrk_file=True):
    '''Code for processing the healthy volunteer protocol artifact scan
    This is typically called from the commandline call or through
    the hv_process.py command at the top of the package.
    '''
       
    ppt = detect_digital(filename, channel='UPPT001')
    ppt.loc[ppt.condition=='1','condition'] ='blink'
    ppt.loc[ppt.condition=='2','condition']='eyemoveHoriz'
    ppt.loc[ppt.condition=='3','condition']='eyemoveVert'
    ppt.loc[ppt.condition=='4','condition']='jawclench'
    ppt.loc[ppt.condition=='5','condition']='swallow'
    ppt.loc[ppt.condition=='6','condition']='breath'
    
    dframe = ppt
    dframe.dropna(inplace=True)
    
    #Filter output conditions
    output_conditions = ['blink', 'eyemoveHoriz','eyemoveVert','jawclench',
                         'swallow','breath']
    dframe = dframe[dframe.condition.isin(output_conditions)]
    
    if write_mrk_file:
        mrk_template_writer.main(dframe, ds_filename=filename, stim_column='condition')
    else:
        summary=dframe.condition.value_counts()
        print(summary)
        
if __name__=='__main__':    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-ds_filename', help='CTF filename - generally a folder ending in .ds')
    parser.description='''Process Artifact file for HV protocol and create 
    a dataframe in the output folder'''
    
    args = parser.parse_args()
    if not args.ds_filename:
        raise ValueError('No dataset filename provided')
    else:
        filename = args.ds_filename
    
    write_mrk_file=True
    main(filename=filename, write_mrk_file=write_mrk_file)
        
