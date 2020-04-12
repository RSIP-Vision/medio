# medio

**Medical images I/O python package**

This package unifies the io engines of itk, nibabel, and pydicom packages in a simple and comprehensive interface.
It includes translation between the metadata conventions, reorientations, affine matrix computation.

# Installation
Download the [whl file](https://drive.google.com/file/d/1slbkF2zk3vZmm6lHbXEfDDzP1ZUpIAg4/view?usp=sharing)
and install it with:
```
(<env-name>) C:\Users\<username>\Downloads>pip install medio-0.1.0-py3-none-any.whl
```
This will install the medio python package and its dependencies in your environment.

## Requirements
The dependencies are:
- numpy
- itk (itk-io, itk-filtering)
- nibabel
- pydicom + dicom-numpy

A conda environment yml is in the project's root.

# Usage
There are 3 main functions in medio: `read_img`, `save_img` and `save_dir`.
```python
from medio import read_img, save_img
# read a dicom series from a folder
img_arr, metadata = read_img('data/dicom-folder/', desired_ornt='IAR')
# do your stuff and save in any format
save_img('ct.nii.gz', img_arr, metadata, backend='nib')
```
