#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  9 15:38:44 2022

@author: jstout
"""

import os
import glob
import mne
import numpy as np
from scipy.stats import zscore
import pandas as pd

topdir='/fast/NOISE'
os.chdir(topdir)

acqs = glob.glob('????????')

class score_noise():
    def __init__(self, fname):
        self.fname = fname
        self.raw = mne.io.read_raw_ctf(self.fname, 
                                       system_clock='ignore')
        self.raw.pick_types(meg=True, ref_meg=False)
        self.raw.load_data()
        self.__gfp = None
        self.__gfp_global = None
        self.__ch_zscore = None
        self.chs = self.raw.ch_names
    
    @property 
    def gfp(self):
        if self.__gfp is None:
            self.__gfp= np.mean(self.raw._data**2,axis=1)
        return self.__gfp
    
    @property
    def gfp_global(self):
        if self.__gfp_global is None:
            self.__gfp_global = np.mean(self.gfp)
        return self.__gfp_global
    
    @property
    def chan_zscore(self):
        if self.__ch_zscore is None:
            self.__ch_zscore = zscore(self.gfp)
        return self.__ch_zscore
    
        
tmp=score_noise('20190102/MEG_EmptyRoom_20190102_01.ds')
    
# =============================================================================
#     
# =============================================================================

def get_multiacqs(topdir=None):
    acqs = glob.glob(f'{topdir}/????????')
    sorted(acqs)
    num_dsets = []
    for i in acqs:
        num_dsets.append(len(glob.glob(f'{i}/*.ds')))
    output = dict(zip(acqs, num_dsets))
    sorted(output)
    return output #sort by date

def find_daily_best(megdir=None):
    '''Loop over MEG folder and identify the lowest noise dataset that 
    does not have flat line channels'''
    dsets = glob.glob(f'{megdir}/*.ds')
    if len(dsets) > 1:
        #Loop datasets
        _results={}
        for fname in dsets:
            _tmp = score_noise(fname)
            _results[fname]=_tmp.gfp_global
        min_gfp = np.min(list(_results.values()))
        #There is a possibility, although low that two runs have same gfp
        min_fname = [i for i,j in _results.items() if j==min_gfp][0]
        return min_fname, _results[min_fname]
    else:
        fname=dsets[0]
        _tmp = score_noise(fname)
        return fname, _tmp.gfp_global

    
        
            
        
        
    # elif len(dsets) == 0: 
    #     #Set as none
    # elif len(dsets) == 1:
    #     # Default send out 1 result
    # else:
    #     raise()
    


#Sort out the testing dates by threshold
tmp = get_multiacqs('./')        
non_testing_dates = {i:j for i,j in sorted(tmp.items()) if j<5}

#Collect the best gfp scan from each day
output_gfps = {}
for acq_date in non_testing_dates.keys():
    fname, gfp_out = find_daily_best(acq_date)
    output_gfps[fname]=gfp_out
    

{find_daily_best.keys(),find_daily_best(i) for i in non_testing_dates.keys()}



multi = {i:j for i,j in non_testing.items() if j>1}


for date in glob.glob('./????????'):
    for run in glob.glob(f'{date}/*.ds'):
        [os.basename(run).split('_')[1] for run in f'{date}/*.ds']
    


    

    