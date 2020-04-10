from warnings import warn
from medio.backends.nib_io import NibIO
from medio.backends.itk_io import ItkIO
from medio.backends.pdcm_io import PdcmIO
from medio.metadata.convert_nib_itk import inv_axcodes
from medio.utils.files import is_nifti


def read_img(input_path, desired_ornt=None, backend=None, **kwargs):
    """
    Read medical image with nibabel or itk
    :param input_path: str or os.PathLike, the input path of image file or a directory containing dicom series
    :param desired_ornt: optional parameter for reorienting the image to desired orientation, e.g. 'RAS'
    The desired_ornt string is in itk standard (if NibIO is used, the orientation is converted accordingly)
    :param backend: optional parameter for setting the reader backend: 'itk', 'nib', 'pdcm' (also 'pydicom') or None
    :return: numpy image and metadata object
    """
    nib_reader = NibIO.read_img
    itk_reader = ItkIO.read_img
    pdcm_reader = PdcmIO.read_img
    if backend is None:
        if is_nifti(input_path):
            reader = nib_reader
        else:
            reader = itk_reader
    else:
        if backend == 'nib':
            reader = nib_reader
        elif backend == 'itk':
            reader = itk_reader
        elif backend in ('pdcm', 'pydicom'):
            if desired_ornt is not None:
                warn(f'Pydicom reader backend does not support reorientation. The passed desired orientation '
                     f'{desired_ornt} will be ignored')
            np_image, metadata = pdcm_reader(input_path, **kwargs)
            return np_image, metadata
        else:
            raise ValueError('The backend argument must be one of: \'itk\', \'nib\', \'pdcm\' (or \'pydicom\'), None')

    if reader == nib_reader:
        desired_ornt = inv_axcodes(desired_ornt)

    np_image, metadata = reader(input_path, desired_axcodes=desired_ornt, **kwargs)
    return np_image, metadata


def save_img(filename, np_image, metadata, use_original_ornt=True, backend=None, **kwargs):
    """
    Save numpy image with corresponding metadata to file
    :param filename: str or os.PathLike, the output filename
    :param np_image: the numpy image
    :param metadata: the metadata of the image
    :param use_original_ornt: whether to save in the original orientation stored in metadata.orig_ornt or not
    :param backend: optional - 'itk', 'nib' or None
    """
    nib_writer = NibIO.save_img
    itk_writer = ItkIO.save_img
    if backend is None:
        if is_nifti(filename, check_exist=False):
            writer = nib_writer
        else:
            writer = itk_writer
    else:
        if backend == 'nib':
            writer = nib_writer
        elif backend == 'itk':
            writer = itk_writer
        else:
            raise ValueError('The backend argument must be one of: \'itk\', \'nib\', None')

    writer(filename, np_image, metadata, use_original_ornt, **kwargs)


def save_dir(dirname, np_image, metadata, use_original_ornt=True):
    """Save image as a dicom directory"""
    ItkIO.save_dcm_dir(dirname, np_image, metadata, use_original_ornt)
