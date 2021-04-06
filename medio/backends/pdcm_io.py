from pathlib import Path

import nibabel as nib
import numpy as np
import pydicom
from dicom_numpy import combine_slices

from medio.backends.nib_io import NibIO
from medio.backends.pdcm_unpack_ds import unpack_dataset
from medio.metadata.convert_nib_itk import inv_axcodes
from medio.metadata.metadata import MetaData
from medio.metadata.pdcm_ds import convert_ds, MultiFrameFileDataset
from medio.utils.files import parse_series_uids


class PdcmIO:
    coord_sys = 'itk'
    # channels axes in the transposed image for pydicom and dicom-numpy. The actual axis is the first or the second
    # value of the tuple, according to the planar configuration (which is either 0 or 1)
    DEFAULT_CHANNELS_AXES_PYDICOM = (0, -1)
    DEFAULT_CHANNELS_AXES_DICOM_NUMPY = (0, 2)

    @staticmethod
    def read_img(input_path, desired_ornt=None, header=False, channels_axis=None, globber='*',
                 allow_default_affine=False, series=None):
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
        temp_channels_axis = -1  # if there are channels, they must be in the last axis for the reorientation
        if input_path.is_dir():
            img, metadata, channeled = PdcmIO.read_dcm_dir(input_path, header, globber,
                                                           channels_axis=temp_channels_axis, series=series)
        else:
            img, metadata, channeled = PdcmIO.read_dcm_file(
                input_path, header, allow_default_affine=allow_default_affine, channels_axis=temp_channels_axis)
        img, metadata = PdcmIO.reorient(img, metadata, desired_ornt)
        # move the channels after the reorientation
        if channeled and channels_axis != temp_channels_axis:
            img = np.moveaxis(img, temp_channels_axis, channels_axis)
        return img, metadata

    @staticmethod
    def read_dcm_file(filename, header=False, allow_default_affine=False, channels_axis=None):
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
            metadata.header = {str(key): ds[key] for key in ds.keys()}
        samples_per_pixel = ds.SamplesPerPixel
        img = PdcmIO.move_channels_axis(img, samples_per_pixel=samples_per_pixel, channels_axis=channels_axis,
                                        planar_configuration=ds.get('PlanarConfiguration', None),
                                        default_axes=PdcmIO.DEFAULT_CHANNELS_AXES_PYDICOM)
        return img, metadata, samples_per_pixel > 1

    @staticmethod
    def read_dcm_dir(input_dir, header=False, globber='*', channels_axis=None, series=None):
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
        img = PdcmIO.move_channels_axis(img, samples_per_pixel=samples_per_pixel, channels_axis=channels_axis,
                                        planar_configuration=slices[0].get('PlanarConfiguration', None),
                                        default_axes=PdcmIO.DEFAULT_CHANNELS_AXES_DICOM_NUMPY)
        return img, metadata, samples_per_pixel > 1

    @staticmethod
    def extract_slices(input_dir, globber='*', series=None):
        """Extract slices from input_dir and return them sorted"""
        files = Path(input_dir).glob(globber)
        slices = [pydicom.dcmread(filename) for filename in files]

        # filter by Series Instance UID
        datasets = {}
        for slc in slices:
            key = slc.SeriesInstanceUID
            datasets[key] = datasets.get(key, []) + [slc]

        series_uid = parse_series_uids(input_dir, datasets.keys(), series, globber)
        slices = datasets[series_uid]

        slices.sort(key=lambda ds: ds.get('InstanceNumber', 0))
        return slices

    @staticmethod
    def aff2meta(affine):
        return MetaData(affine, coord_sys=PdcmIO.coord_sys)

    @staticmethod
    def move_channels_axis(array, samples_per_pixel, channels_axis=None, planar_configuration=None,
                           default_axes=DEFAULT_CHANNELS_AXES_PYDICOM):
        """Move the channels axis from the original axis to the destined channels_axis"""
        if (samples_per_pixel == 1) or (channels_axis is None):
            # no rearrangement is needed
            return array

        # extract the original channels axis
        if planar_configuration not in [0, 1]:
            raise ValueError(f'Invalid Planar Configuration value: {planar_configuration}')

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
            raise ValueError('The original channels axis was not detected')

        return np.moveaxis(array, orig_axis, channels_axis)

    @staticmethod
    def reorient(img, metadata, desired_ornt):
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
        img_struct = nib.spatialimages.SpatialImage(img, metadata.affine)
        reoriented_img_struct = NibIO.reorient(img_struct, desired_ornt)

        img = np.asanyarray(reoriented_img_struct.dataobj)
        metadata = MetaData(reoriented_img_struct.affine, orig_ornt=orig_ornt, coord_sys=NibIO.coord_sys,
                            header=metadata.header)
        # convert back to pydicom convention
        metadata.convert(PdcmIO.coord_sys)
        return img, metadata

    @staticmethod
    def save_arr2dcm_file(output_filename, template_filename, img_arr, dtype=None, keep_rescale=False):
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
