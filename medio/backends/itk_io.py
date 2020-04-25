from pathlib import Path
from typing import Union
from uuid import uuid1

import itk
import numpy as np

from medio.metadata.affine import Affine
from medio.metadata.itk_orientation import itk_orientation_code, codes_str_dict
from medio.metadata.metadata import MetaData, check_dcm_ornt
from medio.utils.files import is_dicom, make_empty_dir


class ItkIO:
    coord_sys = 'itk'
    # default image type:
    dimension = 3
    pixel_type = itk.ctype('short')  # signed short - int16
    image_type = itk.Image[pixel_type, dimension]

    @staticmethod
    def read_img(input_path, desired_axcodes=None, pixel_type=pixel_type, fallback_only=False, dimension=dimension):
        """
        The main reader function, reads images and performs reorientation and unpacking
        :param input_path: path of image file or directory containing dicom series
        :param desired_axcodes: string or tuple - e.g. 'LPI', ('R', 'A', 'S')
        :param pixel_type: preferred itk pixel type for image files or dicom folders
        :param fallback_only: used in itk.imread, relevant to files only. If True, finds the pixel_type automatically
        and uses pixel_type only if failed
        :param dimension: relevant to folders only. The dimension of the image to be read
        :return: numpy image and metadata object which includes pixdim, affine, original orientation string and
        coordinates system
        """
        input_path = Path(input_path)
        if input_path.is_dir():
            img = ItkIO.read_dcm_dir(str(input_path), image_type=itk.Image[pixel_type, dimension])
        elif input_path.is_file():
            img = ItkIO.read_img_file(str(input_path), pixel_type=pixel_type, fallback_only=fallback_only)
        else:
            raise FileNotFoundError(f'No such file or directory: \'{input_path}\'')
        img, original_ornt_code = ItkIO.reorient(img, desired_axcodes)
        image_np, affine = ItkIO.unpack_img(img)
        ornt_str = codes_str_dict[original_ornt_code]
        metadata = MetaData(affine=affine, orig_ornt=ornt_str, coord_sys=ItkIO.coord_sys)
        return image_np, metadata

    @staticmethod
    def save_img(filename, image_np, metadata, use_original_ornt=True, is_vector=False, allow_dcm_reorient=False,
                 compression=False):
        """
        Save an image file with itk
        :param filename: the filename to save, str or os.PathLike
        :param image_np: the image's numpy array
        :param metadata: the corresponding metadata
        :param use_original_ornt: whether to save in the original orientation or not
        :param is_vector: is the image a vector type, for example RGB. If it is - the channels are the first dimension
        :param allow_dcm_reorient: whether to allow automatic reorientation to a right handed orientation or not
        :param compression: use compression or not
        """
        is_dcm = is_dicom(filename, check_exist=False)
        if is_dcm:
            image_np = ItkIO.prepare_dcm_array(image_np, is_vector=is_vector)
        image = ItkIO.prepare_image(image_np, metadata, use_original_ornt, is_vector=is_vector, is_dcm=is_dcm,
                                    allow_dcm_reorient=allow_dcm_reorient)
        ItkIO.save_img_file(image, str(filename), compression=compression)

    @staticmethod
    def prepare_image(image_np, metadata, use_original_ornt, is_vector=False, is_dcm=False, allow_dcm_reorient=False):
        """Prepare image for saving"""
        metadata.convert(ItkIO.coord_sys)
        desired_ornt = metadata.orig_ornt if use_original_ornt else None
        if is_dcm:
            # checking right-handed orientation before saving a dicom file/series
            desired_ornt = check_dcm_ornt(desired_ornt, metadata, allow_dcm_reorient=allow_dcm_reorient)
        image = ItkIO.pack2img(image_np, metadata.affine, is_vector)
        image, _ = ItkIO.reorient(image, desired_ornt)
        return image

    @staticmethod
    def prepare_dcm_array(image_np, is_vector=False):
        """Change image_np to correct data type for saving a single dicom file"""
        if is_vector:
            dcm_dtypes = [np.uint8]
        else:
            # for 3d image the supported data types are:
            dcm_dtypes = [np.uint8, np.uint16]
            # if the image is 2d it can be signed
            image_np_sq = np.squeeze(image_np)
            if image_np_sq.ndim == 2:
                image_np = image_np_sq[..., np.newaxis]
                dcm_dtypes = [np.int16] + dcm_dtypes

        if image_np.dtype in dcm_dtypes:
            return image_np

        for dtype in dcm_dtypes:
            arr = image_np.astype(dtype)
            if np.array_equal(arr, image_np):
                return arr

        raise NotImplementedError('Saving a single dicom file with ItkIO is currently supported only for \n'
                                  '1. 2d images - int16, uint16, uint8\n'
                                  '2. 3d images with integer nonnegative values - uint8, uint16\n'
                                  '3. 2d/3d RGB images - uint8 (with is_vector=True)\n'
                                  'For negative values, try to save a dicom directory or use PdcmIO.save_arr2dcm_file')

    @staticmethod
    def read_img_file(filename, pixel_type=pixel_type, fallback_only=False):
        """Common pixel types: itk.SS (int16), itk.US (uint16), itk.UC (uint8)"""
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
        """Swap the axes to the usual x, y, z convention in RAI orientation (originally z, y, x)"""
        img_array = itk.array_from_image(img_itk).copy().T  # the transpose here is equivalent to keep_axes=True
        return img_array

    @staticmethod
    def array_to_itk_img(img_array, is_vector=False):
        """Set is_vector to True for vector images, e.g. RGB"""
        img_itk = itk.image_from_array(img_array.T.copy(), is_vector=is_vector)  # copy is crucial for the ordering
        return img_itk

    @staticmethod
    def unpack_img(img):
        image_np = ItkIO.itk_img_to_array(img)
        # metadata
        direction = itk.array_from_vnl_matrix(img.GetDirection().GetVnlMatrix().as_matrix())
        spacing = itk.array_from_vnl_vector(img.GetSpacing().GetVnlVector())
        origin = itk.array_from_vnl_vector(img.GetOrigin().GetVnlVector())
        affine = Affine(direction=direction, spacing=spacing, origin=origin)
        return image_np, affine

    @staticmethod
    def pack2img(image_np, affine, is_vector=False):
        image = ItkIO.array_to_itk_img(image_np, is_vector)
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

    @staticmethod
    def read_dcm_dir(dirname, image_type=image_type):
        """
        Read a dicom directory. If there is more than one series in the directory an error is raised
        Shorter option for a single series (provided the slices order is known):
        >>> itk.imread([filename0, filename1, ...])
        """
        names_generator = itk.GDCMSeriesFileNames.New()
        names_generator.SetUseSeriesDetails(True)
        names_generator.AddSeriesRestriction('0008|0021')
        names_generator.SetGlobalWarningDisplay(False)
        names_generator.SetDirectory(dirname)

        series_uid = names_generator.GetSeriesUIDs()

        if len(series_uid) == 0:
            raise FileNotFoundError(f'No DICOMs in: \'{dirname}\'')
        if len(series_uid) > 1:
            raise OSError(f'The directory: \'{dirname}\'\ncontains more than one DICOM series')

        series_identifier = series_uid[0]
        filenames = names_generator.GetFileNames(series_identifier)
        reader = itk.ImageSeriesReader[image_type].New()
        dicom_io = itk.GDCMImageIO.New()
        reader.SetImageIO(dicom_io)
        reader.SetFileNames(filenames)
        reader.ForceOrthogonalDirectionOff()
        reader.Update()
        itk_img = reader.GetOutput()
        return itk_img

    @staticmethod
    def save_dcm_dir(dirname, image_np, metadata, use_original_ornt=True, parents=False, allow_dcm_reorient=False,
                     **kwargs):
        """
        Save a 3d numpy array image_np as a dicom series of 2d dicom slices in the directory dirname
        :param dirname: the directory to save in the files, str or os.PathLike. If exists - must be empty
        :param image_np: the image's numpy array
        :param metadata: the corresponding metadata
        :param use_original_ornt: whether to save in the original orientation or not
        :param allow_dcm_reorient: whether to allow automatic reorientation to a right handed orientation or not
        :param kwargs: optional kwargs passed to ItkIO.dcm_metadata: pattern, metadata_dict
        """
        image = ItkIO.prepare_image(image_np, metadata, use_original_ornt, is_dcm=True,
                                    allow_dcm_reorient=allow_dcm_reorient)
        image_type = type(image)
        _, (pixel_type, _) = itk.template(image)
        image2d_type = itk.Image[pixel_type, 2]
        writer = itk.ImageSeriesWriter[image_type, image2d_type].New()
        make_empty_dir(dirname, parents)
        # Generate necessary metadata and filenames per slice:
        mdict_list, filenames = ItkIO.dcm_series_metadata(image, dirname, **kwargs)
        metadict_vec = itk.vector[itk.MetaDataDictionary](mdict_list)
        writer.SetMetaDataDictionaryArray(metadict_vec)
        writer.SetFileNames(filenames)
        dicom_io = itk.GDCMImageIO.New()
        dicom_io.KeepOriginalUIDOn()
        writer.SetImageIO(dicom_io)
        writer.SetInput(image)
        writer.Update()

    @staticmethod
    def dcm_series_metadata(image, dirname, pattern='IM{}.dcm', metadata_dict=None):
        """
        Return dicom series metadata per slice and filenames
        :param image: the full itk image to be saved as dicom series
        :param dirname: the directory name
        :param pattern: pattern for the filenames, including a placeholder ('{}') for the slice number
        :param metadata_dict: dictionary of metadata for adding tags or overriding the default values. For example,
        metadata_dict = {'0008|0060': 'US'} will override the default 'CT' modality and set it to 'US' (ultrasound)
        :return: metadata dictionaries per slice, slice filenames
        """
        # The number of slices
        n = image.GetLargestPossibleRegion().GetSize().GetElement(2)

        # Shared properties for all the n slices:
        mdict = itk.MetaDataDictionary()

        # Series Instance UID
        mdict['0020|000e'] = str(uuid1())
        # Study Instance UID
        mdict['0020|000d'] = str(uuid1())

        # Pixel Spacing - TODO: maybe not necessary? automatically saved
        spacing = image.GetSpacing()
        mdict['0028|0030'] = f'{spacing[0]}\\{spacing[1]}'
        # Slice Thickness
        mdict['0018|0050'] = str(spacing[2])
        # Spacing Between Slices
        mdict['0018|0088'] = str(spacing[2])
        # Image Orientation (Patient)
        orientation_str = '\\'.join([str(image.GetDirection().GetVnlMatrix().get(i, j))
                                     for j in range(2) for i in range(3)])
        mdict['0020|0037'] = orientation_str

        # Number of Frames
        mdict['0028|0008'] = '1'
        # Number of Slices
        mdict['0054|0081'] = str(n)
        # Modality
        mdict['0008|0060'] = 'CT'

        if metadata_dict is not None:
            for key, val in metadata_dict.items():
                mdict[key] = val

        # Per slice properties:
        mdict_list = []
        filenames = []

        for i in range(n):
            # copy the shared properties dict:
            mdict_i = itk.MetaDataDictionary(mdict)
            # Instance Number
            mdict_i['0020|0013'] = str(i + 1)
            # Image Position (Patient)
            position = image.TransformIndexToPhysicalPoint([0, 0, i])
            position_str = '\\'.join([str(position[i]) for i in range(3)])
            mdict_i['0020|0032'] = position_str

            mdict_list += [mdict_i]
            filenames += [str(Path(dirname) / pattern.format(i + 1))]

        return mdict_list, filenames
