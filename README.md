# medio

**Medical images I/O python package**

This package unifies the io engines of itk, nibabel, and pydicom packages in a simple and comprehensive interface.
It includes translation between the metadata conventions, reorientations, affine matrix computation.

# Installation
Download the [whl file](/uploads/df9f3aaf1ee10485c97d8fbd9ff239bb/medio-0.1.1-py3-none-any.whl)
and install it with:
```
(<env-name>) C:\Users\<username>\Downloads>pip install medio-0.1.1-py3-none-any.whl
```
This will install the medio python package and its dependencies in your environment.

## Requirements
The dependencies are:
- numpy
- itk (itk-io, itk-filtering)
- nibabel
- pydicom + dicom-numpy

A conda environment .yml file is in the project's root.

# Short Documentation
## Reading and Saving Images

The 3 main functions for reading and saving are:

#### read_img
`medio.read_img(input_path, desired_ornt=None, backend=None, dtype=None, **kwargs)`
- `input_path` is a pathlike object (for example str or pathlib.Path) for the data to be 
  read. It can be a file path or a directory path (in the case of a dicom series). It is the only required parameter.
- Returns: (array, metadata) of types numpy.ndarray and medio.MetaData. The first is a numpy array of the 
image, and the second is a metadata object of the image (see MetaData class documentation).

Optional parameters:
- `desired_ornt=None`: str of the desired orientation of the image e.g. 'RAI'. If None, no reorientation is performed.
  
  `desired_ornt` is in itk standard, even when the IO engine ("backend") is nibabel which uses a different standard.
   
- `backend=None`: str for the backend IO engine to be used: 'nib' (nibabel), 'itk' or 'pydicom' (also 'pdcm'). If None, 
the backend is chosen automatically: 'nib' for nifti files ('.nii' or '.nii.gz' suffix), otherwise 'itk'.
- `dtype=None`: if not None, equivalent to `array.astype(dtype)` on the returned image array.

`**kwargs` are additional per-backend optional parameters.

For 'itk' backend:
- `pixel_type=itk.SS`: itk pixel type of the image file/folder. The default value is int16 (`itk.SS` - Signed Short). 
Other common pixel types are: `itk.UC` - uint8, `itk.US` - uint16. 
- `fallback_only=False`: relevant to files only. If True, the pixel type is automatically found. If failed then 
`pixel_type` is used. A similar effect can be achieved with `pixel_type=None`. 
- `dimension=3`: relevant to folders only. The dimension of the image to be read.

For 'nib' backend:
- `unravel=False`: relevant for structured data types, for example RGB image. If True and the image is of such dtype, 
then the channels are stacked along the last axis of the image array.

For 'pydicom' backend
- `globber='*'`:

#### save_img
`save_img(filename, np_image, metadata, use_original_ornt=True, backend=None, dtype=None, mkdir=False, parents=False,
             **kwargs)`
- `filename` is a pathlike object of the file to be saved.

Optional parameters:
- `use_original_ornt=True`: 
- `backend=None`: str of the backend to use: 'nib' or 'itk'. If None, 'nib' is chosen for nifti files and otherwise 
'itk'.
- `dtype=None`: if not None, equivalent to passing `np_image.astype(dtype)`. Note that not every dtype is supported, so
make sure what the dtype of the image array you want to save.
- `mkdir=False`: if True, creates the directory of `filename`.
- `parents=False` to be used with `mkdir=True`. If True, creates also the parent directories. 

'itk' backend optional parameters (`**kwargs`):
- `is_vector=False`
- `allow_dcm_reorient=False`: when saving a dicom file ('.dcm' or '.dicom' suffix) the image orientation should be 
right-handed. If it is left-handed, the image can be reoriented to a right-handed orientation with 
`allow_dcm_reorient=True`, which flips the last axis orientation.
- `compression=False`

#### save_dir
Save dicom series image in a directory (itk backend).


# Usage
There are 3 main functions in medio: `read_img`, `save_img` and `save_dir`.
```python
from medio import read_img, save_img
# read a dicom series from a folder
img_arr, metadata = read_img('data/dicom-folder/', desired_ornt='IAR')
# do your stuff and save in any format
save_img('ct.nii.gz', img_arr, metadata, backend='nib')
```
