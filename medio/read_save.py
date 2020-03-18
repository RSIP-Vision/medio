from pathlib import Path
from medio.backends.nib_io import NibIO
from medio.backends.itk_io import ItkIO
from medio.metadata.convert_nib_itk import inv_axcodes


def is_nifti(filename, check_exist=True):
    suffixes = ['.nii.gz', '.nii']
    if check_exist and not Path(filename).is_file():
        return False
    for suf in suffixes:
        if str(filename).endswith(suf):
            return True
    return False


def read_img(input_path, desired_ornt=None, backend=None):
    """
    Read medical image with nibabel or itk
    :param input_path: str or os.PathLike, the input path of image file or a directory containing dicom series
    :param desired_ornt: optional parameter for reorienting the image to desired orientation, e.g. 'RAS'
    The desired_ornt string is in itk standard (if NibIO is used, the orientation is converted accordingly)
    :param backend: optional parameter for setting the reader backend, 'itk' or 'nib'
    :return: numpy image and metadata object
    """
    nib_reader = NibIO.read_img
    itk_reader = ItkIO.read_img
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
        else:
            raise ValueError('The backend argument must be one of: \'itk\', \'nib\', None')

    if reader == nib_reader:
        desired_ornt = inv_axcodes(desired_ornt)

    np_image, metadata = reader(input_path, desired_axcodes=desired_ornt)
    return np_image, metadata


def save_img(filename, np_image, metadata, use_original_ornt=True, dicom_template_file=None, backend=None):
    """
    Save numpy image with corresponding metadata to file
    :param filename: str or os.PathLike, the output filename
    :param np_image: the numpy image
    :param metadata: the metadata of the image
    :param use_original_ornt: whether to save in the original orientation stored in metadata.orig_ornt or not
    :param dicom_template_file: for saving single dicom file with pydicom
    :param backend: optional, 'itk' or 'nib'
    """
    nib_writer = NibIO.save_img
    itk_writer = ItkIO.save_img
    if dicom_template_file is None:
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

        writer(filename, np_image, metadata, use_original_ornt)
    else:
        itk_writer(filename, np_image, metadata, use_original_ornt, dicom_template_file)
