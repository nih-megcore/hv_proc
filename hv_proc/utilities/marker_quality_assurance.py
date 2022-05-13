#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 12, 2020


Code to be run after processing of triggers and prior to bids process
Loops over all HV protocol datasets and checks the number of triggers vs expected

@author: stoutjd
"""

import mne, glob, copy
import pandas as pd
import numpy as np
import os

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

# def ppt_dataframe(filename):
#     '''Load the parrallel port into a dataframe'''
#     raw = mne.io.read_raw_ctf(filename, verbose=False) 
#     raw.get_data(picks=['UPPT001'])
#     events = mne.event.find_events(raw, stim_channel='UPPT001', verbose=False)
#     dframe=pd.DataFrame(events, columns=['Sample', 'duration', 'description'])
#     dframe['onset']=dframe.Sample/raw.info['sfreq']
#     dframe=dframe.drop('Sample', axis=1)
#     return dframe

####################### SET OF TESTS FOR OUTPUTS ON HV #######################
# These verify that the expected outputs have the right number of triggers
def qa_airpuff(filename=None, logfile=None):
    dframe=annot_dataframe(filename)
    summary=dframe.description.value_counts()
    assert summary.loc['stim'] == 425
    assert summary.loc['missingstim'] == 75

def qa_oddball(filename=None, logfile=None):
    dframe=annot_dataframe(filename)
    summary=dframe.description.value_counts()
    assert summary.loc['standard'] >= 210 
    assert summary.loc['distractor'] == 45
    assert summary.loc['target'] == 45
    assert summary.loc['response_hit']>30
    if 'response_miss' in summary.index:
        assert summary.loc['response_miss']<20
    
def qa_hariri(filename=None, logfile=None):
    '''Load the hariri dataset and verify that the emotional and contrast stims
    sum to the appropriate amount'''
    dframe=annot_dataframe(filename)
    summary=dframe.description.value_counts()
    assert summary[['probe_face', 'probe_shape']].sum() == 150
    assert summary.loc['response_hit'] > 120  #80% accuracy
    assert summary.loc['probe_face'] == 90
    assert summary.loc['encode_face'] == 90
    assert summary.loc['encode_shape'] == 60
    assert summary.loc['probe_shape'] == 60
    assert summary.loc['probe_match_sad'] > 35
    assert summary.loc['probe_match_happy'] > 35
    assert summary.loc[['encode_male', 'encode_female']].sum() == 90
    assert summary.loc[['response_r', 'response_l']].sum() > 120
    
def qa_sternberg(filename=None, logfile=None):
    dframe = annot_dataframe(filename)
    summary=dframe.description.value_counts()
    assert summary.loc['encode4'] == 40
    assert summary.loc['encode6'] == 40
    assert summary.loc['probe_in_set'] == 40
    assert summary.loc['probe_not_in_set'] == 40
    assert summary.loc['response_l'] > 20  
    assert summary.loc['response_r'] > 20 
    assert summary.loc['response_hit'] > 30  #Threshold of 75% correct
    assert summary.loc['response_miss'] < 20
    
def qa_gonogo(filename=None, logfile=None):
    dframe = annot_dataframe(filename)
    summary=dframe.description.value_counts()
    assert summary.loc[['go','nogo']].sum() == 300
    assert summary.loc['go'] > 180
    assert summary.loc['nogo'] > 80
    assert summary.loc['response_hit'] > 150
    assert summary.loc['response_correct_rejection'] > 75
    if 'response_false_alarm' in summary.index:
        assert summary.loc['response_false_alarm'] < 30
    
# def get_filename_match(pattern):
#     '''Return specific filenames that match a pattern'''
#     output = glob.glob(pattern)
#     if len(output) == 1:
#         return output[0]
#     elif len(output) > 1:
#         raise ValueError('More than one match')
#     # elif len(output) == 0:
#     #     return ''
        
        
def get_all_filenames(topdir):
    '''Returns all present filenames in a dictionary for the HV datasets.
    Will return an error if multiple matches'''
    filenames={'airpuff' : glob.glob(os.path.join(topdir, '*airpuff*')),
               'gonogo' : glob.glob(os.path.join(topdir, '*gonogo*')),
               'sternberg' : glob.glob(os.path.join(topdir, '*sternberg*')),
               'hariri' : glob.glob(os.path.join(topdir, '*hariri*')),
               'oddball' : glob.glob(os.path.join(topdir, '*oddball*'))}
    return filenames

def qa_datasets(topdir=None, filenames_dict={}, ignore=[], test_only=[]):
    '''Loop over all datasets found in the topdir folder.
    Tests will be performed on all datasets
    Currently: airpuff, gonogo, sternberg, hariri, oddball
    
    ignore=['list', 'of', 'ignore', 'tests']
    test_only=['list', 'of', 'tests']'''
    if topdir==None and filenames_dict==[]:
        raise ValueError('Must specify the topdir directory or a list of filenames')
    if filenames_dict == {}:
        filenames = get_all_filenames(topdir)
    else:
        filenames = filenames_dict
    
    if len(ignore) > 0:
        for item in ignore:
            filenames.pop(item)
    if len(test_only) > 0:
        filenames = {k: filenames[k] for k in test_only}
   
    for key in filenames.keys():
        # if key in ignore:
        #     continue
        for curr_filename in filenames[key]:
            tmp = 'qa_{}(\'{}\')'.format(key, curr_filename)
            print('Testing: {}'.format(curr_filename))
            try:
                exec(tmp)
            except:
                print('>>> FAILED TEST: {} <<<'.format(tmp))



    
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='''Perform tests on the HV dataset markers:
                                   airpuff, hariri, oddball, sternberg, gonogo''')
    parser.add_argument("-data_folder", help='''Top subject directory.  
                        Typically desinated with a date''')
    parser.add_argument("-ignore", action='append', 
                        help='''Add entries to ignore specific datatypes
                        Multiple ignore flags can be set''')
    parser.add_argument("-test_only", action='append', 
                        help='''Specify a specific datatype to test
                        Multiple test_only flags can be set''')
    parser.add_argument("-print_counts", 
                        help='''Filename of dataset (not folder) to load into a
                        dataframe and print the counts of all the markers.
                        This is helpful to assess test failures''' )
    #parser.add_argument("-write_log", help='', action='store_true')
    args=parser.parse_args()
    

    if args.print_counts:
        filename=args.print_counts
        dframe=annot_dataframe(filename)
        print(dframe.description.value_counts())
        exit(0)

    if not args.data_folder:
        raise IOError('No Dataset provided')
    if args.ignore and args.test_only:
        raise ValueError('Can only use ignore or test_only')
        
    if args.ignore:
        qa_datasets(args.data_folder, ignore=args.ignore)
    elif args.test_only:
        qa_datasets(args.data_folder, test_only=args.test_only)
    else:
        qa_datasets(args.data_folder)
    
