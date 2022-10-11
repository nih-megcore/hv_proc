import pandas as pd
import glob 

import os

dset1='bids_staging/MEG'
dset2='bids_staging_batch2/MEG'

os.chdir('/gpfs/gsfs4/users/NIMH_MEGCoregroup/NIMH_HV')
all_subjs=glob.glob('bids_staging/MEG/????????/*.ds') 
all_subjs+=glob.glob('bids_staging_batch2/MEG/????????/*.ds')

def return_fname(var):
	return os.path.split(var)[-1]

def return_split_name(var, idx=1):
	return var.split('_')[idx]


dframe=pd.DataFrame(all_subjs, columns=['dset'])

dframe['fname']=dframe.dset.apply(return_fname)

dframe['task']=dframe.fname.apply(return_split_name, idx=1) 
dframe['subjid']=dframe.fname.apply(return_split_name, idx=0)


dframe.task.value_counts() 
dframe.pivot_table(columns='task', index='subjid', aggfunc='count')

