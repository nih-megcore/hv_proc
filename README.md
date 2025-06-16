# Scripts for QA and trigger preprocessing of NIMH HV Protocol

## Install 
```
pip  install git+https://github.com/nih-megcore/hv_proc
```
For datasets pre-2025 (git clone ... cd hv_proc ... git checkout v1.0.0 ... pip install .)

## Usage
hv_process.py will interface to call the appropriate TASK script: hv_proc/Process_scripts/Process_TASK.py.
hv_process.py will find appropriate datasets from the list (airpuff, hariri, sternberg, gonogo, oddball)
and process the trigger/response/logfile timing and write the values into the MarkerFile.mrk in the meg dataset.
QA processing will check that the appropriate number of trials have been extracted and that the response
rate is appropriate (75-80% depending on task).  Errors are reported to standard output/error and are typically redirected to a logfile for further QA.  
```
#Required path variables - typically set in .bashrc
export hv_meg_path=${MEGPATH}
export hv_logfile_path=${LOGPATH}

#Installation will place hv_process.py on the commandline path. 
hv_process.py <options>

#Example usage
hv_process.py -subjid ${subjid} -extract_all_triggers -QA_all

optional arguments:
  -h, --help            show this help message and exit
  -subjid SUBJID        subject 8-digit data acqusition hash ID
  -list_subjects        Print out all of the subjects in the MEG folder
  -airpuff              Process triggers for airpuff dataset
  -hariri               Process triggers for Hariri hammer dataset
  -sternberg            Process triggers for Sternberg task
  -gonogo               Process triggers for gonogo task
  -oddball              Process triggers for auditory oddball task
  -extract_all_triggers
                        Loop over all datasets and process the triggers for the
                        subject
  -QA_all               Run QA tests on all of the datasets to ensure the trigger
                        count is appropriate
  -QA_task task [task ...]
                        Provide a task to QA. Must be one or more of the following:
                        airpuff oddball hariri sternberg gonogo Tasks are separated
                        by a space
  -print_stim_counts task [task ...]
                        Print out the current value counts from the Markerfile.mrk.
                        Can specify a datatype or 'all' to loop over all datasets
  -scrub_openneuro      Scrub the path from the markerfile.mrk and remove extra
                        files [.bak and .hist]

```
### To analyze all subjects at once:
```
for subj in $(hv_process.py -list_subjects); do hv_process.py -subjid $subj -extract_all_triggers >> logfile.txt; done
```
### Alternate troubleshooting
Task by task - loop over subjects and QA outputs
```
task=airpuff
for subj in $(hv_process.py -list_subjects); do hv_process.py -${task} -QA_task ${task} -subjid $subj  2>&1 | tee -a output_${task}.log ; done 
```
