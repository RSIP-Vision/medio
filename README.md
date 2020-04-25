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
- pydicom
- dicom-numpy

A conda environment .yml file is in the project's root.

# Usage
There are 3 main functions in medio: `read_img`, `save_img` and `save_dir`.
```python
from medio import read_img, save_img
# read a dicom series from a folder
img_arr, metadata = read_img('data/dicom-folder/', desired_ornt='IAR')
# do your stuff and save in any format
save_img('ct.nii.gz', img_arr, metadata, backend='nib')
```

# Documentation
## Reading and Saving Images

The 3 main functions for reading and saving are:

### read_img
`medio.read_img(input_path, desired_ornt=None, backend=None, dtype=None, **kwargs)`
- `input_path` is a path-like object (str or pathlib.Path) for the data to be read. It can be a file or a folder (in 
the case of a dicom series). It is the only required parameter.
  If the input path is s folder, it should contain a single dicom series.
- Returns: (array, metadata) of types numpy.ndarray and medio.MetaData. The first is a numpy array of the 
image, and the second is a metadata object of the image (see [MetaData](README.md#metadata) class documentation).

Optional parameters:
- `desired_ornt=None`: str of the desired orientation of the image e.g. 'RAI'. If None, no reorientation is performed.
  The desired orientation is in itk standard, even when the IO engine ("backend") is nibabel which uses a different 
  standard (see [Orientation](README.md#orientation)).
- `backend=None`: str for the backend IO engine to be used: 'nib' (nibabel), 'itk' or 'pydicom' (also 'pdcm'). If None, 
the backend is chosen automatically: 'nib' for nifti files ('.nii' or '.nii.gz' suffix), otherwise 'itk'.
- `dtype=None`: if not None, equivalent to `array.astype(dtype)` on the returned image array.

`**kwargs` are additional per-backend optional parameters:
- 'itk' backend:
  - `pixel_type=itk.SS`: itk pixel type of the image file/folder. The default value is int16 (`itk.SS` - Signed Short). 
Other common pixel types are: `itk.UC` - uint8, `itk.US` - uint16. 
  - `fallback_only=False`: relevant to files only. If True, the pixel type is automatically found. If failed then 
`pixel_type` is used. A similar effect can be achieved with `pixel_type=None`. 
  - `dimension=3`: relevant to folders only. The dimension of the image to be read.

- 'nib' backend:
  - `unravel=False`: relevant for structured data types, for example RGB image. If True and the image is of such dtype, 
then the channels are stacked along the last axis of the image array.

- 'pydicom' backend
  - `globber='*'`:

### save_img
`save_img(filename, np_image, metadata, use_original_ornt=True, backend=None, dtype=None, mkdir=False, parents=False,
             **kwargs)`
- `filename`: a path-like object of the file to be saved.
- `np_image`: the image array.
- `metadata`: the corresponding metadata.

Optional parameters:
- `use_original_ornt=True`: 
- `backend=None`: str of the backend to use: 'nib' or 'itk'. If None, 'nib' is chosen for nifti files and otherwise 
'itk'.
- `dtype=None`: if not None, equivalent to passing `np_image.astype(dtype)`. Note that not every dtype is supported, so
make sure what the dtype of the image array you want to save.
- `mkdir=False`: if True, creates the directory of `filename`.
- `parents=False`: to be used with `mkdir=True`. If True, creates also the parent directories. 

'itk' backend optional parameters (`**kwargs`):
- `is_vector=False`
- `allow_dcm_reorient=False`: when saving a dicom file ('.dcm' or '.dicom' suffix) the image orientation should be 
right-handed. If it is left-handed, the image can be reoriented to a right-handed orientation with 
`allow_dcm_reorient=True`, which flips the last axis orientation.
- `compression=False`: whether to use compression in itk writer. Note that you do not have to set

### save_dir
Save dicom series image in a directory (itk backend).

## Metadata Objects
### Affine
The affine of an image is a transformation between 
The Affine class is a subclass of numpy.ndarray with some special properties: spacing, origin and direction which can 
be accessed and set.

This class includes also some static methods for affine construction from its components (spacing, origin and direction)
and also the inverse methods for getting the spacing, origin and direction matrix from a general affine matrix.

For a mathematical explanation about affine see 
[NiBabel's affine documentation](https://nipy.org/nibabel/coordinate_systems.html#the-affine-matrix-as-a-transformation-between-spaces).

### MetaData
Together with the image's numpy array, the MetaData object is a necessary component for the I/O functions.

A MetaData object 'metadata' is comprised mainly of the affine - `metadata.affine` (of class Affine), coordinate system 
`metadata.coord_sys` ('itk' or 'nib') and the original orientation of the image `metadata.orig_ornt` (used for saving).

Other properties of the metadata are derived from the affine: spacing `metadata.spacing` (a reference to 
`metadata.affine.spacing`) and current image orientation `metadata.ornt`. These properties can be viewed easily in the 
console:
```python
>>> import medio
>>> array, metadata = medio.read_img('avg152T1_LR_nifti.nii.gz')
>>> print(metadata)
Affine:
[[  -2.    0.    0.   90.]
 [   0.    2.    0. -126.]
 [   0.    0.    2.  -72.]
 [   0.    0.    0.    1.]]
Spacing: [2. 2. 2.]
Coordinate system: nib
Orientation: LAS
Original orientation: LAS
```
A MetaData object has also the method `metadata.is_right_handed_ornt` which checks for a right handed orientation,
according to the determinant of the direction matrix of the affine (`metadata.affine.direction`). This method can be 
useful before saving a dicom file or series, which should have a right-handed orientation.

#### Orientation
The orientation of the image is derived from its affine and coordinate system (the convention). It denotes along which 
physical axis we move when we increase a single index out of `i, j, k` in the expression `np_image[i, j, k]`.

'RAS' in itk:
- Right to left, Anterior to posterior, Superior to inferior

'RAS' in nib - also 'RAS+':
- left to Right, posterior to Anterior, inferior to Superior

Note that the conventions are opposite. Therefore, for stability reasons we use only itk convention in `read_img`'s 
argument `desired_ornt`.

For further discussion see 
[NiBabel's image orientation documentation](https://nipy.org/nibabel/image_orientation.html#image-voxel-orientation).

## Array and Metadata Operations
Some of the operations on an image affects also its metadata, for example resizing, rotating and cropping. 

