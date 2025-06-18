#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 16 17:14:14 2025

@author: jstout
"""

import os, os.path as op
import pytest 
from hv_proc.hv_process import get_subject_datasets, filter_list_by_task, get_logfile


test_logfile_dir = op.expanduser('~/nihmeg_test_data/HVDATA/v2.0.0/logfiles')
os.environ['hv_logfile_path'] = test_logfile_dir
test_data_dir = op.expanduser('~/nihmeg_test_data/HVDATA/v2.0.0') 
os.environ['hv_meg_path'] = test_data_dir

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
    assert gt_mid == get_logfile('CDCDCDCD', task='MID', logfile_path=test_logfile_dir)
    gt_flank = f'{test_logfile_dir}/CDCDCDCD/CDCDCDCD_Flanker_run_0001-01-01_01h01.01.001.csv'
    assert gt_flank == get_logfile('CDCDCDCD', task='flanker', logfile_path=test_logfile_dir)    
    gt_ling = f'{test_logfile_dir}/CDCDCDCD/CDCDCDCD_LingTask_Seq1_01010001_010101.csv'
    assert gt_ling == get_logfile('CDCDCDCD', task='lingtask', logfile_path=test_logfile_dir)    
        
    
    
    
