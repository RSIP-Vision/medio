from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

import nibabel as nib
import nibabel.spatialimages
import numpy as np

from medio.metadata.affine import Affine
from medio.metadata.metadata import MetaData

if TYPE_CHECKING:
    import os

    from numpy.typing import NDArray


def _reorient_affine(
    nib_affine: NDArray[np.floating],
    orig_shape: tuple[int, ...],
    desired_nib_axcodes: str | tuple[str, ...],
) -> tuple[NDArray[np.floating], tuple[int, ...]]:
    """Reorient a nibabel affine and shape to `desired_nib_axcodes` without loading pixel data.

    :param nib_affine: 4x4 nibabel-convention affine matrix
    :param orig_shape: spatial shape in the current orientation (x, y, z)
    :param desired_nib_axcodes: destination orientation, e.g. 'LPI' or ('L', 'P', 'I')
    :return: (new_nib_affine, new_shape)
    """
    if isinstance(desired_nib_axcodes, str):
        desired_nib_axcodes = tuple(desired_nib_axcodes)
    start_ornt = nib.orientations.io_orientation(nib_affine)
    end_ornt = nib.orientations.axcodes2ornt(desired_nib_axcodes)
    ornt_transform = nib.orientations.ornt_transform(start_ornt, end_ornt)
    new_affine = nib.orientations.inv_ornt_aff(ornt_transform, orig_shape) @ nib_affine
    new_shape = tuple(orig_shape[int(t[0])] for t in ornt_transform)
    return new_affine, new_shape


NibImage = nibabel.spatialimages.SpatialImage


class NibIO:
    coord_sys: ClassVar[Literal["nib"]] = "nib"
    RGB_DTYPE = np.dtype([("R", np.uint8), ("G", np.uint8), ("B", np.uint8)])
    RGBA_DTYPE = np.dtype([("R", np.uint8), ("G", np.uint8), ("B", np.uint8), ("A", np.uint8)])

    @staticmethod
    def read_img(
        input_path: str | os.PathLike[str],
        desired_axcodes: tuple[str, ...] | str | None = None,
        header: bool = False,
        channels_axis: int | None = None,
    ) -> tuple[NDArray[np.floating], MetaData[object]]:
        """
        Reads a NIFTI file and returns the image array and metadata
        :param input_path: path-like (str or pathlib.Path) of the image file to read
        :param desired_axcodes: str, tuple of str or None - the desired orientation of the image to be returned
        :param header: whether to include a header attribute with additional metadata in the returned metadata
        :param channels_axis: if not None and the array dtype is structured, stacks the channels along channels_axis
        :return: image array and corresponding metadata
        """
        img_struct = nib.load(input_path)
        orig_ornt_str = "".join(nib.aff2axcodes(img_struct.affine))
        if desired_axcodes is not None:
            img_struct = NibIO.reorient(img_struct, desired_axcodes)
        img = np.asanyarray(img_struct.dataobj)
        if channels_axis is not None:
            img = NibIO.unravel_array(img, channels_axis)
        affine = Affine(img_struct.affine)
        metadata = MetaData(affine=affine, orig_ornt=orig_ornt_str, coord_sys=NibIO.coord_sys)
        if header:
            metadata.header = {key: img_struct.header[key] for key in img_struct.header}
        return img, metadata

    @staticmethod
    def read_meta(
        input_path: str | os.PathLike[str],
        desired_axcodes: tuple[str, ...] | str | None = None,
        header: bool = False,
    ) -> MetaData[object]:
        """
        Read only the metadata (affine, orientation, spatial shape) of a NIfTI file without loading pixel data.
        :param input_path: path to the NIfTI file
        :param desired_axcodes: optional desired orientation, e.g. 'RAS'
        :param header: if True, populate metadata.header with NIfTI header fields
        :return: MetaData with spatial_shape set
        """
        # nibabel already does lazy loading of the pixel data, so we can read the affine and header
        # without loading the whole image.
        img_struct = nib.load(input_path)
        orig_ornt_str = "".join(nib.aff2axcodes(img_struct.affine))
        nib_affine: NDArray[np.floating] = img_struct.affine
        orig_shape: tuple[int, ...] = tuple(img_struct.shape[:3])

        if desired_axcodes is not None:
            new_affine, new_shape = _reorient_affine(nib_affine, orig_shape, desired_axcodes)
        else:
            new_affine, new_shape = nib_affine, orig_shape

        metadata: MetaData[object] = MetaData(
            affine=Affine(new_affine),
            orig_ornt=orig_ornt_str,
            coord_sys=NibIO.coord_sys,
            spatial_shape=new_shape,
        )
        metadata.spatial_shape = new_shape
        if header:
            metadata.header = {key: img_struct.header[key] for key in img_struct.header}
        return metadata

    @staticmethod
    def save_img(
        filename: str | os.PathLike[str],
        img: NDArray[np.floating],
        metadata: MetaData[object],
        use_original_ornt: bool = True,
        channels_axis: int | None = None,
    ) -> None:
        """
        Saves the given image as a NIFTI file.
        :param filename: path-like output filename, including a '.nii.gz' or '.nii' suffix
        :param img: image data array
        :param metadata: the matching metadata
        :param use_original_ornt: whether to use the original orientation of the image of not
        :param channels_axis: if not None gives the channels axis of img (for channeled images RGB/RGBA)
        """
        if channels_axis is not None:
            img = NibIO.pack_channeled_img(img, channels_axis)
        orig_coord_sys = metadata.coord_sys
        metadata.convert(NibIO.coord_sys)
        img_struct = nib.Nifti1Image(img, metadata.affine)
        desired_axcodes = metadata.orig_ornt if use_original_ornt else None
        metadata.convert(orig_coord_sys)
        img_struct = NibIO.reorient(img_struct, desired_axcodes)
        nib.save(img_struct, filename)

    @staticmethod
    def reorient(img_struct: NibImage, desired_axcodes: tuple[str, ...] | str | None) -> NibImage:
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
    def unravel_array(array: NDArray[np.generic], channels_axis: int = -1) -> NDArray[np.generic]:
        """Simplify array dtype if it is a structured data type. For example, if the array if of RGB dtype:
        np.dtype([('R', 'uint8'), ('G', 'uint8'), ('B', 'uint8')])
        Convert it into an array with dtype 'uint8' and 3 channels for RGB in an additional last dimension"""
        dtype = array.dtype
        if not (hasattr(dtype, "__len__") and len(dtype) > 1):
            return array
        return np.stack([array[field] for field in dtype.fields], axis=channels_axis)

    @staticmethod
    def pack_channeled_img(img: NDArray[np.uint8], channels_axis: int) -> NDArray[np.void]:
        dtype = img.dtype
        if not np.issubdtype(dtype, np.uint8):
            raise ValueError(f'RGB or RGBA images must have dtype "np.uint8", got: "{dtype}"')
        n_channels = img.shape[channels_axis]
        img = np.moveaxis(img, channels_axis, -1)
        r_channel = img[..., 0]
        if n_channels == 3:
            img_rgb = np.empty_like(r_channel, dtype=NibIO.RGB_DTYPE)
            img_rgb["R"] = r_channel
            img_rgb["G"] = img[..., 1]
            img_rgb["B"] = img[..., 2]
            return img_rgb
        elif n_channels == 4:
            img_rgba = np.empty_like(r_channel, dtype=NibIO.RGBA_DTYPE)
            img_rgba["R"] = r_channel
            img_rgba["G"] = img[..., 1]
            img_rgba["B"] = img[..., 2]
            img_rgba["A"] = img[..., 3]
            return img_rgba
        else:
            raise ValueError(f"Invalid number of channels: {n_channels}, should be 3 (RGB) or 4 (RGBA)")
