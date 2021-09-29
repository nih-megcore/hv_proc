import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hv_proc", 
    version="0.1.0",
    author="Jeff Stout",
    author_email="stoutjd@nih.gov",
    description="Package to process triggers for NIMH healthy volunteer MEG protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nih-megcore/hv_proc",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: UNLICENSE",
        "Operating System :: Linux/Unix",
    ],
    #python_requires='<3.9',
    install_requires=['mne', 'numpy', 'scipy', 'pandas','pytest', 'seaborn'],
    scripts=['hv_proc/hv_process.py'] 
)
