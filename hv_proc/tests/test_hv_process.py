#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 10:39:12 2020

@author: stoutjd
"""


 
from ..hv_process import *

#Some Tests
def return_null_test_args():
    import argparse
    args = argparse.Namespace()
    args.subjid = None
    args.airpuff = None
    args.hariri = None
    args.sternberg = None
    args.gonogo = None
    args.QA_task = None
    args.QA_all = None    
    args.oddball = None
    args.print_stim_counts = []
    args.scrub_openneuro = None
    return args

def test_oddball_call():
    args = return_null_test_args()
    args.subjid='SUBJID'
    args.oddball = True
    args.QA_task = 'oddball'
    main(args)
    
def test_airpuff():
    args = return_null_test_args()
    args.subjid='SUBJID'
    args.airpuff = True
    args.QA_task = 'airpuff'
    main(args)
    
def test_hariri():
    args = return_null_test_args()
    args.subjid='SUBJID'
    args.hariri = True
    args.QA_task = 'hariri'
    main(args)
    
def test_sternberg():
    args = return_null_test_args()
    args.subjid='SUBJID'
    args.sternberg = True
    args.QA_task = 'sternberg'
    main(args)  

def test_gonogo():
    args = return_null_test_args()
    args.subjid='SUBJID'
    args.gonogo = True
    args.QA_task = 'gonogo'
    main(args)  

def test_get_logfile():
    subjid='SUBJID'
    logfile_path='/data/logfiles'  #Change this path if on biowulf
    sternberg_log=get_logfile(subjid, task='sternberg', logfile_path=logfile_path)
    assert sternberg_log == os.path.join(logfile_path,'SUBJID/Sternberg-s-SUBJID.log')

# def test_scrub_openneuro():
#     import shutil, hv_proc
    
#     shutil.copytree(os.path.join(hv_proc.__path__[0], 'MEG', 'SUBJID_haririhammer_20200122_04.ds'),
#                     '/tmp/20200122')
    
    

    
# def test_filter_list_by_task():
#     #Needs to be rewritten for biowulf
#     test_subj='SUBJID'
#     tmp = get_subject_datasets(test_subj, meg_path='/data/MEG')
#     tmp = filter_list_by_task(tmp, task='gonogo')
#     assert tmp == ['/data/MEG/.ds']
 
