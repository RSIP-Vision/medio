import pydicom
from pydicom.tag import Tag
from dicom_numpy import combine_slices
from pathlib import Path
from medio.backends.unpack_ds import unpack_dataset
from medio.metadata.pdcm_ds import FramedFileDataset


class PdcmIO:
    """
    Handle dicom files writing based on a template dicom file
    """
    # if ds.NumberOfFrames > 1:
    # Single dicom file tags
    t_shrd_func = Tag((0x5200, 0x9229))  # Shared Functional Groups Sequence

    t_plane_orient = Tag((0x0020, 0x9116))  # Plane Orientation Sequence
    t_image_orient = Tag((0x0020, 0x0037))  # ds[t_shrd_func][0][t_plane_orient][0].ImageOrientationPatient
    # ds.SharedFunctionalGroupsSequence[0].PlaneOrientationSequence[0].ImageOrientationPatient

    t_pixel_meas = Tag((0x0028, 0x9110))
    t_pixel_spacing = Tag((0x0028, 0x0030))  # ds[t_shrd_func][0][t_plane_orient][0].PixelSpacing
    t_slice_thickness = Tag((0x0018, 0x0050))  # ds[t_shrd_func][0][t_plane_orient][0].SliceThickness

    t_pixel_trans = Tag((0x0028, 0x9145))  # Pixel Value Transformation Sequence
    t_rescale_inter = Tag((0x0028, 0x1052))  # Rescale Intercept, ds[t_shrd_func][0][t_trans][0].RescaleIntercept
    t_rescale_slope = Tag((0x0028, 0x1053))  # Rescale Slope, ds[t_shrd_func][0][t_trans][0].RescaleSlope
    # ds.SharedFunctionalGroupsSequence[0].PixelValueTransformationSequence[0].RescaleIntercept

    # TODO
    t_per_frame = Tag((0x5200, 0x9230))  # Per-frame Functional Groups Sequence
    t_plane_position = Tag((0x0020, 0x9113))  # Plane Position Sequence
    t_image_position = Tag((0x0020, 0x0032))  # ds[t_shrd_func][0][t_plane_position][0].ImageOrientationPatient
    # ds.PerFrameFunctionalGroupsSequence[0].PlanePositionSequence[0].ImagePositionPatient

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
        return img, affine

    @staticmethod
    def read_dcm_file(filename):
        """Read a single dicom file"""
        ds = pydicom.dcmread(filename)
        # Multi-frame file dataset
        if ds.NumberOfFrames > 1:
            ds.__class__ = FramedFileDataset
        img, affine = unpack_dataset(ds)
        return img, affine

    @staticmethod
    def read_img(input_path, globber='*'):
        input_path = Path(input_path)
        if input_path.is_file():
            return PdcmIO.read_dcm_file(str(input_path))
        elif input_path.is_dir():
            return PdcmIO.read_dcm_dir(str(input_path), globber)
        else:
            raise IOError('Invalid input path')

    @staticmethod
    def save_arr2dcm_file(output_filename, img_arr, template_filename, keep_rescale=False):
        """
        Writes a dicom single file image using template file, without the intensity transformation from template dataset
        :param img_arr: numpy array of the image to be saved, should be in the same orientation as template_filename
        :param template_filename: the single dicom scan whose meta data is used
        """
        ds = pydicom.dcmread(template_filename)
        if not keep_rescale:
            PdcmIO.del_intensity_rescale(ds)
        ds.PixelData = img_arr.astype('int16').tobytes()
        ds.save_as(output_filename)

    @staticmethod
    def del_intensity_rescale(ds):
        """Delete pixel value transformation sequence tag from dataset"""
        if PdcmIO.t_shrd_func in ds and PdcmIO.t_trans in ds[PdcmIO.t_shrd_func][0]:
            del ds[PdcmIO.t_shrd_func][0][PdcmIO.t_trans]

    @staticmethod
    def ds_img(ds):
        """Return the rescaled pixel_array of ds"""
        img = ds.pixel_array.astype('int16')
        m = ds.RescaleSlope
        b = ds.RescaleIntercept
        img = m * img + b
        return img
