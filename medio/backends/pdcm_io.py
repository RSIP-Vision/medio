import pydicom
from pydicom.tag import Tag
from dicom_numpy import combine_slices
from pathlib import Path
from medio.backends.unpack_ds import unpack_dataset
from medio.metadata.pdcm_ds import convert_ds, FramedFileDataset
from medio.metadata.metadata import MetaData


class PdcmIO:
    coord_sys = 'itk'

    @staticmethod
    def read_img(input_path, globber='*'):
        input_path = Path(input_path)
        if input_path.is_file():
            return PdcmIO.read_dcm_file(input_path)
        elif input_path.is_dir():
            return PdcmIO.read_dcm_dir(input_path, globber)
        else:
            raise IOError('Invalid input path')

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
        # find all dicom files within the specified folder, read every file separately sort them by InstanceNumber
        files = list(Path(input_dir).glob(globber))
        if len(files) == 0:
            raise IOError(f'Received an empty directory: {str(input_dir)}')
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
    def save_arr2dcm_file(output_filename, img_arr, template_filename, keep_rescale=False):
        """
        Writes a dicom single file image using template file, without the intensity transformation from template dataset
        :param img_arr: numpy array of the image to be saved, should be in the same orientation as template_filename
        :param template_filename: the single dicom scan whose meta data is used
        """
        ds = pydicom.dcmread(template_filename)
        ds = convert_ds(ds)
        if not keep_rescale:
            if isinstance(ds, FramedFileDataset):
                ds.del_intensity_trans()
            else:
                del ds.RescaleSlope
                del ds.RescaleIntercept
        ds.PixelData = img_arr.astype('int16').tobytes()
        ds.save_as(output_filename)
