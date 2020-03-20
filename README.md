# medio

**Medical images I/O python package**

This package unifies the io engines of itk, nibabel, and pydicom packages in a simple and comprehensive interface.
It includes translation between the metadata conventions, reorientations, affine matrix computation.

## Requirements
- numpy
- itk
- simple itk
- nibabel
- pydicom + dicom-numpy

The conda environment yml is in the project's root.

# Usage
```python
>>> from medio import read_img, save_img
>>> # read a dicom series from a folder
>>> img_arr, metadata = read_img('data/dicom-folder/', desired_ornt='IAR')
>>> # do your stuff and save in any format
>>> save_img('ct.nii.gz', img_arr, metadata, backend='nib')
```
