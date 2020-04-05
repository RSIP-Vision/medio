import itk
import numpy as np
from pathlib import Path
from typing import Union
from medio.metadata.affine import Affine
from medio.metadata.metadata import MetaData
from medio.metadata.itk_orientation import itk_orientation_code, codes_str_dict


class ItkIO:
    dimension = 3
    pixel_type = itk.ctype('short')  # signed short - int16
    image_type = itk.Image[pixel_type, dimension]
    coord_sys = 'itk'

    @staticmethod
    def read_img(input_path, desired_axcodes=None, image_type=image_type, dtype='int16'):
        """
        The main reader function, reads images and performs reorientation and unpacking
        :param input_path: path of image file or directory containing dicom series
        :param desired_axcodes: string or tuple - e.g. 'LPI', ('R', 'A', 'S')
        :param image_type: preferred itk image type for dicom folders
        :param dtype: the dtype of the returned numpy array
        :return: numpy image and metadata object which includes pixdim, affine, original orientation string and
        coordinates system
        """
        input_path = Path(input_path)
        if input_path.is_file():
            img = ItkIO.read_img_file(str(input_path))
        elif input_path.is_dir():
            img = ItkIO.read_dcm_dir(str(input_path), image_type=image_type)
        else:
            raise IOError('Invalid input path')
        img, original_ornt_code = ItkIO.reorient(img, desired_axcodes)
        image_np, affine = ItkIO.unpack_img(img, dtype)
        ornt_str = codes_str_dict[original_ornt_code]
        metadata = MetaData(affine=affine, orig_ornt=ornt_str, coord_sys=ItkIO.coord_sys)
        return image_np, metadata

    @staticmethod
    def save_img(filename, image_np, metadata, use_original_ornt=True, dtype='int16'):
        if ItkIO.is_dcm_file(filename):
            image_np, dtype = ItkIO.prepare_dcm_image(image_np)
        image = ItkIO.prepare_image(image_np, metadata, use_original_ornt, dtype)
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        ItkIO.save_img_file(image, filename)

    @staticmethod
    def prepare_image(image_np, metadata, use_original_ornt, dtype):
        """Prepare image for saving"""
        metadata.convert(ItkIO.coord_sys)
        image = ItkIO.pack2img(image_np, metadata.affine, dtype)
        if use_original_ornt:
            image, _ = ItkIO.reorient(image, metadata.orig_ornt)
        return image

    @staticmethod
    def prepare_dcm_image(image_np):
        """Change image_np to correct data type for saving a single dicom file"""
        # if the image is 2d it can be signed
        image_np_sq = np.squeeze(image_np)
        if image_np_sq.ndim == 2:
            image_np = image_np_sq[..., np.newaxis]
            return image_np, image_np.dtype

        # if it is 3d, the supported data types are:
        dcm_dtypes = [np.uint8, np.uint16]

        if image_np.dtype in dcm_dtypes:
            return image_np, image_np.dtype

        for dtype in dcm_dtypes:
            arr = image_np.astype(dtype)
            if np.array_equal(arr, image_np):
                return arr, dtype

        # TODO: may be solved with rescale and intercept tags in dicom
        raise NotImplementedError('Saving single dicom files with ItkIO is currently supported only for \n'
                                  '1. 2d images, or \n'
                                  '2. 3d images with integer nonnegative values (np.uint8, np.uint16)\n'
                                  'Try to save a dicom directory or use PdcmIO.save_arr2dcm_file')

    @staticmethod
    def is_dcm_file(filename, check_exist=False):
        if check_exist and not Path(filename).is_file():
            return False
        return filename.endswith('.dcm') or filename.endswith('.dicom')

    @staticmethod
    def read_img_file(filename, pixel_type=pixel_type, fallback_only=True):
        image = itk.imread(filename, pixel_type, fallback_only=fallback_only)
        return image

    @staticmethod
    def read_img_file_long(filename, image_type=image_type):
        """Longer version of read_img_file which returns the itk image and io engine string"""
        reader = itk.ImageFileReader[image_type].New()
        reader.SetFileName(filename)
        reader.Update()
        image_io = str(reader.GetImageIO()).split(' ')[0]
        image = reader.GetOutput()
        return image, image_io

    @staticmethod
    def save_img_file(image, filename, compression=False):
        itk.imwrite(image, filename, compression=compression)

    @staticmethod
    def save_img_file_long(image, filename, compression=False):
        image_type = type(image)
        writer = itk.ImageFileWriter[image_type].New()
        if compression:
            writer.UseCompressionOn()
        writer.UseInputMetaDataDictionaryOn()
        writer.SetFileName(filename)
        writer.SetInput(image)
        writer.Update()

    @staticmethod
    def itk_img_to_array(img_itk):
        """Swap the axes to make the third axis the z axis (inferior - superior) in RAS orientation"""
        img_array = itk.array_from_image(img_itk).copy().T
        return img_array

    @staticmethod
    def array_to_itk_img(img_array):
        img_itk = itk.image_from_array(img_array.T.copy())
        return img_itk

    @staticmethod
    def unpack_img(img, dtype='int16'):
        image_np = ItkIO.itk_img_to_array(img).astype(dtype)
        # metadata
        direction = itk.array_from_vnl_matrix(img.GetDirection().GetVnlMatrix().as_matrix())
        spacing = itk.array_from_vnl_vector(img.GetSpacing().GetVnlVector())
        origin = itk.array_from_vnl_vector(img.GetOrigin().GetVnlVector())
        affine = Affine(direction=direction, spacing=spacing, origin=origin)
        return image_np, affine

    @staticmethod
    def pack2img(image_np, affine, dtype='int16'):
        image = ItkIO.array_to_itk_img(image_np.astype(dtype))
        direction_arr, spacing, origin = affine.direction, affine.spacing, affine.origin

        # setting metadata
        spacing_vec = itk.Vector[itk.D, ItkIO.dimension]()
        spacing_vec.SetVnlVector(itk.vnl_vector_from_array(spacing.astype('float')))
        image.SetSpacing(spacing_vec)

        image.SetOrigin(origin.astype('float'))

        direction_mat = itk.vnl_matrix_from_array(direction_arr.astype('float'))
        direction = itk.Matrix[itk.D, ItkIO.dimension, ItkIO.dimension](direction_mat)
        image.SetDirection(direction)

        return image

    @staticmethod
    def read_dcm_dir(dirname, image_type=image_type):
        """
        Read a dicom directory. If there is more than one series in the directory an error is raised
        Shorter option for a single series (provided the slices order is known):
        >>> itk.imread([filename0, filename1, ...])
        """
        names_generator = itk.GDCMSeriesFileNames.New()
        names_generator.SetUseSeriesDetails(True)
        names_generator.AddSeriesRestriction("0008|0021")
        names_generator.SetGlobalWarningDisplay(False)
        names_generator.SetDirectory(dirname)

        series_uid = names_generator.GetSeriesUIDs()

        if len(series_uid) == 0:
            raise IOError('No DICOMs in: ' + dirname)
        if len(series_uid) > 1:
            raise IOError('The directory: ' + dirname + '\ncontains more than one DICOM file')

        series_identifier = series_uid[0]
        filenames = names_generator.GetFileNames(series_identifier)
        reader = itk.ImageSeriesReader[image_type].New()
        dicom_io = itk.GDCMImageIO.New()
        reader.SetImageIO(dicom_io)  # TODO: is this necessary?
        reader.SetFileNames(filenames)
        reader.ForceOrthogonalDirectionOff()  # TODO: why?
        reader.Update()
        itk_img = reader.GetOutput()
        return itk_img

    @staticmethod
    def reorient(img, desired_orientation: Union[int, tuple, str, None]):
        if desired_orientation is None:
            return img, None

        image_type = type(img)
        orient = itk.OrientImageFilter[image_type, image_type].New()
        orient.UseImageDirectionOn()
        orient.SetInput(img)
        if isinstance(desired_orientation, (str, tuple)):
            desired_orientation = itk_orientation_code(desired_orientation)
        orient.SetDesiredCoordinateOrientation(desired_orientation)
        orient.Update()
        reoriented_itk_img = orient.GetOutput()
        original_orientation_code = orient.GetGivenCoordinateOrientation()
        return reoriented_itk_img, original_orientation_code
