#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 08:59:50 2020

@author: stoutjd
"""
import os, glob
import logging


#Set the paths to the meg and logfile data
try:
    default_meg_path = os.path.join(os.environ['hv_meg_path'])
    default_outlog_path = os.path.join(os.path.dirname(default_meg_path), 'out_logs')
    if not os.path.exists(default_outlog_path):
        os.mkdir(default_outlog_path)
    default_logfile_path = os.path.join(os.environ['hv_logfile_path'])
except:
    if 'hv_meg_path' not in os.environ:
        raise ValueError('''Make sure to set hv_meg_path.
                         In bash: export hv_meg_path=/$PATH/TOMEG''')
    if 'hv_logfile_path' not in os.environ:
        raise ValueError('''Make sure to set hv_logfile_path.
                         In bash: export hv_logfile_path=/$PATH/TO_Logs''')
    else:
        raise ValueError('''Unknown error setting default paths''')

def get_subj_logger(subjid, session, log_dir=None):
     '''Return the subject specific logger.
     This is particularly useful in the multiprocessing where logging is not
     necessarily in order'''
     fmt = '%(asctime)s :: %(levelname)s :: %(message)s'
     sub_ses = f'{subjid}'
     subj_logger = logging.getLogger(sub_ses)
     subj_logger.setLevel(logging.INFO)
     if subj_logger.handlers != []: # if not first time requested, use the file handler already defined
         tmp_ = [type(i) for i in subj_logger.handlers ]
         if logging.FileHandler in tmp_:
             return subj_logger
     else: # first time requested, add the file handler
         fileHandle = logging.FileHandler(f'{log_dir}/{subjid}_log.txt')
         fileHandle.setLevel(logging.INFO)
         fileHandle.setFormatter(logging.Formatter(fmt)) 
         subj_logger.addHandler(fileHandle)
         subj_logger.info('Initializing subject level HV log')
     return subj_logger   

def log(function):
    def wrapper(*args, **kwargs):  
        logger.info(f"{function.__name__} :: START")
        try:
            output = function(*args, **kwargs)
        except BaseException as e:
            logger.exception(f"{function.__name__} :: " + str(e))
            raise
        logger.info(f"{function.__name__} :: COMPLETED")
        return output
    return wrapper


def get_subject_datasets(subjid, meg_path=None):
    '''If meg_path not supplied - it defaults to the NIMH biowulf path'''
    if meg_path==None:
        meg_path = default_meg_path
    return glob.glob(os.path.join(meg_path,'????????', subjid+'*.ds'))

def filter_list_by_task(filename_list, task=None):
    '''Return a subset of files with the task name'''
    outputs=[]
    if task=='hariri': task='haririhammer'
    for filename in filename_list:
        if task in filename.split('_'):
            outputs.append(filename)
    if len(outputs) > 1:
        print('>> More than one input dataset <<\n{}\n'.format(outputs))  #Change this to a log warning <<<<<<<<<<<<<<
    return outputs

def get_logfile(subjid, task=None, logfile_path=None):
    '''Returns the logfile as a path string
    Errors if zero or multiple logfiles are found'''
    task_dict={'hariri':'HH*{}*.log'.format(subjid),
               'sternberg':'Sternberg*{}*.log'.format(subjid),
               'gonogo': 'GoNoGo*{}*.log'.format(subjid)
               }
    if logfile_path==None:
        logfile_path=default_logfile_path
    logfile=glob.glob(os.path.join(logfile_path, subjid, task_dict[task]))
    print(logfile)
    if logfile == []:
        raise IOError('No logfile for {} : Should be of form {}'.format(
            subjid, task_dict[task]))
    if len(logfile) > 1:
        raise IOError('Found multiple lofiles {}'.format(logfile))
    else:
        return logfile[0]


def main(args):
    subjid = args.subjid
    logger = get_subj_logger(args.subjid, session=None, log_dir=default_outlog_path)
    logger.info(f'Initializing structure :: {args.subjid}')
    
    #Search all datasets in the default meg path for the subject ID
    subj_datasets=get_subject_datasets(subjid) 
    if subj_datasets == []:
        raise ValueError('''\nThere are no datasets for this subject {} \nin folder {}
                         \nVerify that you have the correct subject'''.format(subjid, default_meg_path))

    has_airpuff = len(filter_list_by_task(subj_datasets, 'airpuff')) > 0
    has_hariri = len(filter_list_by_task(subj_datasets, 'hariri')) > 0
    has_sternberg = len(filter_list_by_task(subj_datasets, 'sternberg')) > 0
    has_oddball = len(filter_list_by_task(subj_datasets, 'oddball')) > 0
    has_gonogo = len(filter_list_by_task(subj_datasets, 'gonogo')) > 0
    has_artifact = len(filter_list_by_task(subj_datasets, 'artifact')) > 0

    ######################## Process Task Data ###############################
    if args.airpuff and has_airpuff:
        from hv_proc.Process_scripts import process_airpuff
        filename = filter_list_by_task(subj_datasets, 'airpuff')
        logger.info('\nProcessing airpuff file: {}'.format(filename[0]))
        try:
            process_airpuff.main(filename[0], write_mrk_file=True) #Does not expect logfile
        except BaseException as e:
            logger.exception(f'Airpuff Exception: {e}')
    if args.hariri and has_hariri:
        from hv_proc.Process_scripts import process_hariri
        filename = filter_list_by_task(subj_datasets, 'hariri')
        logger.info('\nProcessing hariri file: {}'.format(filename[0]))
        logfile = get_logfile(subjid, 'hariri')
        try:
            process_hariri.main(filename[0], logfile, write_mrk_file=True)
        except BaseException as e:
            logger.exception(f'Hariri Exception: {e}')
    if args.sternberg and has_sternberg:
        from hv_proc.Process_scripts import process_sternberg
        filename = filter_list_by_task(subj_datasets, 'sternberg')
        logger.info('\nProcessing sternberg file: {}'.format(filename[0]))
        logfile = get_logfile(subjid, 'sternberg')
        try:
            process_sternberg.main(filename[0], logfile, write_mrk_file=True)
        except BaseException as e:
            logger.exception(f'Sternberg Exception: {e}')
    if args.gonogo and has_gonogo:
        from hv_proc.Process_scripts import process_gonogo
        filename = filter_list_by_task(subj_datasets, 'gonogo')
        logger.info('\nProcessing gonogo file: {}'.format(filename[0]))
        logfile = get_logfile(subjid, 'gonogo')
        try:
            process_gonogo.main(filename[0], logfile, write_mrk_file=True)
        except BaseException as e:
            logger.exception(f'Gonogo Exception: {e}')
    if args.oddball and has_oddball:
        from hv_proc.Process_scripts import process_oddball
        filename = filter_list_by_task(subj_datasets, 'oddball')
        logger.info('\nProcessing oddball file: {}'.format(filename[0]))
        try:
            process_oddball.main(filename[0], remove_process_folder=True)
        except BaseException as e:
            logger.exception(f'Oddball Exception: {e}')
    if args.artifact and has_artifact:
        from hv_proc.Process_scripts import process_artifact_scan
        filename = filter_list_by_task(subj_datasets, 'artifact')
        logger.info('\nProcessing artifact file: {}'.format(filename[0]))
        try:
            process_artifact_scan.main(filename[0], write_mrk_file=True)
        except BaseException as e:
            logger.exception(f'Artifact Exception: {e}')
        
    #################### List the output counts for the task #################
    from hv_proc.utilities.response_summary import (print_airpuff_stats, 
                                                    print_gonogo_stats, 
                                                    print_hariri_stats,
                                                    print_oddball_stats,
                                                    print_sternberg_stats)
    for datatype in args.print_stim_counts:
        filename_list = filter_list_by_task(subj_datasets, datatype)
        for filename in filename_list:
            print(filename)
            tmp_fileparts = os.path.basename(filename).split('_')
            if 'airpuff' in tmp_fileparts:
                print_airpuff_stats(filename)
            if 'gonogo' in tmp_fileparts:
                print_gonogo_stats(filename)
            if 'sternberg' in tmp_fileparts:
                print_sternberg_stats(filename)
            if ('hariri' in tmp_fileparts) or ('haririhammer' in tmp_fileparts):
                print_hariri_stats(filename)
            if 'oddball' in tmp_fileparts:
                print_oddball_stats(filename)
        
    #################### Perform Quality Assurance Tests #####################
    from hv_proc.utilities.marker_quality_assurance import (qa_oddball, 
                                                            qa_airpuff,
                                                            qa_hariri, 
                                                            qa_sternberg,
                                                            qa_gonogo, 
                                                            )
    from hv_proc.utilities.print_QA_images import (plot_airpuff,
                                                    plot_oddball,
                                                    plot_hariri,
                                                    plot_sternberg, 
                                                    plot_gonogo)
    

    
    if ('airpuff' in args.QA_task) and has_airpuff:
        airpuff_filename = filter_list_by_task(subj_datasets, 'airpuff')[0]
        print('Testing airpuff: {}'.format(airpuff_filename))
        qa_airpuff(airpuff_filename, args.subjid)
        #plot_airpuff(airpuff_filename)
        
    if ('hariri' in args.QA_task) and has_hariri:
        hariri_filename = filter_list_by_task(subj_datasets, 'hariri')[0]
        logger.info('Testing hariri: {}'.format(hariri_filename))
        qa_hariri(hariri_filename, args.subjid)
        #plot_hariri(hariri_filename)

    if ('sternberg' in args.QA_task) and has_sternberg:
        sternberg_filename = filter_list_by_task(subj_datasets, 'sternberg')[0]
        print('Testing sternberg: {}'.format(sternberg_filename))
        qa_sternberg(sternberg_filename, args.subjid)
        #plot_sternberg(sternberg_filename)

    if ('gonogo' in args.QA_task) and has_gonogo:
        gonogo_filename = filter_list_by_task(subj_datasets, 'gonogo')[0]
        logger.info('Testing gonogo: {}'.format(gonogo_filename))
        qa_gonogo(gonogo_filename, args.subjid)
        #plot_gonogo(gonogo_filename)
 
    if ('oddball' in args.QA_task) and has_oddball:
        oddball_filename = filter_list_by_task(subj_datasets, 'oddball')[0]
        print('Testing oddball: {}'.format(oddball_filename))
        qa_oddball(oddball_filename, args.subjid)
        #plot_oddball(oddball_filename)
        
    if args.scrub_openneuro:
        #from hv_proc.utilities import clear
        remove_files=[]
        for filename in subj_datasets:
            remove_files.extend(glob.glob(os.path.join(filename, '*.bak')))
            remove_files.extend(glob.glob(os.path.join(filename, '*.hist')))
        print('Removing the following files: {}'.format('\n'.join(remove_files)))
        remove_bool = input('Do you want to remove these files? (y/n)')
        if remove_bool.lower()=='y':
            for rem_file in remove_files:
                os.remove(rem_file)
        
        #Scrub the path information from the header of the mark file
        from hv_proc.utilities.clear_mrk_path import (calc_extra_mark_filelist,
                                                      remove_extra_mrk_files, 
                                                      clean_filepath_header)
        for filename in subj_datasets:
            mrk_file = os.path.join(filename, 'MarkerFile.mrk')
            if not os.path.exists(mrk_file):
                continue
            clean_filepath_header(mrk_file)
            # Remove extra mark files that may be present
            extra_mrk_files=calc_extra_mark_filelist(filename)
            remove_extra_mrk_files(extra_mrk_files)

        

    
if __name__=='__main__':    
    import argparse
    #from argparse import RawTextHelpFormatter
    #from argparse import ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(
        description='''Main function for processing NIMH healthy volunteer MEG data
        for upload to OpenNeuro.  Datasets include: airpuff, rest, gonogo,
        sternberg, hariri, oddball, and movie.  Information on the protocol can 
        be found in: 
        https://openneuro.org/datasets/ds004215/versions/1.0.1 
        
        Nugent, A.C., Thomas, A.G., Mahoney, M. et al. The NIMH intramural healthy 
        volunteer dataset: A comprehensive MEG, MRI, and behavioral resource. 
        Sci Data 9, 518 (2022). https://doi.org/10.1038/s41597-022-01623-9 .
        hv_process loads options and calls trigger procesing functions located
        in hv_proc/Processing_Scripts.  
        Quality assurance scripts are located in hv_proc/utilities 
        
        Raw data initially starts in hv_nimh/MEG
        Data is copied to hv_nimh/bids_staging
        
        Tasks: Sternberg, Hariri, and gonogo (go/no-go) require psychoPy 
        logfiles
        These are expected to be in nimh_hv/MEG/logfiles folder on biowulf
        
        Additional tip::
        task=airpuff;
for subj in $(hv_process.py -list_subjects); do hv_process.py -${task} -QA_task ${task} -subjid $subj  2>&1 | tee -a output_${task}.log ; done 
        
        ''') 

    parser.add_argument('-subjid', help='subject 8-digit data acqusition hash ID')
    parser.add_argument('-list_subjects', help='''Print out all of the subjects in 
                        the MEG folder''', action='store_true')

    ### Trigger Processing functions
    parser.add_argument('-airpuff', action='store_true',
                        help='Process triggers for airpuff dataset')
    parser.add_argument('-hariri', action='store_true', 
                        help='Process triggers for Hariri hammer dataset')
    parser.add_argument('-sternberg', action='store_true', 
                        help='Process triggers for Sternberg task')
    parser.add_argument('-gonogo', action='store_true', 
                        help='Process triggers for gonogo task')
    parser.add_argument('-oddball', action='store_true',
                        help='Process triggers for auditory oddball task')
    parser.add_argument('-artifact', action='store_true',
                        help='Process triggers for artifact scan')    
    parser.add_argument('-extract_all_triggers', action='store_true', 
                        help='''Loop over all datasets and process the triggers 
                        for the subject''')
    
    ## QA the data
    parser.add_argument('-QA_all', action='store_true',
                        help='''Run QA tests on all of the datasets to ensure the
                        trigger count is appropriate''') 
    parser.add_argument('-QA_task', metavar='task',
                        nargs='+', 
                        choices=['airpuff','oddball','hariri','sternberg','gonogo'],
                        help='''Provide a task to QA.
                        Must be one or more of the following: 
                            airpuff oddball hariri sternberg gonogo
                        Tasks are separated by a space''')
    parser.add_argument('-print_stim_counts', metavar='task',
                        nargs='+',
                        choices=['airpuff','oddball','hariri','sternberg','gonogo','all'],
                        help='''Print out the current value counts from the Markerfile.mrk.
                        Can specify a datatype or 'all' to loop over all datasets''')
    
    ### Cleanup from processing data
    parser.add_argument('-scrub_openneuro', action='store_true', 
                        help='''Scrub the path from the markerfile.mrk and
                        remove extra files [.bak and .hist]''')
                        
    args = parser.parse_args()
    if (not args.subjid) and (not args.list_subjects):
        raise ValueError('No subject ID provided')
        
    if args.extract_all_triggers:
        for i in ['airpuff', 'hariri', 'sternberg', 'gonogo', 'oddball',
                  'artifact']:
            tmp='args.{}=True'.format(i)
            exec(tmp)
    if args.QA_all:
        args.QA_task=['airpuff', 'hariri', 'sternberg', 'gonogo', 'oddball',
                      'artifact']
        
    if args.print_stim_counts:
        args.print_stim_counts = [i.lower() for i in args.print_stim_counts]
        if 'all' in args.print_stim_counts:
            args.print_stim_counts = ['airpuff', 'hariri', 'sternberg', 'gonogo', 'oddball']
    if not args.print_stim_counts:
        args.print_stim_counts = []
    
    #QA_task needs initialization because of list reference during processing
    if not args.QA_task:
        args.QA_task=[]  
    #print(args.__dict__)    
    if args.list_subjects:
        tmp_dsfiles=glob.glob(os.path.join(default_meg_path, '????????', '*.ds'))
        tmp_subjids=set([os.path.basename(i).split('_')[0] for i in tmp_dsfiles])
        tmp_subjids = sorted(tmp_subjids)
        print(' '.join(tmp_subjids))
        exit(0)
        
        
    main(args)



