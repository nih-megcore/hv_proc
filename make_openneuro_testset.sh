

#mamba create -p /fast/PYTHON_envs/datalad conda-forge::datalad -y 
conda activate datalad

topdir=$(pwd)
OpenNeuroDset=ds004215
#datalad install https://github.com/OpenNeuroDatasets/${OpenNeuroDset}.git
cd ${OpenNeuroDset}
datalad get sub-ON02747/ses-01/meg/*
datalad get sub-ON02747/ses-01/anat/*

#Resampled the data into a new folder
cd sub-ON02747/ses-01/meg/
mkdir downsampled
for dset in *.ds; do newDs -resample 6 ${dset} downsampled/${dset}; done
cp *.tsv *.json downsampled

#Make new openneuro dataset
new_bids=${topdir}/downsampled_openneuro
deriv_dir=${new_bids}/derivatives/ctf_downsample
mkdir -p ${deriv_dir}
cp ${topdir}/${OpenNeuroDset}/{participants.json,LICENSE,dataset_description.json} ${new_bids}

out_participantTsv=${new_bids}/participants.tsv 
head -1 ${topdir}/${OpenNeuroDset}/participants.tsv > "${out_participantTsv}"
cat ${topdir}/${OpenNeuroDset}/participants.tsv | grep sub-ON02747 >> ${out_participantTsv}

readme_fname=${new_bids}/README
echo "This is test data for the following project">>${readme_fname}
echo "doi:10.18112/openneuro.ds004215.v1.0.1">>${readme_fname}
echo "Downsampled datasets are in the derivatives/ctf_downsample/ folder" >> ${readme_fname}

new_megdir=${deriv_dir}/sub-ON02747/ses-01/meg/
new_mridir=${deriv_dir}/sub-ON02747/ses-01/anat
mkdir -p ${new_megdir}
mv downsampled/* ${new_megdir}
rm -r downsampled

#Open neuro won't accept just derivatives
cd $topdir
cp -L -r ${OpenNeuroDset}/sub-ON02747 ${new_bids}
rm -rf ${new_bids}/sub-ON02747/ses-01/{dwi,func,perf}

