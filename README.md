# Materials Science EM Metadata Extractor

A collection of Python scripts that extract metadata from EM data for Materials Science.
All extracted metadata files are in json format.

## Description

All materials science data to be studied within the scope of OpenEM are extracted in some form of hdf5 format.
To read them and extract their metadata, we are using extrernal libraries suited for this task.
These extrernal dependecies are the reason this extractor is written in Python, as Go does not support all of them.
In the rare case that a file cannot be processed by a library, the fallback solution is using numpy, as all hdf5 files can be read as numpy files.
Their capabilities are explored below:

## Code

1. hyperspy_script:
    - Uses python v3.10.12 and hyperspy v1.7.5
    - Working only for .emd files, .prz files are not recongized by this version of hyperspy
    - Output directory: 'hyperspy_script_metadata/'

2. rsciio_script:
    - Uses python v3.11.9 and the latest version of hyperspy (v2.1) which essentially leads to RosettaSciIO library (rosettasciio v0.4)
    - Working for both .emd and .prz files, with the exception of EELSDataCube Single Image, which is still unsupported
    - Output directory: 'rsciio_script_metadata/'

3. manual_script:
    - Uses python v3.11.9, numpy v1.26.4 and h5py v3.9.0
    - Working for all input files, however in some cases the metadata is lacking information
    - Output directory: 'manual_script_metadata/'

4. final_script: (WIP)
    - Uses python v3.11.9, rosettasciio v0.4 and numpy v1.26.4
    - Same as `rsciio_script` but for the unsupported .prz file it uses numpy as seen in `manual_script`
    - Output directory: 'final_script_metadata/'
