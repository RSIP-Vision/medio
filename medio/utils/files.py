from pathlib import Path


def is_file_suffix(filename, *suffixes, check_exist=True):
    if check_exist and not Path(filename).is_file():
        return False
    for suf in suffixes:
        if str(filename).endswith(suf):
            return True
    return False


def is_nifti(filename, check_exist=True):
    return is_file_suffix(filename, '.nii.gz', '.nii', check_exist=check_exist)


def is_dicom(filename, check_exist=True):
    return is_file_suffix(filename, '.dcm', '.dicom', check_exist=check_exist)


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
            raise FileExistsError(f'The directory \'{dir_path}\' is not empty')
