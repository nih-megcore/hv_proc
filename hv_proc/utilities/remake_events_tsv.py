#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 11 14:24:26 2022

The oddball task had the triggers reassessed to create a new MarkerFile.mrk.
The bids data has already been created - so the events.tsv needs to be 
written again.  It was preferralbe not to make the bids tree again.


@author: jstout
"""

import mne
import numpy as np
from mne_bids.write import _events_tsv
# import os
import sys
import logging

logger = logging.Logger('events')

fname = sys.argv[1]

logger.info(f'Running: {fname}')
raw = mne.io.read_raw_ctf(fname, preload=True, system_clock='ignore')
events, trial_type = mne.events_from_annotations(raw)

events_tsv_fname = fname.replace('_meg.ds','_events.tsv')

try:
    _events_tsv(events,                         #Events
                np.zeros(len(events)),          #Durations
                raw,                            #MNE data
                events_tsv_fname,               #events_fname
                trial_type,                     #trial_type
                overwrite=True)
except BaseException as e:
    logger.exception(e)
    