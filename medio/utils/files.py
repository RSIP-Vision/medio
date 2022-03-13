import pprint
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
    return is_file_suffix(
        filename,
        (".nii.gz", ".nii", ".img.gz", ".img", ".hdr"),
        check_exist=check_exist,
    )


def is_dicom(filename, check_exist=True):
    return is_file_suffix(
        filename, (".dcm", ".dicom", ".DCM", ".DICOM"), check_exist=check_exist
    )


def make_empty_dir(dir_path, parents=False):
    """Make an empty directory. If it exists - check that it is empty"""
    dir_path = Path(dir_path)
    try:
        dir_path.mkdir(parents=parents, exist_ok=False)
    except FileExistsError:
        # the directory exists
        try:
            next(dir_path.glob("*"))
        except StopIteration:
            pass  # the directory exists but empty - ok
        else:
            raise FileExistsError(f'The directory "{dir_path}" is not empty')


def make_dir(dir_path, parents=False, exist_ok=False):
    if exist_ok:
        Path(dir_path).mkdir(parents=parents, exist_ok=exist_ok)
    else:
        make_empty_dir(dir_path, parents)


def parse_series_uids(input_dir, series_uids, series=None, globber=None):
    """Receive an input dir, an iterable of series UIDs, and a series (UID string or int),
    return a series uid according to series_uids and series"""
    keys = sorted(series_uids)
    num_series = len(keys)
    if num_series == 0:
        raise FileNotFoundError(
            f'No DICOMs in:\n"{input_dir}"'
            + (f'\nwith globber="{globber}"' if globber is not None else "")
        )

    if num_series == 1:
        return keys[0]

    # if there is more than a single series
    if num_series > 1:
        if series is None:
            raise ValueError(
                f'The directory: "{input_dir}"\n'
                "contains more than a single DICOM series. "
                "The following series were identified according to their Series Instance UID:\n"
                f"{pprint.pformat(keys)}\n"
                "Try passing: series=series_uid, where series_uid is a one of the strings above,\n"
                f"or an integer between 0 and {num_series - 1} corresponding to one of them."
            )
        elif isinstance(series, int):
            return keys[series]
        else:
            if series not in keys:
                raise ValueError(
                    "The series:\n"
                    f"'{series}'\n"
                    "is not one of the following:"
                    f"\n{pprint.pformat(keys)}"
                )
            return series
