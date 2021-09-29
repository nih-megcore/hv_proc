#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 16:53:48 2020

@author: stoutjd
"""

import mne
import autoreject
from autoreject import AutoReject
from hv_proc.utilities.print_QA_images import get_output_prefix
import sys

filename=sys.argv[1]

import os
if 'OMP_NUM_THREADS' in os.environ:
    set_njobs = int(os.environ['OMP_NUM_THREADS'])
if 'SLURM_CPUS_PER_TASK' in os.environ:
    set_njobs = int(os.environ['SLURM_CPUS_PER_TASK'])
else:
    set_njobs = -1

#epo_filename=get_output_prefix(filename)+'_gonogo-epo.fif'

epochs = mne.read_epochs(filename)

#Necessary to get rid of extraneous channels in dataset
picks = [i for i in epochs.ch_names if i[0]=='M'] 

epochs.pick_channels(picks)

ar = AutoReject(n_jobs=set_njobs)
epochs_clean = ar.fit_transform(epochs)
epochs_clean_fname = filename.split('-epo.fif')[0]+'_clean-epo.fif'
epochs_clean.save(epochs_clean_fname, overwrite=True)
ar.save(epochs_clean_fname[:-14]+'_ar.hdf5', overwrite=True)

reject_log = ar.get_reject_log(epochs)
ar_plot=ar.get_reject_log(epochs).plot(show=False)
ar_plot.savefig(fname=epochs_clean_fname[:-14]+'_reject_plot.png', 
                dpi='figure',bbox_inches='tight')
 
