from typing import Union

import nibabel as nib
import numpy as np

from medio.metadata.affine import Affine
from medio.metadata.metadata import MetaData


class NibIO:
    coord_sys = 'nib'

    @staticmethod
    def read_img(input_path, desired_axcodes=None, unravel=False):
        """Reads a NIFTI file"""
        img_struct = nib.load(input_path)
        orig_ornt_str = ''.join(nib.aff2axcodes(img_struct.affine))
        if desired_axcodes is not None:
            img_struct = NibIO.reorient(img_struct, desired_axcodes)
        img = np.asanyarray(img_struct.dataobj)
        if unravel:
            img = NibIO.unravel_array(img)
        affine = Affine(img_struct.affine)
        metadata = MetaData(affine=affine, orig_ornt=orig_ornt_str, coord_sys=NibIO.coord_sys)
        return img, metadata

    @staticmethod
    def save_img(filename, img, metadata, use_original_ornt=True):
        """
        Saves the given image as a NIFTI file.
        :param filename: output filename, including a '.nii.gz' or '.nii' suffix.
        :param img: image data array.
        :param metadata: the matching metadata.
        :param use_original_ornt: whether to use the original orientation of the image of not
        """
        orig_coord_sys = metadata.coord_sys
        metadata.convert(NibIO.coord_sys)
        img_struct = nib.Nifti1Image(img, metadata.affine)
        desired_axcodes = metadata.orig_ornt if use_original_ornt else None
        metadata.convert(orig_coord_sys)
        img_struct = NibIO.reorient(img_struct, desired_axcodes)
        nib.save(img_struct, filename)

    @staticmethod
    def reorient(img_struct, desired_axcodes: Union[tuple, str, None]):
        """Reorient a nibabel image to a desired orientation described by desired_axcodes strings tuple, for example
        ('L', 'P', 'I'). If desired_axcodes is None it returns the given img_struct"""
        if desired_axcodes is not None:
            if isinstance(desired_axcodes, str):
                desired_axcodes = tuple(desired_axcodes)
            start_ornt = nib.orientations.io_orientation(img_struct.affine)
            end_ornt = nib.orientations.axcodes2ornt(desired_axcodes)
            ornt_tform = nib.orientations.ornt_transform(start_ornt, end_ornt)
            img_struct = img_struct.as_reoriented(ornt_tform)
        return img_struct

    @staticmethod
    def unravel_array(array):
        """Simplify array dtype if it is a structured data type. For example, if the array if of RGB dtype:
        np.dtype([('R', 'uint8'), ('G', 'uint8'), ('B', 'uint8')])
        Convert it into an array with dtype 'uint8' and 3 channels for RGB in an additional last dimension"""
        dtype = array.dtype
        if not (hasattr(dtype, '__len__') and len(dtype) > 1):
            return array
        return np.stack([array[field] for field in dtype.fields], axis=-1)
