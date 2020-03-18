import pydicom
from pydicom.tag import Tag
from dicom_numpy import combine_slices
from pathlib import Path


# class Single

class PdcmIO:
    """
    Handle dicom files writing based on a template dicom file
    """
    # Single dicom file tags
    t_shrd_func = Tag((0x5200, 0x9229))  # Shared Functional Groups Sequence

    t_trans = Tag((0x0028, 0x9145))  # Pixel Value Transformation Sequence
    t_inter = Tag((0x0028, 0x1052))  # Rescale Intercept
    t_slope = Tag((0x0028, 0x1053))  # Rescale Slope

    t_plane_orient = Tag((0x0020, 0x9116))
    t_image_orient = Tag((0x0020, 0x0037))

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
        if PdcmIO.t_shrd_func in ds and PdcmIO.t_trans in ds[PdcmIO.t_shrd_func][0]:
            trans = ds[PdcmIO.t_shrd_func][0][PdcmIO.t_trans][0]
            if (PdcmIO.t_inter in trans) and (PdcmIO.t_slope in trans):
                m = trans[PdcmIO.t_slope].value
                b = trans[PdcmIO.t_inter].value
                img = m * img + b
        return img

    # methods for dicom directory
    @staticmethod
    def read_dcm_dir(input_dir, globber='*'):
        """Reads a 3D dicom image: input path can be a file or directory (DICOM series)"""
        # find all dicom files within the specified folder, read every file separately sort them by InstanceNumber
        files = list(Path(input_dir).glob(globber))
        slices = [pydicom.dcmread(str(filename)) for filename in files]
        # slices.sort(key=lambda x: int(x.InstanceNumber))
        # get pixdim based on one dcm file:
        ds0 = slices[0]
        pixdim = (float(ds0.PixelSpacing[0]), float(ds0.PixelSpacing[1]), float(ds0.SliceThickness))
        img, affine = combine_slices(slices)
        return img, pixdim, affine
