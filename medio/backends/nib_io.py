import nibabel as nib
from pathlib import Path
from medio.metadata.metadata import MetaData
from medio.metadata.affine import Affine


class NibIO:
    coord_sys = 'nib'

    @staticmethod
    def read_img(input_path, desired_axcodes=None, dtype='int16'):
        """Reads a NIFTI file"""
        img_struct = nib.load(input_path)
        orig_ornt_str = ''.join(nib.aff2axcodes(img_struct.affine))
        if desired_axcodes is not None:
            img_struct = NibIO.reorient(img_struct, desired_axcodes)
        img = img_struct.get_fdata().astype(dtype)
        affine = Affine(img_struct.affine)
        metadata = MetaData(affine=affine, orig_ornt=orig_ornt_str, coord_sys=NibIO.coord_sys)
        return img, metadata

    @staticmethod
    def save_img(filename, img, metadata, use_original_ornt=True, dtype='int16'):
        """
        Saves the given image as a NIFTI file.
        :param filename: output filename, including a '.nii.gz' suffix.
        :param img: image data array.
        :param metadata: the matching metadata.
        """
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        metadata.convert(NibIO.coord_sys)
        img_struct = nib.Nifti1Image(img.astype(dtype), metadata.affine)
        if use_original_ornt:
            desired_axcodes = metadata.orig_ornt
            img_struct = NibIO.reorient(img_struct, desired_axcodes)
        nib.save(img_struct, filename)

    @staticmethod
    def reorient(img_struct, desired_axcodes=None):
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
