from pathlib import Path

import pydicom
from dicom_numpy import combine_slices

from medio.backends.pdcm_unpack_ds import unpack_dataset
from medio.metadata.metadata import MetaData
from medio.metadata.pdcm_ds import convert_ds, FramedFileDataset


class PdcmIO:
    coord_sys = 'itk'

    @staticmethod
    def read_img(input_path, globber='*'):
        """
        Read a dicom file or folder (series) and return the numpy array and the corresponding metadata
        :param input_path: path-like object (str or pathlib.Path) of the file or directory to read
        :param globber: relevant for a directory - globber for selecting the series files (all files by default)
        :return: numpy array and metadata
        """
        input_path = Path(input_path)
        if input_path.is_dir():
            return PdcmIO.read_dcm_dir(input_path, globber)
        else:
            return PdcmIO.read_dcm_file(input_path)

    @staticmethod
    def read_dcm_file(filename):
        """Read a single dicom file"""
        ds = pydicom.dcmread(str(filename))
        ds = convert_ds(ds)
        img, affine = unpack_dataset(ds)
        return img, PdcmIO.aff2meta(affine)

    @staticmethod
    def read_dcm_dir(input_dir, globber='*'):
        """Reads a 3D dicom image: input path can be a file or directory (DICOM series)"""
        # find all dicom files within the specified folder, read every file separately and sort them by InstanceNumber
        files = list(Path(input_dir).glob(globber))
        if len(files) == 0:
            raise FileNotFoundError(f'Received an empty directory: \'{input_dir}\'')
        elif len(files) == 1:
            return PdcmIO.read_dcm_file(files[0])
        slices = [pydicom.dcmread(str(filename)) for filename in files]
        slices.sort(key=lambda x: int(x.InstanceNumber))
        img, affine = combine_slices(slices)
        return img, PdcmIO.aff2meta(affine)

    @staticmethod
    def aff2meta(affine):
        return MetaData(affine, coord_sys=PdcmIO.coord_sys)

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
            if isinstance(ds, FramedFileDataset):
                ds.del_intensity_trans()
            else:
                del ds.RescaleSlope
                del ds.RescaleIntercept
        if dtype is None:
            img_arr = img_arr.astype(ds.pixel_array.dtype)
        else:
            img_arr = img_arr.astype(dtype)
        ds.PixelData = img_arr.tobytes()
        ds.save_as(output_filename)
