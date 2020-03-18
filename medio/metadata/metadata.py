from medio.metadata.convert_nib_itk import convert, inv_axcodes, convert_affine
from medio.metadata.affine import Affine
from nibabel import aff2axcodes


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
        if coord_sys not in ['itk', 'nib']:
            raise ValueError('Metadata coord_sys must be \'itk\' or \'nib\'')
        self.coord_sys = coord_sys

    def __repr__(self):
        return (f'Affine:\n'
                f'{self.affine}\n'
                f'Spacing: {self.spacing}\n'
                f'Coordinate system: {self.coord_sys}\n'
                f'Orientation: {self.ornt}\n'
                f'Original orientation: {self.orig_ornt}')

    def convert(self, dest_coord_sys):
        """
        Converts the metadata coordinate system inplace to dest_coord_sys. Affects only affine and orig_ornt
        :param dest_coord_sys: the destination coordinate system - 'itk' or 'nib' (nifti)
        """
        if dest_coord_sys != self.coord_sys:
            self.affine, self.orig_ornt = convert(self.affine, self.orig_ornt)
            self.coord_sys = dest_coord_sys

    def get_ornt(self):
        """Returns current orientation based on the affine and coordinate system"""
        if self.coord_sys == 'nib':
            ornt_tup = aff2axcodes(self.affine)
        elif self.coord_sys == 'itk':
            ornt_tup = inv_axcodes(aff2axcodes(convert_affine(self.affine)))
        else:
            raise Exception('Unknown coord_sys:', self.coord_sys)
        ornt_str = ''.join(ornt_tup)
        return ornt_str

    @property
    def ornt(self):
        if self._ornt is None:
            self._ornt = self.get_ornt()
        return self._ornt

    @property
    def spacing(self):
        return self.affine.spacing
