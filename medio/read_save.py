from pathlib import Path
from medio.backends.nib_io import NibIO
from medio.backends.itk_io import ItkIO
from medio.backends.pdcm_io import PdcmIO
from medio.metadata.convert_nib_itk import inv_axcodes
from medio.utils.files import is_nifti


def read_img(input_path, desired_ornt=None, backend=None, dtype=None, **kwargs):
    """
    Read medical image with nibabel or itk
    :param input_path: str or os.PathLike, the input path of image file or a directory containing dicom series
    :param desired_ornt: optional parameter for reorienting the image to desired orientation, e.g. 'RAS'
    The desired_ornt string is in itk standard (if NibIO is used, the orientation is converted accordingly)
    :param backend: optional parameter for setting the reader backend: 'itk', 'nib', 'pdcm' (also 'pydicom') or None
    :param dtype: equivalent to np_image.astype(dtype) if dtype is not None
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
                raise NotImplementedError('Pydicom reader backend does not yet support reorientation. The passed '
                                          'desired orientation must be None (default).')
            reader = pdcm_reader
        else:
            raise ValueError('The backend argument must be one of: \'itk\', \'nib\', \'pdcm\' (or \'pydicom\'), None')

    if reader == nib_reader:
        desired_ornt = inv_axcodes(desired_ornt)

    if reader is pdcm_reader:
        np_image, metadata = reader(input_path, **kwargs)
    else:
        np_image, metadata = reader(input_path, desired_axcodes=desired_ornt, **kwargs)

    if dtype is not None:
        np_image = np_image.astype(dtype)
    return np_image, metadata


def save_img(filename, np_image, metadata, use_original_ornt=True, backend=None, dtype=None, mkdir=False, parents=False,
             **kwargs):
    """
    Save numpy image with corresponding metadata to file
    :param filename: str or os.PathLike, the output filename
    :param np_image: the numpy image
    :param metadata: the metadata of the image
    :param use_original_ornt: whether to save in the original orientation stored in metadata.orig_ornt or not
    :param backend: optional - 'itk', 'nib' or None
    :param dtype: equivalent to np_image.astype(dtype) if dtype is not None
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
    if mkdir:
        Path(filename).parent.mkdir(parents=parents, exist_ok=True)
    if dtype is not None:
        np_image = np_image.astype(dtype)
    writer(filename, np_image, metadata, use_original_ornt, **kwargs)


def save_dir(dirname, np_image, metadata, use_original_ornt=True, dtype=None, **kwargs):
    """Save image as a dicom directory
    :param dtype: equivalent to image_np.astype(dtype) in the packing to itk image
    """
    if dtype is not None:
        np_image = np_image.astype(dtype)
    ItkIO.save_dcm_dir(dirname, np_image, metadata, use_original_ornt, **kwargs)
