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
        self.__ch_zscore = None
        self.chs = self.raw.ch_names
    
    @property 
    def gfp(self):
        if self.__gfp is None:
            self.__gfp= np.mean(self.raw._data**2,axis=1)
        return self.__gfp
    
    @property
    def chan_zscore(self):
        if self.__ch_zscore is None:
            self.__ch_zscore = zscore(self.gfp)
        return self.__ch_zscore
    
        







tmp=score_noise('20190102/MEG_EmptyRoom_20190102_01.ds')
    
    
    
    