#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 11:35:08 2024

@author: jstout
"""

import sys
import pandas as pd
import os, os.path as op
import glob
error_tag = ':: ERROR ::'
info_tag = ':: INFO ::'
warn_tag = ':: WARNING ::'

logdir = sys.argv[1]
tasks = ['airpuff',
         'gonogo',
         'sternberg',
         'hariri',
         'rest',
         'oddball',
         'movie'
         ]

def parse_logfile(logfile):
    with open(logfile,'r') as f:
        lines = f.readlines()
    errors=[]
    infos = []
    out_dict = {i:'missing' for i in tasks}
    out_dict['movie']='unchecked'
    out_dict['rest']='unchecked'
    for i in lines:
        if error_tag in i:
            errors.append(i)
        elif i[:10].lower()=='processing':
            infos.append(i)
    for i in infos:
        tmp = i.split()
        if tmp[0]=='Processing':
            out_dict[tmp[1].lower()] = 'proc_success'
    for i in errors:
        task_error=i.split(error_tag)[-1].split(' ')[1]
        out_dict[task_error.lower()]='proc_error'
    if 'proc_error' in out_dict.values():
        out_dict['Final']='ERROR'
    else:
        out_dict['Final'] ='SUCCESS'
    return out_dict        


logfiles = glob.glob(op.join(logdir, '????????_log.txt'))
dframe = pd.DataFrame(columns=tasks+['Final'])
for logfile in logfiles:
    subjid=op.basename(logfile)[0:8]
    tmp_dict = parse_logfile(logfile)
    dframe.loc[subjid, tasks]=[tmp_dict[i] for i in tasks]
    dframe.loc[subjid, 'Final'] = tmp_dict['Final']

dframe.to_csv(op.join(logdir, 'ProcAssess.csv'))


# =============================================================================
# 
# =============================================================================
def parse_QA_logfile(logfile):
    with open(logfile,'r') as f:
        lines = f.readlines()
    errors=[]
    infos = []
    out_dict = {i:'missing' for i in tasks}
    out_dict['movie']='unchecked'
    out_dict['rest']='unchecked'
    for i in lines:
        if error_tag in i:
            errors.append(i)
        elif warn_tag in i:
            errors.append(i)
        elif info_tag in i:
            infos.append(i)
    for i in infos:
        if len(i.split('::')) > 1:
            task_=i.split('::')[2].split(':')[0].split(' ')[-1].strip().lower()
            if task_ in tasks:
                out_dict[task_]='qa_success'
    for i in errors:
        if len(i.split('::')) > 1:
            task_=i.split('::')[2].split(':')[0].split(' ')[-1].strip().lower() #.strip().lower()
            if task_ in tasks:
                out_dict[task_]='qa_error'        
    if 'proc_error' in out_dict.values():
        out_dict['Final']='ERROR'
    else:
        out_dict['Final'] ='SUCCESS'
    return out_dict    
    
logfiles = glob.glob(op.join(logdir, '????????_QA_log.txt'))
dframe = pd.DataFrame(columns=tasks+['Final'])
for logfile in logfiles:
    subjid=op.basename(logfile)[0:8]
    tmp_dict = parse_QA_logfile(logfile)
    dframe.loc[subjid, tasks]=[tmp_dict[i] for i in tasks]
    dframe.loc[subjid, 'Final'] = tmp_dict['Final']

dframe.to_csv(op.join(logdir, 'ProcAssessQA.csv'))
    
    



def to_failure_matrix_proc(  ):
    ''';lja;lkj;lj'''
    
    
    
def to_failure_matrix_check(  ):
    ''' lj;lj  '''