"""
This module is equivalent to dicom_numpy's module: combine_slices.py, but here for a single dicom dataset
"""
import logging

import numpy as np

from dicom_numpy.combine_slices import _validate_image_orientation, _extract_cosines, _requires_rescaling


logger = logging.getLogger(__name__)


def unpack_dataset(dataset, rescale=None):
    """
    Given a pydicom dataset of a single image file return three-dimensional numpy array.
    Also calculate a 4x4 affine transformation matrix that converts the ijk-pixel-indices
    into the xyz-coordinates in the DICOM patient's coordinate system.

    Returns a two-tuple containing the 3D-ndarray and the affine matrix.

    If `rescale` is set to `None` (the default), then the image array dtype
    will be preserved, unless any of the DICOM images contain either the
    `Rescale Slope
    <https://dicom.innolitics.com/ciods/ct-image/ct-image/00281053>`_ or the
    `Rescale Intercept <https://dicom.innolitics.com/ciods/ct-image/ct-image/00281052>`_
    attributes.  If either of these attributes are present they will be applied.

    If `rescale` is `True` the voxels will be cast to `float32`, if set to
    `False`, the original dtype will be preserved even if DICOM rescaling information is present.

    The returned array has the column-major byte-order.

    This function requires that the datasets:

    - Be in same series (have the same
      `Series Instance UID <https://dicom.innolitics.com/ciods/ct-image/general-series/0020000e>`_,
      `Modality <https://dicom.innolitics.com/ciods/ct-image/general-series/00080060>`_,
      and `SOP Class UID <https://dicom.innolitics.com/ciods/ct-image/sop-common/00080016>`_).
    - The binary storage of each slice must be the same (have the same
      `Bits Allocated <https://dicom.innolitics.com/ciods/ct-image/image-pixel/00280100>`_,
      `Bits Stored <https://dicom.innolitics.com/ciods/ct-image/image-pixel/00280101>`_,
      `High Bit <https://dicom.innolitics.com/ciods/ct-image/image-pixel/00280102>`_, and
      `Pixel Representation <https://dicom.innolitics.com/ciods/ct-image/image-pixel/00280103>`_).
    - The image slice must approximately form a grid. This means there can not
      be any missing internal slices (missing slices on the ends of the dataset
      are not detected).
    - It also means that  each slice must have the same
      `Rows <https://dicom.innolitics.com/ciods/ct-image/image-pixel/00280010>`_,
      `Columns <https://dicom.innolitics.com/ciods/ct-image/image-pixel/00280011>`_,
      `Pixel Spacing <https://dicom.innolitics.com/ciods/ct-image/image-plane/00280030>`_, and
      `Image Orientation (Patient) <https://dicom.innolitics.com/ciods/ct-image/image-plane/00200037>`_
      attribute values.
    - The direction cosines derived from the
      `Image Orientation (Patient) <https://dicom.innolitics.com/ciods/ct-image/image-plane/00200037>`_
      attribute must, within 1e-4, have a magnitude of 1.  The cosines must
      also be approximately perpendicular (their dot-product must be within
      1e-4 of 0).  Warnings are displayed if any of these approximations are
      below 1e-8, however, since we have seen real datasets with values up to
      1e-4, we let them pass.
    - The `Image Position (Patient) <https://dicom.innolitics.com/ciods/ct-image/image-plane/00200032>`_
      values must approximately form a line.

    If any of these conditions are not met, a `dicom_numpy.DicomImportException` is raised.
    """
    _validate_image_orientation(dataset.ImageOrientationPatient)
    voxels = _unpack_pixel_array(dataset, rescale)
    transform = _ijk_to_patient_xyz_transform_matrix(dataset)

    return voxels, transform


def _unpack_pixel_array(dataset, rescale=None):
    voxels = dataset.pixel_array.T

    if rescale is None:
        rescale = _requires_rescaling(dataset)

    if rescale:
        voxels = voxels.astype('int16')
        slope = getattr(dataset, 'RescaleSlope', 1)
        intercept = getattr(dataset, 'RescaleIntercept', 0)
        if int(slope) == slope and int(intercept) == intercept:
            slope = int(slope)
            intercept = int(intercept)
        voxels = voxels * slope + intercept

    return voxels


def _ijk_to_patient_xyz_transform_matrix(dataset):
    image_orientation = dataset.ImageOrientationPatient
    row_cosine, column_cosine, slice_cosine = _extract_cosines(image_orientation)

    row_spacing, column_spacing = dataset.PixelSpacing
    slice_spacing = float(getattr(dataset, 'SliceThickness', 0))

    transform = np.identity(4, dtype=np.float32)

    transform[:3, 0] = row_cosine * column_spacing
    transform[:3, 1] = column_cosine * row_spacing
    transform[:3, 2] = slice_cosine * slice_spacing

    transform[:3, 3] = dataset.ImagePositionPatient

    return transform
