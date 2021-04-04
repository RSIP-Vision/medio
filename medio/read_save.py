from pathlib import Path

from medio.backends.itk_io import ItkIO
from medio.backends.nib_io import NibIO
from medio.backends.pdcm_io import PdcmIO
from medio.metadata.convert_nib_itk import inv_axcodes
from medio.utils.files import is_nifti


def read_img(input_path, desired_ornt=None, backend=None, dtype=None, header=False, channels_axis=-1,
             coord_sys='itk', **kwargs):
    """
    Read medical image with nibabel or itk
    :param input_path: str or os.PathLike, the input path of image file or a directory containing dicom series
    :param desired_ornt: optional parameter for reorienting the image to a desired orientation, e.g. 'RAS'.
    The desired_ornt string is in the convention of `coord_sys` argument (itk by default).
    :param backend: optional parameter for setting the reader backend: 'itk', 'nib', 'pdcm' (also 'pydicom') or None
    :param dtype: equivalent to np_image.astype(dtype) if dtype is not None
    :param header: if True, the returned metadata will include a header attribute with additional metadata dictionary as
    read by the backend. Note: currently, this is supported for files only
    :param channels_axis: if not None and the image is channeled (e.g. RGB) move the channels to channels_axis in the
    returned image array
    :param coord_sys: the coordinate system (or convention) of the `desired_ornt` parameter and the returned metadata.
    It can be 'itk', 'nib' or None, and is 'itk' by default.
    None means that the backend will determine coord_sys, but it can lead to a backend-dependent array and metadata
    :return: numpy image and metadata object
    """
    nib_reader_data = (NibIO.read_img, NibIO.coord_sys)
    itk_reader_data = (ItkIO.read_img, ItkIO.coord_sys)
    pdcm_reader_data = (PdcmIO.read_img, PdcmIO.coord_sys)
    if backend is None:
        if is_nifti(input_path):
            reader, reader_sys = nib_reader_data
        else:
            reader, reader_sys = itk_reader_data
    else:
        if backend == 'nib':
            reader, reader_sys = nib_reader_data
        elif backend == 'itk':
            reader, reader_sys = itk_reader_data
        elif backend in ('pdcm', 'pydicom'):
            reader, reader_sys = pdcm_reader_data
        else:
            raise ValueError('The backend argument must be one of: "itk", "nib", "pdcm" (or "pydicom"), None')

    if (coord_sys is not None) and (coord_sys != reader_sys):
        desired_ornt = inv_axcodes(desired_ornt)

    np_image, metadata = reader(input_path, desired_ornt, header, channels_axis, **kwargs)

    if dtype is not None:
        np_image = np_image.astype(dtype, copy=False)
    if coord_sys is not None:
        metadata.convert(coord_sys)
    return np_image, metadata


def save_img(filename, np_image, metadata, use_original_ornt=True, backend=None, dtype=None, channels_axis=None,
             mkdir=False, parents=False, **kwargs):
    """
    Save numpy image with corresponding metadata to file
    :param filename: str or os.PathLike, the output filename
    :param np_image: the numpy image
    :param metadata: the metadata of the image
    :param use_original_ornt: whether to save in the original orientation stored in metadata.orig_ornt or not
    :param backend: optional - 'itk', 'nib' or None
    :param dtype: equivalent to np_image.astype(dtype) if dtype is not None
    :param channels_axis: if not None - the image is channeled (e.g. RGB) and the channels are in channels_axis
    :param mkdir: if True, creates the directory of `filename`
    :param parents: to be used with `mkdir=True`. If True, creates also the parent directories
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
            raise ValueError('The backend argument must be one of: "itk", "nib", None')
    if mkdir:
        Path(filename).parent.mkdir(parents=parents, exist_ok=True)
    if dtype is not None:
        np_image = np_image.astype(dtype, copy=False)
    writer(filename, np_image, metadata, use_original_ornt, channels_axis, **kwargs)


def save_dir(dirname, np_image, metadata, use_original_ornt=True, dtype=None, channels_axis=None, parents=False,
             exist_ok=False, allow_dcm_reorient=False, **kwargs):
    """
    Save image as a dicom directory. See medio.backends.itk_io.ItkIO.save_dcm_dir documentation.
    dtype is equivalent to passing image_np.astype(dtype) if dtype is not None
    """
    if dtype is not None:
        np_image = np_image.astype(dtype, copy=False)
    ItkIO.save_dcm_dir(dirname, np_image, metadata, use_original_ornt, channels_axis, parents, exist_ok,
                       allow_dcm_reorient, **kwargs)
