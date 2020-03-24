Key features, pros & cons:
ITK
The engine behind ITK-SNAP
Presents the most comprehensive formats support
Originally written in C++ - wrapped with swig to python. Consequently, itk python code is unnatural/not pythonic and hard to understand
Uses itk world coordinates for origin and directions. Default orientation: RAI
Dicom file: can save only UChar - unsigned int 8, good for segmentations. int16/float are not supported
Derived: SimpleITK (sitk), allows saving dicom folder

NiBabel
Pythonic nifti package
Contains reorientation handling
Packs metadata into affine matrix
Uses nifti world coordinates for affine and orientation. Default orientation: RAS+ = LPI

Pydicom
Pythonic dicom package
Relatively easy access to tags
Supports modifying dicom single file pixel data and saving it - dicom2dicom
No reorientation support. Can use nibabel: ornt_transform and apply_orientation. Get original orientation with itk
Derived: dicom_numpy for combining slices - dicom folder (?), high level
https://nipy.org/nibabel/reference/nibabel.orientations.html#ornt-transform

===============
Performance:	nifti segmentation: 1. itk, 2. nib
	nifti image (dense): 1. nib, 2. itk

===============	
input:	nifti	dicom folder	dicom file
output:			
nifti	v	v	v
dicom folder	v	v	v
dicom file	v	v	v

===============
Default orientation affine matrix: (with origin = (0,0,0) and pixdims = (1,1,1))			
1	0	0	0
0	1	0	0
0	0	1	0
0	0	0	1

===============
ITK bug:
In keras fit_generator, when fitting a Sequence instance with
model.fit_generator(..., workers!=1,
max_queue_size=tc.MAX_QUEUE_SIZE,
use_multiprocessing=False)

There is a bug in ITK:
File "C:\Users\%User%\Anaconda3\envs\tf\lib\site-packages\itkBase.py", line 63, in LoadModule
swig.__dict__.update(this_module.swig.__dict__)
AttributeError: module 'ITKIOImageBase' has no attribute 'swig'

===============
IO engine	ITK	NiBabel	Pydicom
nifti support	v	v	x
dicom support	v	x	v
single dicom file reader	v	x	v
single dicom file writer	v	x	v
reorientation	v	v	x
metadata	v	v	v
saving dicom int16		x	v - with template
saving dicom uint8	v	x	
pythonic	x	v	v
high level	x	v	x