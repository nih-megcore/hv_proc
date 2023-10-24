#!/bin/bash

for task in airpuff hariri sternberg gonogo oddball artifact;
do 
	for subject in $(hv_process.py -list_subjects); do hv_process.py -${task} -QA_task ${task} -subjid $subject >>  LOGS/${task}_log.txt 2>&1 ; 
	done
done
