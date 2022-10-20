#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 22:17:34 2020

@author: stoutjd
"""


import mne
import numpy as np
import os, sys
# filename = sys.argv[1]


import matplotlib
matplotlib.use('agg')

outdir = os.environ['hv_QA_path']
if not os.path.exists(outdir): os.mkdir(outdir)



def get_output_prefix(filename):
    subjid = os.path.basename(filename).split('_')[0]
    global outdir
    subj_outdir = os.path.join(outdir, subjid)
    if not os.path.exists(subj_outdir): os.mkdir(subj_outdir)
    return os.path.join(subj_outdir, subjid)

#Preprocessing
def preproc(filename, lfreq=None, hfreq=None, pre_stim=-0.2, post_stim=0.4, 
            stim_keeps=[]):
    raw = mne.io.read_raw_ctf(filename, preload=True, verbose=False, 
                              system_clock='ignore')
    raw = raw.filter(lfreq, hfreq, verbose=False)
    
    events, event_dict = mne.events_from_annotations(raw, verbose=False)
    if stim_keeps != []:
        event_dict = {key:value for (key,value) in event_dict.items() if key in stim_keeps }   
    epochs = mne.Epochs(raw, events, tmin=pre_stim, tmax=post_stim, 
                        event_id=event_dict, preload=True, verbose=False) #, event_repeated=True)
    return epochs, event_dict


def save_ave_plot(epochs, condition_name=None, task_name=None, 
                     outprefix=None, topo_range=None):
    '''topo_range must be a numpy range  np.arange(start, stop, step)'''
    evoked = epochs[condition_name].average()
    evoked_plot = evoked.plot()
    evoked_plot.savefig('{}_{}_{}_butterfly.png'.format(outprefix, task_name, condition_name))
    matplotlib.pyplot.close(evoked_plot)
    
    evoked_topo=evoked.plot_topomap(topo_range)
    evoked_topo.savefig('{}_{}_{}_topo.png'.format(outprefix, task_name, condition_name))
    matplotlib.pyplot.close(evoked_topo)

#################   All of the Task based plotting routines ##################
def plot_airpuff(filename):
    stim_names = ['stim', 'missingstim']
    epochs, event_dict = preproc(filename, lfreq=0.5, hfreq=100, pre_stim=-0.1, 
                                 post_stim=0.3, stim_keeps=stim_names)
    outprefix = get_output_prefix(filename)
    epochs.save(outprefix+'_airpuff-epo.fif', overwrite=True)
    for stim_name in stim_names:
            save_ave_plot(epochs, condition_name=stim_name, task_name='airpuff', 
                          outprefix=outprefix, topo_range=np.arange(0, 0.07, 0.01))    
    
def plot_gonogo(filename):
    stim_names = ['go','nogo']
    epochs, event_dict = preproc(filename, lfreq=1, hfreq=40, pre_stim=-0.5, 
                                 post_stim=1, stim_keeps=stim_names)
    outprefix = get_output_prefix(filename)
    epochs.save(outprefix+'_gonogo-epo.fif', overwrite=True)
    for stim_name in stim_names:
            save_ave_plot(epochs, condition_name=stim_name, task_name='gonogo', 
                          outprefix=outprefix, topo_range=np.arange(0, 0.7, 0.1))      
    
def plot_hariri(filename):
    stim_names=['encode_happy', 'encode_sad', 'encode_shape']
    epochs, event_dict = preproc(filename, lfreq=1, hfreq=40, pre_stim=-0.5, 
                                 post_stim=1, stim_keeps=stim_names)
    outprefix=get_output_prefix(filename)  #Add the output directory to name
    epochs.save(outprefix+'_hariri-epo.fif', overwrite=True)
    for stim_name in stim_names:
            save_ave_plot(epochs, condition_name=stim_name, task_name='hariri', 
                          outprefix=outprefix, topo_range=np.arange(0, 0.7, 0.1))
            
def plot_oddball(filename):
    stim_names = ['standard', 'target', 'distractor']
    epochs, event_dict = preproc(filename, lfreq=1, hfreq=100, pre_stim=-0.2, 
                                 post_stim=.6, stim_keeps=stim_names)
    outprefix=get_output_prefix(filename)  
    epochs.save(outprefix+'_oddball-epo.fif', overwrite=True)
    for stim_name in stim_names:
            save_ave_plot(epochs, condition_name=stim_name, task_name='oddball', 
                          outprefix=outprefix, topo_range=np.arange(0, .15, 0.01))

def plot_sternberg(filename):
    stim_names = ['encode4', 'encode6']
    epochs, event_dict = preproc(filename, lfreq=0.5, hfreq=50, pre_stim=-0.5, 
                                 post_stim=2.0, stim_keeps=stim_names)
    outprefix=get_output_prefix(filename)  
    epochs.save(outprefix+'_sternberg-epo.fif', overwrite=True)
    for stim_name in stim_names:
            save_ave_plot(epochs, condition_name=stim_name, task_name='sternberg', 
                          outprefix=outprefix, topo_range=np.arange(0, 2, 0.3))    
    




# compare_plot = mne.viz.plot_compare_evokeds([evoked_stim, evoked_missed], 
#                                             picks='meg', combine='median')


