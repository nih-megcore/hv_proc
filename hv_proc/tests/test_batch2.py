#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 17:14:14 2025

@author: jstout
"""

import os, os.path as op
import pytest 
import mne
import pandas as pd
import subprocess

test_logfile_dir = op.expanduser('~/nihmeg_test_data/HVDATA/v2.0.0/logfiles')
os.environ['hv_logfile_path'] = test_logfile_dir
test_data_dir = op.expanduser('~/nihmeg_test_data/HVDATA/v2.0.0') 
os.environ['hv_meg_path'] = test_data_dir

# Import of main must be set after the os.environ has been set
from hv_proc.hv_process import main
from hv_proc.hv_process import get_subject_datasets, filter_list_by_task, get_logfile


subject_dsets = get_subject_datasets('CDCDCDCD', meg_path=test_data_dir)

@pytest.fixture(scope='session')
def test_dir(tmp_path_factory):
    out_dir = tmp_path_factory.getbasetemp()
    return out_dir        

def test_get_subjects_datsets(test_dir):
    gt = ['01010001/CDCDCDCD_EmptyRoom6m_01010001_001.ds',
     '01010001/CDCDCDCD_poeppel_01010001_004.ds',
     '01010001/CDCDCDCD_artifact_01010001_001.ds',
     '01010001/CDCDCDCD_artifact_01010001_002.ds',
     '01010001/CDCDCDCD_flanker_01010001_008.ds',
     '01010001/CDCDCDCD_MID_01010001_006.ds',
     '01010001/CDCDCDCD_rest_01010001_007.ds',
     '01010001/CDCDCDCD_movie_01010001_003.ds',
     '01010001/CDCDCDCD_rest_01010001_003.ds']
    
    gt = [op.join(test_data_dir, i) for i in gt]
    
    _test_data = get_subject_datasets('CDCDCDCD', meg_path=test_data_dir)
    assert len(gt)==len(_test_data)
    for test_path in gt:
        assert test_path in gt
    
def test_filter_list_by_task(test_dir):
    filename_list = ['01010001/CDCDCDCD_EmptyRoom6m_01010001_001.ds',
     '01010001/CDCDCDCD_poeppel_01010001_004.ds',
     '01010001/CDCDCDCD_artifact_01010001_001.ds',
     '01010001/CDCDCDCD_artifact_01010001_002.ds',
     '01010001/CDCDCDCD_flanker_01010001_008.ds',
     '01010001/CDCDCDCD_MID_01010001_006.ds',
     '01010001/CDCDCDCD_rest_01010001_007.ds',
     '01010001/CDCDCDCD_movie_01010001_003.ds',
     '01010001/CDCDCDCD_rest_01010001_003.ds']
    
    gt_MID = ['01010001/CDCDCDCD_MID_01010001_006.ds']
    assert gt_MID == filter_list_by_task(filename_list, task='MID')
    gt_flank = ['01010001/CDCDCDCD_flanker_01010001_008.ds']
    assert gt_flank == filter_list_by_task(filename_list, task='flanker')
    
def test_get_logfile(test_dir):
    gt_mid = f'{test_logfile_dir}/CDCDCDCD/CDCDCDCD_MID_0101001_010101.csv'
    assert gt_mid == get_logfile('CDCDCDCD', task='mid', logfile_path=test_logfile_dir)
    gt_flank = f'{test_logfile_dir}/CDCDCDCD/CDCDCDCD_Flanker_run_0001-01-01_01h01.01.001.csv'
    assert gt_flank == get_logfile('CDCDCDCD', task='flanker', logfile_path=test_logfile_dir)    
    gt_ling = f'{test_logfile_dir}/CDCDCDCD/CDCDCDCD_LingTask_Seq1_01010001_010101.csv'
    assert gt_ling == get_logfile('CDCDCDCD', task='lingtask', logfile_path=test_logfile_dir)    
    

##
class test_args():
    def __init__(self, task=None):
        self.subjid='CDCDCDCD'
        full_list = ['airpuff','hariri','gonogo','artifact','sternberg','oddball', 
                     'flanker','lingtask','mid']
        full_list.remove(task)
        setattr(self, task, True)
        for nulltask in full_list:
            setattr(self, nulltask, False)
            
        self.print_stim_counts=None 
            
def test_flanker():
    taskfile = filter_list_by_task(subject_dsets, task='flanker')[0]
    mrkfile = op.join(taskfile, 'MarkerFile.mrk')
    if op.exists(mrkfile):
        os.remove(mrkfile)
    args = test_args(task='flanker')
    main(args)
    
    assert op.exists(mrkfile)
    raw = mne.io.read_raw_ctf(taskfile, preload=False, system_clock='ignore')
    dframe = pd.DataFrame(raw.annotations)
    value_dict = dict(dframe.description.value_counts())
    gt_dict = {'fixation': 160,
                 'correct_response': 55,
                 'right_response': 55,
                 'left_response': 52,
                 'incorrect_response': 45,
                 'right_incongruent': 40,
                 'left_congruent': 40,
                 'left_incongruent': 40,
                 'right_congruent': 40}
    for key in gt_dict.keys():
        assert gt_dict[key]==value_dict[key]
    
    
def test_lingtask():
    taskfile = filter_list_by_task(subject_dsets, task='poeppel')[0]
    mrkfile = op.join(taskfile, 'MarkerFile.mrk')
    if op.exists(mrkfile):
        os.remove(mrkfile)    
    
    args = test_args(task='lingtask')
    main(args)
    assert op.exists(mrkfile)
    raw = mne.io.read_raw_ctf(taskfile, preload=False, system_clock='ignore')
    dframe = pd.DataFrame(raw.annotations)
    value_dict = dict(dframe.description.value_counts())
    
    _gt_file = op.join(op.dirname(__file__), 'test_outputs','lingtask_dframe.csv')
    _gt_dframe = pd.read_csv(_gt_file)
    gt_dict = dict(_gt_dframe.description.value_counts())
    for key in gt_dict.keys():
        assert gt_dict[key]==value_dict[key]    
    
    

def test_mid():
    taskfile = filter_list_by_task(subject_dsets, task='MID')[0]
    mrkfile = op.join(taskfile, 'MarkerFile.mrk')
    if op.exists(mrkfile):
        os.remove(mrkfile)    
    
    args = test_args(task='mid')
    main(args)
    assert op.exists(mrkfile)
    raw = mne.io.read_raw_ctf(taskfile, preload=False, system_clock='ignore')
    dframe = pd.DataFrame(raw.annotations)
    value_dict = dict(dframe.description.value_counts())
    gt_dict = {'cue_neutral': 38,
             'target_neutral': 38,
             'cue_win': 38,
             'target_win': 38,
             'cue_loss': 38,
             'target_loss': 38,
             'response_loss': 32,
             'response_win': 28,
             'response_neutral': 27}
    for key in gt_dict.keys():
        assert gt_dict[key]==value_dict[key]
    



    
