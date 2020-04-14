import numpy as np
from nibabel import aff2axcodes
from medio.metadata.affine import Affine
from medio.metadata.convert_nib_itk import convert, inv_axcodes, convert_affine


class MetaData:
    def __init__(self, affine, orig_ornt=None, coord_sys='itk'):
        """
        Initialize medical image's metadata
        :param affine: affine matrix of class Affine, numpy float array of shape (4, 4)
        :param orig_ornt: orientation string code, str of length 3 or None (was not computed because the image was not
        reoriented)
        :param coord_sys: 'itk' or 'nib', the coordinate system of the given affine and orientation: itk or nib (nifti)
        """
        if not isinstance(affine, Affine):
            affine = Affine(affine)
        self.affine = affine
        self.orig_ornt = orig_ornt
        self._ornt = None
        self.check_valid_coord_sys(coord_sys)
        self.coord_sys = coord_sys

    @staticmethod
    def check_valid_coord_sys(coord_sys):
        if coord_sys not in ('itk', 'nib'):
            raise ValueError('Metadata coord_sys must be \'itk\' or \'nib\'')

    def __repr__(self):
        return (f'Affine:\n'
                f'{self.affine}\n'
                f'Spacing: {self.spacing}\n'
                f'Coordinate system: {self.coord_sys}\n'
                f'Orientation: {self.ornt}\n'
                f'Original orientation: {self.orig_ornt}')

    def convert(self, dest_coord_sys):
        """
        Converts the metadata coordinate system inplace to dest_coord_sys. Affects affine, ornt and orig_ornt
        :param dest_coord_sys: the destination coordinate system - 'itk' or 'nib' (nifti)
        """
        self.check_valid_coord_sys(dest_coord_sys)
        if dest_coord_sys != self.coord_sys:
            self.affine, self._ornt, self.orig_ornt = convert(self.affine, self._ornt, self.orig_ornt)
            self.coord_sys = dest_coord_sys

    def get_ornt(self):
        """Returns current orientation based on the affine and coordinate system"""
        if self.coord_sys == 'nib':
            ornt_tup = aff2axcodes(self.affine)
        elif self.coord_sys == 'itk':
            ornt_tup = inv_axcodes(aff2axcodes(convert_affine(self.affine)))
        else:
            raise ValueError('Unknown coord_sys:', self.coord_sys)
        ornt_str = ''.join(ornt_tup)
        return ornt_str

    @property
    def ornt(self):
        if self._ornt is None:
            self._ornt = self.get_ornt()
            # if self.orig_ornt is also None, the affine was not reoriented and the original orientation is the same
            if self.orig_ornt is None:
                self.orig_ornt = self._ornt
        return self._ornt

    @property
    def spacing(self):
        return self.affine.spacing

    def is_right_handed_ornt(self):
        """Check whether the affine orientation is right or left handed. The sign of the triple product of the
        direction matrix is calculated with a determinant. It should be +1 or -1 because it is a rotation matrix.
        +1 (-1) indicates right (left) handed orientation. 0 indicates a 0's column in the direction matrix which
        can occur in 2d images. To be used primarily before saving a dicom file or series"""
        if self.affine.dim != 3:
            raise ValueError('Right handed orientation is relevant only to a 3d space')
        return np.linalg.det(self.affine.direction) >= 0
