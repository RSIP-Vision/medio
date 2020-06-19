# medio

**Medical images I/O python package**

This package unifies the io engines of itk, nibabel, and pydicom (and dicom-numpy) packages in a simple and 
comprehensive interface.

It includes conversion between the metadata conventions, reorientations, affine matrix computation for itk and pydicom
and saving dicom series or file.

# Installation
First, make sure you have the latest pip version (better to close PyCharm or any other program which uses the 
environments):
```
(<env-name>) >pip install --upgrade pip
```
Then, download the [.whl file](/uploads/eefdcc80d1e44d6d0d0acaabc4a02ee9/medio-0.2.0-py3-none-any.whl)
and install it with:
```
(<env-name>) >pip install medio-0.2.0-py3-none-any.whl
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

### read_img
`medio.read_img(input_path, desired_ornt=None, backend=None, dtype=None, header=False, channels_axis=-1, **kwargs)`
- `input_path`: *path-like*<br>
  Path for the data to be read (str or pathlib.Path object for example). It can be a file or a folder (in 
the case of a dicom series). It is the only required parameter.
  If the input path is s folder, it should contain a single dicom series.
- Returns: *array, metadata*<br>
  array of type *numpy.ndarray* and metadata of type *medio.MetaData*. The first is a numpy array of the 
image, and the second is a metadata object of the image (see [MetaData](#metadata) class documentation).

Optional parameters:
- `desired_ornt`: *orientation string or None*<br>
  The desired orientation of the returned image array, e.g. 'RAI'. If None, no reorientation is performed.
  The desired orientation is in itk standard, even when the IO engine ("backend") is nibabel which uses a different 
  standard (see [Orientation](#orientation)).<br>
  If you use pydicom backend, it should be None.<br>
  If `desired_ornt` is the same as the original image orientation, no reorientation is performed.
- `backend`: *'nib', 'itk', 'pydicom', 'pdcm', or None*<br>
  The backend IO engine to use: 'nib' (nibabel), 'itk' or 'pydicom' (also 'pdcm'). If None, 
the backend is chosen automatically: 'nib' for nifti files (e.g. '.nii' or '.nii.gz' suffix), otherwise 'itk'.
- `dtype`: *numpy data-type or None*<br>
  If not None, equivalent to `array.astype(dtype)` on the returned image array.
- `header`: *bool*<br>
  If True, the returned metadata includes also a `metadata.header` attribute which stores the raw metadata of the file 
  as a dictionary.<br>
  This is not implemented for series of files (folder `input_path`), and not used during saving.
- `channels_axis`: *int or None*<br>
  If not None and the image has more than a single channel / component (e.g. RGB or RGBA), the channels axis 
  are is `channels_axis`. If None, the backend's original convention is used.

`**kwargs` are additional per-backend optional parameters:
- 'itk' backend:
  - `pixel_type=itk.SS`: *itk pixel-type or None*<br>
    Itk pixel type of the image file/folder. The default value is int16 (`itk.SS` - Signed Short). 
    Other common pixel types are: `itk.UC` - uint8, `itk.US` - uint16.<br>
    You can use the function `itk.ctype` in order to convert C-types to itk types. For example:<br>
    `itk.ctype('unsigned short') == itk.US`
  - `fallback_only=True`: *bool*<br>
    If True, the pixel type is automatically found and if failed then `pixel_type` is used 
    (`pixel_type` must be not None in this case).<br>
    Note: if `itk.imread(input_path)` fails, using `fallback_only=True` will result in a slightly 
    inferior performance. If you know what is pixel-type of the image, you can set it with `pixel_type`
    and use `fallback_only=False`.

- 'pydicom' backend
  - `globber='*'`: *str*<br>
    Relevant for a directory - glob pattern for selecting the series files (all files by default).
  - `allow_default_affine=False`: *bool*<br>
    Relevant for multiframe dicom file - if True and the dicom miss some physical tags for the affine
    calculation, use a default affine value.

### save_img
`medio.save_img(filename, np_image, metadata, use_original_ornt=True, backend=None, dtype=None, channels_axis=None,
mkdir=False, parents=False, **kwargs)`
- `filename`: *path-like*<br>
  The file to be saved.
- `np_image`: *numpy.ndarray*<br>
  The image array.
- `metadata`: *medio.MetaData*<br>
  The corresponding metadata.

Optional parameters:
- `use_original_ornt`: *bool*<br> 
  Whether to save in the original orientation stored in `metadata.orig_ornt` or not.
- `backend`: *'nib', 'itk' or None*<br>
  The backend to use: 'nib' or 'itk'. If None, 'nib' is chosen for nifti files and 'itk' otherwise.
- `dtype`: *numpy data-type or None*<br>
  If not None, equivalent to passing `np_image.astype(dtype)`. Note that not every dtype is supported 
in saving, so make sure what is the dtype of the image array you want to save.
- `channels_axis`: *int or None*<br>
  If not None, the image has channels (e.g. RGB) along the axis `channels_axis` of `np_image`.
- `mkdir`: *bool*<br>
  If True, creates the directory of `filename`.
- `parents`: *bool*<br>
  To be used with `mkdir=True`. If True, creates also the parent directories. 

'itk' backend optional parameters (`**kwargs`):
- `allow_dcm_reorient=False`: *bool*<br>
 When saving a dicom file ('.dcm' or '.dicom' suffix) the image orientation should be right-handed.
 If it is left-handed, the image can be reoriented to a right-handed orientation with setting this 
parameter to True, which flips the last axis direction.
- `compression=False`: *bool*<br>
  Whether to use compression in itk writer. Using a '.nii.gz' suffix in `filename` also compresses 
the image.

### save_dir
`medio.save_dir(dirname, np_image, metadata, use_original_ornt=True, dtype=None, channels_axis=None,
parents=False, allow_dcm_reorient=False, **kwargs)`

Save a 3d numpy array `np_image` as a dicom series of 2d slices in the directory `dirname` (itk backend).

- `dirname`: *path-like*<br>
  The directory to save the files in (str or pathlib.Path). If it exists - must be empty.

The other parameters: `np_image`, `metadata`, `use_original_ornt`, `dtype`, `channels_axis`, `parents`
and `allow_dcm_reorient` are equivalent to those used in [save_img](#save_img).

Additional optional parameters (`**kwargs`): 
- `pattern='IM{}.dcm'`: *str*<br>
  Pattern for the filenames to save, including a placeholder ('`{}`') for the slice number.
- `metadata_dict=None`: *dict or None*<br>
  Dictionary of metadata for adding tags or overriding the default values. For example, 
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
