#!/usr/bin/env python
import mne
import pandas as pd
import hv_proc
from hv_proc.Process_scripts.trigger_utilities import parse_marks
import sys
from hv_proc.Process_scripts.trigger_utilities import append_conditions
from hv_proc.utilities import mrk_template_writer
#
raw_fname = sys.argv[1]
raw = mne.io.read_raw_ctf(raw_fname, preload=False, system_clock='ignore')

dframe = pd.DataFrame(raw.annotations)
dframe.rename(columns=dict(description='condition'), inplace=True)

shape_hit=parse_marks(dframe, lead_condition='probe_shape', lag_condition='response_hit', window=(0,1), marker_on='lead', marker_name='shape_hit').dropna(subset=['onset','channel'])
happy_hit=parse_marks(dframe, lead_condition='probe_match_happy', lag_condition='response_hit', window=(0,1), marker_on='lead', marker_name='happy_hit').dropna(subset=['onset','channel'])
sad_hit=parse_marks(dframe, lead_condition='probe_match_sad', lag_condition='response_hit', window=(0,1), marker_on='lead', marker_name='sad_hit').dropna(subset=['onset','channel'])

dframe = append_conditions([shape_hit, happy_hit, sad_hit,dframe])
dframe.duration = 0.0

#dframe.rename(columns=dict(condition='description'), inplace=True)
try:
	mrk_template_writer.main(dframe=dframe,
		ds_filename=raw_fname)
	print(f'Successful processing of {raw_fname}')
except:
	raise Error('Failed')
	
	

