# medio

**Medical images I/O python package**

This package unifies the io engines of itk, nibabel, and pydicom packages in a simple and comprehensive interface.

It includes conversion between the metadata conventions, reorientations, affine matrix computation for itk and pydicom
and saving dicom series or file.

# Installation
Download the [.whl file](/uploads/338e95916f6c22548d998dda4f1bf5bc/medio-0.1.2-py3-none-any.whl)
and install it with:
```
(<env-name>) C:\Users\<username>\Downloads>pip install medio-0.1.2-py3-none-any.whl
```
This will install the medio python package and its dependencies in your environment.

### Requirements
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
array, metadata = read_img('data/dicom-folder/', desired_ornt='IAR')
# do your stuff and save in any format
save_img('ct.nii.gz', array, metadata, backend='nib')
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
image, and the second is a metadata object of the image (see [MetaData](#metadata) class documentation).

Optional parameters:
- `desired_ornt=None`: str of the desired orientation of the image, e.g. 'RAI'. If None, no reorientation is performed.
  The desired orientation is in itk standard, even when the IO engine ("backend") is nibabel which uses a different 
  standard (see [Orientation](#orientation)). If you use pydicom backend, it should be None.
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
  - `globber='*'`: relevant for a directory - glob pattern for selecting the series files (all files by default)

### save_img
`medio.save_img(filename, np_image, metadata, use_original_ornt=True, backend=None, dtype=None, mkdir=False,
parents=False, **kwargs)`
- `filename`: a path-like object of the file to be saved.
- `np_image`: the image array.
- `metadata`: the corresponding metadata.

Optional parameters:
- `use_original_ornt=True`: whether to save in the original orientation stored in metadata.orig_ornt or not.
- `backend=None`: str of the backend to use: 'nib' or 'itk'. If None, 'nib' is chosen for nifti files and 'itk' 
otherwise.
- `dtype=None`: if not None, equivalent to passing `np_image.astype(dtype)`. Note that not every dtype is supported 
in saving, so make sure what is the dtype of the image array you want to save.
- `mkdir=False`: if True, creates the directory of `filename`.
- `parents=False`: to be used with `mkdir=True`. If True, creates also the parent directories. 

'itk' backend optional parameters (`**kwargs`):
- `is_vector=False`: set to True if the image is channeled (e.g. RGB). In such case, the channels should be in the 
first dimension of `np_image`. 
- `allow_dcm_reorient=False`: when saving a dicom file ('.dcm' or '.dicom' suffix) the image orientation should be 
right-handed. If it is left-handed, the image can be reoriented to a right-handed orientation with setting this 
parameter to True, which flips the last axis direction.
- `compression=False`: whether to use compression in itk writer. Using a '.nii.gz' suffix in `filename` also compresses 
the image.

### save_dir
Save a 3d image as dicom series of 2d slices in a directory (itk backend).

`medio.save_dir(dirname, np_image, metadata, use_original_ornt=True, dtype=None, parents=False,
allow_dcm_reorient=False, **kwargs)`

Save a 3d numpy array image_np as a dicom series of 2d dicom slices in the directory dirname
- `dirname`: the directory to save the files in, str or pathlib.Path. If it exists - must be empty.
- `np_image`: the image array.
- `metadata`: the corresponding metadata.

Optional parameters, see also in [save_img](#save_img):
- `use_original_ornt=True`: whether to save in the original orientation or not.
- `dtype=None`: if not None, equivalent to passing `np_image.astype(dtype)`.
- `parents=False`: if True, creates also the parents of `dirname`.
- `allow_dcm_reorient=False`: whether to allow automatic reorientation to a right-handed orientation or not.

Additional optional parameters (`**kwargs`): 
- `pattern='IM{}.dcm'`: str pattern for the filenames to save, including a placeholder ('`{}`') for the slice number.
- `metadata_dict=None`: dictionary of metadata for adding tags or overriding the default values. For example, 
`metadata_dict={'0008|0060': 'US'}` will override the default 'CT' modality and set it to 'US' (ultrasound).

## Metadata Objects
### Affine
`medio.Affine`

The affine of an image is a transformation between the index space of the array to the physical 3d space. 
The Affine class is a subclass of numpy.ndarray with some special properties (attributes): `spacing`, `origin` and 
`direction` which can be accessed and set. The method `index2coord` maps the indices to the physical space.

This class includes also some static methods for affine construction from its components (spacing, origin and direction)
and also the inverse methods for getting the spacing, origin and direction matrix from a general affine matrix.

For a mathematical explanation about the affine matrix see 
[NiBabel's affine documentation](https://nipy.org/nibabel/coordinate_systems.html#the-affine-matrix-as-a-transformation-between-spaces).

Some usage examples:
```python
>>> import numpy as np
>>> from medio import Affine
>>> affine1 = Affine(np.eye(4))
>>> affine2 = Affine(direction=np.eye(3), spacing=[0.33, 1, 0.33], origin=[-90.3, 10, 1.44])
>>> index = [4, 0, 9]
>>> coord = affine2.index2coord(index)
>>> print(coord)
[-88.98  10.     4.41]
```

### MetaData
`medio.MetaData`

Together with the image's numpy array, the MetaData object is a necessary component for the I/O functions.

A MetaData object 'metadata' is mainly comprised of:
- `metadata.affine`: the affine (of class Affine)
- `metadata.coord_sys`: coordinate system ('itk' or 'nib') 
- `metadata.orig_ornt`: the original orientation of the image (used for saving)

Other properties of the metadata are derived from the affine:
- `metadata.spacing`: voxels spacing (a reference to `metadata.affine.spacing`) 
- `metadata.ornt`: the current image orientation (also depends on the coordinate system)

All these properties can be viewed easily in the console:
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
The MetaData method `metadata.is_right_handed_ornt()` checks for a right handed orientation according to the determinant 
of the direction matrix (`metadata.affine.direction`). This method can be useful before saving a dicom file or series, 
which should have a right-handed orientation.

#### Orientation
The orientation of a 3d image is string of length 3 which is derived from its affine and coordinate system (the 
convention). It denotes along which physical axis we move when we increase a single index out of `i, j, k` in the 
expression `np_image[i, j, k]`.

For example, 'RAS' orientation in itk:
- Right to left, Anterior to posterior, Superior to inferior

'RAS' in nib - also 'RAS+':
- left to Right, posterior to Anterior, inferior to Superior

Note that the conventions are opposite. Therefore, for stability reasons we use only itk convention in `read_img`'s 
argument `desired_ornt`.

For further discussion see 
[NiBabel's image orientation documentation](https://nipy.org/nibabel/image_orientation.html#image-voxel-orientation).

## Array and Metadata Operations
Some operations on an image affect also its metadata, for example resizing, rotations and cropping.

The class MedImg (`medio.medimg.medimg.MedImg`) holds an image array with its metadata, and supports some of these 
operations through the indexing syntax:
```python
>>> from medio.medimg.medimg import MedImg
>>> mimg = MedImg(np_image, metadata)
>>> new_mimg = mimg[:, 4:-4, ::3]
>>> print(new_mimg.metadata)
```
Ellipsis ('...') syntax is also supported. This indexing allows cropping and basic down-sampling, along with correct 
metadata update.
