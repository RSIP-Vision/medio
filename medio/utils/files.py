from pathlib import Path


def is_file_suffix(filename, suffixes, check_exist=True):
    """
    is_file + check for suffix
    :param filename: pathlike object
    :param suffixes: tuple of possible suffixes
    :param check_exist: whether to check the file's existence
    :return: bool
    """
    if check_exist and not Path(filename).is_file():
        return False
    return str(filename).endswith(suffixes)


def is_nifti(filename, check_exist=True):
    return is_file_suffix(filename, ('.nii.gz', '.nii', '.img.gz', '.img', '.hdr'), check_exist=check_exist)


def is_dicom(filename, check_exist=True):
    return is_file_suffix(filename, ('.dcm', '.dicom', '.DCM', '.DICOM'), check_exist=check_exist)


def make_empty_dir(dir_path, parents=False):
    """Make an empty directory. If it exists - check that it is empty"""
    dir_path = Path(dir_path)
    try:
        dir_path.mkdir(parents=parents, exist_ok=False)
    except FileExistsError:
        # the directory exists
        try:
            next(dir_path.glob('*'))
        except StopIteration:
            pass  # the directory exists but empty - ok
        else:
            raise FileExistsError(f'The directory "{dir_path}" is not empty')
