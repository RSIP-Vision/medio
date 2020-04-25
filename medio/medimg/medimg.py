from medio.metadata.affine import Affine
from medio.metadata.metadata import MetaData
from medio.read_save import read_img, save_img
from medio.utils.explicit_slicing import explicit_inds


class MedImg:
    def __init__(self, np_image, metadata, filename=None, **kwargs):
        """
        Class for a single medical image, represented by numpy array and metadata object - image affine, original
        orientation and coordinate system. The class allows performing operations on the image with respective update of
        the metadata (mainly affine).
        The class can be instantiated also with a filename:
        >>> MedImg(None, None, '../scan1.mhd')
        With possible kwargs for the reader.
        """
        if filename is not None:
            np_image, metadata = read_img(filename, **kwargs)
        self.np_image = np_image
        self.metadata = metadata

    def save(self, filename, **kwargs):
        save_img(filename, self.np_image, self.metadata, **kwargs)

    def __getitem__(self, item):
        """
        This method allows cropping and basic down sampling:
        >>> mimg = MedImg(np_image, metadata)
        >>> new_mimg = mimg[:, 4:-4, ::3]
        >>> print(new_mimg.metadata)
        Ellipsis (...) is also supported
        """
        np_image = self.np_image[item]
        start, stop, stride = explicit_inds(item, self.np_image.shape)
        affine = Affine(self.metadata.Affine.copy())
        affine.origin = affine.index2coord(start)
        affine.spacing = affine.spacing * stride
        metadata = MetaData(affine, self.metadata.orig_ornt, self.metadata.coord_sys)
        return MedImg(np_image, metadata)
