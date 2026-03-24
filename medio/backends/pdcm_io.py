from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal

import nibabel.spatialimages
import numpy as np
import pydicom
from dicom_numpy import combine_slices
from dicom_numpy.combine_slices import _extract_cosines, _validate_image_orientation

from medio.backends.nib_io import NibIO, _reorient_affine
from medio.backends.pdcm_unpack_ds import affine_from_dataset, unpack_dataset
from medio.metadata.convert_nib_itk import inv_axcodes
from medio.metadata.metadata import MetaData
from medio.metadata.pdcm_ds import MultiFrameFileDataset, convert_ds
from medio.utils.files import parse_series_uids

if TYPE_CHECKING:
    import os

    from numpy.typing import NDArray


class PdcmIO:
    coord_sys: ClassVar[Literal["itk"]] = "itk"
    # channels axes in the transposed image for pydicom and dicom-numpy. The actual axis is the first or the second
    # value of the tuple, according to the planar configuration (which is either 0 or 1)
    DEFAULT_CHANNELS_AXES_PYDICOM: tuple[int, int] = (0, -1)
    DEFAULT_CHANNELS_AXES_DICOM_NUMPY: tuple[int, int] = (0, 2)

    @staticmethod
    def read_img(
        input_path: str | os.PathLike[str],
        desired_ornt: str | None = None,
        header: bool = False,
        channels_axis: int | None = None,
        globber: str = "*",
        allow_default_affine: bool = False,
        series: str | int | None = None,
    ) -> tuple[NDArray[np.generic], MetaData[object]]:
        """
        Read a dicom file or folder (series) and return the numpy array and the corresponding metadata
        :param input_path: path-like object (str or pathlib.Path) of the file or directory to read
        :param desired_ornt: str, tuple of str or None - the desired orientation of the image to be returned
        :param header: whether to include a header attribute with additional metadata in the returned metadata (single
        file only)
        :param channels_axis: if not None and the image is channeled (e.g. RGB) move the channels to channels_axis in
        the returned image array
        :param globber: relevant for a directory - globber for selecting the series files (all files by default)
        :param allow_default_affine: whether to allow default affine when some tags are missing (multiframe file only)
        :param series: str or int of the series to read (in the case of multiple series in a directory)
        :return: numpy array and metadata
        """
        input_path = Path(input_path)
        # if there are channels, they must be in the last axis for the reorientation
        temp_channels_axis = -1
        if input_path.is_dir():
            img, metadata, channeled = PdcmIO.read_dcm_dir(
                input_path,
                header,
                globber,
                channels_axis=temp_channels_axis,
                series=series,
            )
        else:
            img, metadata, channeled = PdcmIO.read_dcm_file(
                input_path,
                header,
                allow_default_affine=allow_default_affine,
                channels_axis=temp_channels_axis,
            )
        img, metadata = PdcmIO.reorient(img, metadata, desired_ornt)
        # move the channels after the reorientation
        if channeled and channels_axis != temp_channels_axis:
            img = np.moveaxis(img, temp_channels_axis, channels_axis)
        return img, metadata

    @staticmethod
    def read_meta(
        input_path: str | os.PathLike[str],
        desired_ornt: str | None = None,
        header: bool = False,
        globber: str = "*",
        allow_default_affine: bool = False,
        series: str | int | None = None,
    ) -> MetaData[object]:
        """
        Read only the metadata (affine, orientation, spatial shape) of a DICOM file or directory without loading pixel
        data.
        :param input_path: path-like object (str or pathlib.Path) of the file or directory to read
        :param desired_ornt: optional orientation string to reorient the metadata, e.g. 'LPI'
        :param header: whether to include a header attribute (single file only; series raises NotImplementedError)
        :param globber: relevant for a directory - globber for selecting the series files
        :param allow_default_affine: use a default identity affine when geometric tags are missing (multiframe only)
        :param series: series to read when a directory has multiple series
        :return: MetaData with spatial_shape set
        """
        from medio.metadata.convert_nib_itk import convert_affine

        input_path = Path(input_path)
        if input_path.is_dir():
            slices = PdcmIO.extract_slices_no_pixels(input_path, globber, series)
            affine = PdcmIO._compute_series_affine(slices)
            ds0 = slices[0]
            spatial_shape: tuple[int, ...] = (int(ds0.Columns), int(ds0.Rows), len(slices))
            metadata: MetaData[object] = PdcmIO.aff2meta(affine)
            if header:
                raise NotImplementedError("header=True is currently not supported for a series")
        else:
            ds = pydicom.dcmread(input_path, stop_before_pixels=True)
            ds = convert_ds(ds)
            if ds.__class__ is MultiFrameFileDataset:
                affine = affine_from_dataset(ds, allow_default_affine=allow_default_affine)
                n_frames = int(ds.NumberOfFrames)
                spatial_shape = (int(ds.Columns), int(ds.Rows), n_frames)
            else:
                try:
                    _validate_image_orientation(ds.ImageOrientationPatient)
                    affine = PdcmIO._compute_single_slice_affine(ds)
                except AttributeError as e:
                    if allow_default_affine:
                        affine = np.eye(4, dtype=np.float32)
                    else:
                        raise AttributeError(str(e) + "\nTry using: allow_default_affine=True") from e
                spatial_shape = (int(ds.Columns), int(ds.Rows), 1)
            metadata = PdcmIO.aff2meta(affine)
            if header:
                metadata.header = {str(key): ds[key] for key in ds}

        if desired_ornt is not None and desired_ornt != metadata.ornt:
            orig_ornt = metadata.ornt
            # Convert affine to nib convention, reorient via pure matrix math, convert back
            nib_affine = convert_affine(metadata.affine)
            nib_desired = inv_axcodes(desired_ornt)
            new_nib_affine, spatial_shape = _reorient_affine(np.array(nib_affine), spatial_shape, nib_desired)
            metadata = MetaData(
                affine=convert_affine(new_nib_affine),
                orig_ornt=orig_ornt,
                coord_sys=PdcmIO.coord_sys,
                header=metadata.header,
            )

        metadata.spatial_shape = spatial_shape
        return metadata

    @staticmethod
    def _compute_single_slice_affine(ds: pydicom.Dataset) -> NDArray[np.float32]:
        """Compute affine for a regular (non-multiframe) single-slice DICOM dataset using header tags only."""
        row_cosine, column_cosine, _ = _extract_cosines(ds.ImageOrientationPatient)
        row_spacing, column_spacing = [float(x) for x in ds.PixelSpacing]
        slice_cosine = np.cross(row_cosine, column_cosine)
        slice_spacing = float(getattr(ds, "SpacingBetweenSlices", 1))
        transform = np.identity(4, dtype=np.float32)
        transform[:3, 0] = row_cosine * column_spacing
        transform[:3, 1] = column_cosine * row_spacing
        transform[:3, 2] = slice_cosine * slice_spacing
        transform[:3, 3] = [float(x) for x in ds.ImagePositionPatient]
        return transform

    @staticmethod
    def _compute_series_affine(slices: list[pydicom.Dataset]) -> NDArray[np.float32]:
        """Compute affine from a sorted list of DICOM slice datasets using header tags only."""
        ds0 = slices[0]
        row_cosine, column_cosine, _ = _extract_cosines(ds0.ImageOrientationPatient)
        row_spacing, column_spacing = [float(x) for x in ds0.PixelSpacing]
        first_pos = np.array([float(x) for x in ds0.ImagePositionPatient], dtype=np.float32)
        if len(slices) == 1:
            slice_cosine = np.cross(row_cosine, column_cosine)
            slice_spacing = float(getattr(ds0, "SpacingBetweenSlices", 1))
            slice_vector = slice_cosine * slice_spacing
        else:
            last_pos = np.array([float(x) for x in slices[-1].ImagePositionPatient], dtype=np.float32)
            slice_vector = (last_pos - first_pos) / (len(slices) - 1)
        transform = np.identity(4, dtype=np.float32)
        transform[:3, 0] = row_cosine * column_spacing
        transform[:3, 1] = column_cosine * row_spacing
        transform[:3, 2] = slice_vector
        transform[:3, 3] = first_pos
        return transform

    @staticmethod
    def read_dcm_file(
        filename: str | os.PathLike[str],
        header: bool = False,
        allow_default_affine: bool = False,
        channels_axis: int | None = None,
    ) -> tuple[NDArray[np.generic], MetaData[object], bool]:
        """
        Read a single dicom file.
        Return the image array, metadata, and whether it has channels
        """
        ds = pydicom.dcmread(filename)
        ds = convert_ds(ds)
        if ds.__class__ is MultiFrameFileDataset:
            img, affine = unpack_dataset(ds, allow_default_affine=allow_default_affine)
        else:
            img, affine = combine_slices([ds])
        metadata = PdcmIO.aff2meta(affine)
        if header:
            metadata.header = {str(key): ds[key] for key in ds}
        samples_per_pixel = ds.SamplesPerPixel
        img = PdcmIO.move_channels_axis(
            img,
            samples_per_pixel=samples_per_pixel,
            channels_axis=channels_axis,
            planar_configuration=ds.get("PlanarConfiguration", None),
            default_axes=PdcmIO.DEFAULT_CHANNELS_AXES_PYDICOM,
        )
        return img, metadata, samples_per_pixel > 1

    @staticmethod
    def read_dcm_dir(
        input_dir: str | os.PathLike[str],
        header: bool = False,
        globber: str = "*",
        channels_axis: int | None = None,
        series: str | int | None = None,
    ) -> tuple[NDArray[np.generic], MetaData[object], bool]:
        """
        Reads a 3D dicom image: input path can be a file or directory (DICOM series).
        Return the image array, metadata, and whether it has channels
        """
        # find all dicom files within the specified folder, read every file separately and sort them by InstanceNumber
        slices = PdcmIO.extract_slices(input_dir, globber=globber, series=series)
        img, affine = combine_slices(slices)
        metadata = PdcmIO.aff2meta(affine)
        if header:
            # TODO: add header support, something like
            #  metdata.header = [{str(key): ds[key] for key in ds.keys()} for ds in slices]
            raise NotImplementedError("header=True is currently not supported for a series")
        samples_per_pixel = slices[0].SamplesPerPixel
        img = PdcmIO.move_channels_axis(
            img,
            samples_per_pixel=samples_per_pixel,
            channels_axis=channels_axis,
            planar_configuration=slices[0].get("PlanarConfiguration", None),
            default_axes=PdcmIO.DEFAULT_CHANNELS_AXES_DICOM_NUMPY,
        )
        return img, metadata, samples_per_pixel > 1

    @staticmethod
    def extract_slices(
        input_dir: str | os.PathLike[str],
        globber: str = "*",
        series: str | int | None = None,
    ) -> list[pydicom.Dataset]:
        """Extract slices from input_dir and return them sorted"""
        files = Path(input_dir).glob(globber)
        slices = [pydicom.dcmread(filename) for filename in files]

        # filter by Series Instance UID
        datasets = {}
        for slc in slices:
            key = slc.SeriesInstanceUID
            datasets[key] = [*datasets.get(key, []), slc]

        series_uid = parse_series_uids(input_dir, datasets.keys(), series, globber)
        slices = datasets[series_uid]

        slices.sort(key=lambda ds: ds.get("InstanceNumber", 0))
        return slices

    @staticmethod
    def extract_slices_no_pixels(
        input_dir: str | os.PathLike[str],
        globber: str = "*",
        series: str | int | None = None,
    ) -> list[pydicom.Dataset]:
        """Extract slices from input_dir without loading pixel data (header-only).
        Returns sorted list of pydicom Datasets read with stop_before_pixels=True."""
        files = list(Path(input_dir).glob(globber))
        slices = [pydicom.dcmread(f, stop_before_pixels=True) for f in files]

        datasets: dict[str, list[pydicom.Dataset]] = {}
        for slc in slices:
            key = slc.SeriesInstanceUID
            datasets[key] = [*datasets.get(key, []), slc]

        series_uid = parse_series_uids(input_dir, datasets.keys(), series, globber)
        slices = datasets[series_uid]
        slices.sort(key=lambda ds: ds.get("InstanceNumber", 0))
        return slices

    @staticmethod
    def aff2meta(affine: NDArray[np.floating]) -> MetaData[object]:
        return MetaData(affine, coord_sys=PdcmIO.coord_sys)

    @staticmethod
    def move_channels_axis(
        array: NDArray[np.generic],
        samples_per_pixel: int,
        channels_axis: int | None = None,
        planar_configuration: int | None = None,
        default_axes: tuple[int, int] = DEFAULT_CHANNELS_AXES_PYDICOM,
    ) -> NDArray[np.generic]:
        """Move the channels axis from the original axis to the destined channels_axis"""
        if (samples_per_pixel == 1) or (channels_axis is None):
            # no rearrangement is needed
            return array

        # extract the original channels axis
        if planar_configuration not in [0, 1]:
            raise ValueError(f"Invalid Planar Configuration value: {planar_configuration}")

        orig_axis = default_axes[planar_configuration]
        flag = True  # original channels axis is assigned
        shape = array.shape
        # validate that the assigned axis matches samples_per_pixel, if not - try to search for it
        if shape[orig_axis] != samples_per_pixel:
            flag = False
            for i, sz in enumerate(shape):
                if sz == samples_per_pixel:
                    orig_axis = i
                    flag = True
                    break

        if not flag:
            raise ValueError("The original channels axis was not detected")

        return np.moveaxis(array, orig_axis, channels_axis)

    @staticmethod
    def reorient(
        img: NDArray[np.generic],
        metadata: MetaData[object],
        desired_ornt: str | None,
    ) -> tuple[NDArray[np.generic], MetaData[object]]:
        """
        Reorient img array and affine (in the metadata) to desired_ornt (str) using nibabel.
        desired_ornt is in itk convention.
        Note that if img has channels (RGB for example), they must be in last axis
        """
        if (desired_ornt is None) or (desired_ornt == metadata.ornt):
            return img, metadata
        # convert from pydicom (itk) to nibabel convention
        metadata.convert(NibIO.coord_sys)
        orig_ornt = metadata.ornt
        desired_ornt = inv_axcodes(desired_ornt)
        # use nibabel for the reorientation
        img_struct = nibabel.spatialimages.SpatialImage(img, metadata.affine)
        reoriented_img_struct = NibIO.reorient(img_struct, desired_ornt)

        img = np.asanyarray(reoriented_img_struct.dataobj)
        metadata = MetaData(
            reoriented_img_struct.affine,
            orig_ornt=orig_ornt,
            coord_sys=NibIO.coord_sys,
            header=metadata.header,
        )
        # convert back to pydicom convention
        metadata.convert(PdcmIO.coord_sys)
        return img, metadata

    @staticmethod
    def save_arr2dcm_file(
        output_filename: str | os.PathLike[str],
        template_filename: str | os.PathLike[str],
        img_arr: NDArray[np.generic],
        dtype: np.dtype[np.generic] | str | None = None,
        keep_rescale: bool = False,
    ) -> None:
        """
        Writes a dicom single file image using template file, without the intensity transformation from template dataset
        unless keep_rescale is True
        :param output_filename: path-like object of the output file to be saved
        :param template_filename: the single dicom scan whose metadata is used
        :param img_arr: numpy array of the image to be saved, should be in the same orientation as template_filename
        :param dtype: the dtype for the numpy array, for example 'int16'. If None - will use the dtype of the template
        :param keep_rescale: whether to keep intensity rescale values
        """
        ds = pydicom.dcmread(template_filename)
        ds = convert_ds(ds)
        if not keep_rescale:
            if isinstance(ds, MultiFrameFileDataset):
                ds.del_intensity_trans()
            else:
                del ds.RescaleSlope
                del ds.RescaleIntercept
        if dtype is None:
            img_arr = img_arr.astype(ds.pixel_array.dtype, copy=False)
        else:
            img_arr = img_arr.astype(dtype, copy=False)
        ds.PixelData = img_arr.tobytes()
        ds.save_as(output_filename)
