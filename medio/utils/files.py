from pathlib import Path


def is_nifti(filename, check_exist=True):
    suffixes = ['.nii.gz', '.nii']
    if check_exist and not Path(filename).is_file():
        return False
    for suf in suffixes:
        if str(filename).endswith(suf):
            return True
    return False


def is_dcm_file(filename, check_exist=False):
    if check_exist and not Path(filename).is_file():
        return False
    return str(filename).endswith('.dcm') or str(filename).endswith('.dicom')


def make_empty_dir(dir_path):
    """Make an empty directory. If it exists - check that it is empty"""
    try:
        dir_path.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        # the directory exists
        try:
            next(dir_path.glob('*'))
        except StopIteration:
            pass  # the directory exists but empty - ok
        else:
            raise FileExistsError(f'The directory {str(dir_path)} is not empty')
