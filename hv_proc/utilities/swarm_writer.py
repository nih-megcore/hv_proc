#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 12:19:18 2020

@author: stoutjd
"""


import argparse
import glob, os
import hv_proc
import itertools

# def assemble_sbatch_command(args, files=None, subjids=None):
#     output=[]
#     if args.flag_vals:
#         flag_vals=args.flag_vals
#     else:
#         flag_vals=''
        
#     if files != None:
#         for filename in files:
#             tmp = '{} {} {} \n'.format(args.command, flag_vals, filename)
#             output.append(tmp)
#     return output

def assemble_inverse_swarm(subject_list=None, task_list=None):
    '''Build a swarm command for the inverse solution and write it to ./tmp_swarm.file'''
    output=[]
    hv_proc_path=hv_proc.__path__[0]
    inverse_path = os.path.join(hv_proc_path, 'process_images/inverse_process.py')
    
    module_load_cmd = 'module load afni; module load ctf; '
    for task,subject in itertools.product(task_list, subject_list):
        inv_cmd = '{} -task {} -subject_list {}'.format(inverse_path, 
                                                        task, subject)
        cmd = module_load_cmd + inv_cmd + '\n'
        output.append(cmd)

    with open('./tmp_swarm.file', 'w') as outfile:
        outfile.write('#!/bin/bash \n')
        outfile.writelines(output)    
    

            
# def main(args):
#     # print(args.flags)
#     glob_cmd = args.file_parser
    
#     response = 'n'
#     while glob_cmd.lower() != 'y':
#         files = glob.glob(glob_cmd)
#         print(files)
#         glob_cmd = input('''Are these the correct files.  
#                          \nIf not put in a new glob filtering - eg. /data/MEG/????????/*oddball*.ds\n''')
#     output = assemble_sbatch_command(args, files)
#     for out in output:
#         print(out)
    
#     with open('./tmp_swarm.file', 'w') as outfile:
#         outfile.write('#!/bin/bash \n')
#         outfile.writelines(output)
        
            
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('-inverse', action='store_true',
                        help='Create a swarm file for the inverse solution')
    parser.add_argument('-subject_list', nargs='+', 
                        help='''List of subject IDs''')
    parser.add_argument('-task_list', nargs='+',
                        help='''List of tasks to process''')
    
                    
    args = parser.parse_args()
    if args.inverse:
        assemble_inverse_swarm(subject_list=args.subject_list, 
                               task_list=args.task_list)
        print('Use the following to submit the job')
        print('swarm -f ./tmp_swarm.file -g 4 -t 2 --time 12:00:00')
    
    
    


# if __name__=='__main__':
#     parser=argparse.ArgumentParser()
#     parser.add_argument('-command', help='The command path to be executed')
#     parser.add_argument('-flag_vals', help='''Put all flag options inside quotes.
#                         -flag_vals "-highpass 3.0 -lowpass 40.0 ....".  These will
#                         be passed on to swarm file ''')
#     parser.add_argument('-file_parser', help='''This will use the glob command
#                         to locate all files with these wildcards''')
                    
#     args = parser.parse_args()
#     main(args)