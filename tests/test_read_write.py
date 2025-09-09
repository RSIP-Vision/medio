import os
import tempfile
import numpy as np
from medio.read_save import read_img, save_img, save_dir

TEST_NII = os.path.join(os.path.dirname(__file__), 'data', 'test.nii.gz')
TEST_DCM_DIR = os.path.join(os.path.dirname(__file__), 'data', 'dcm')

def test_read_write_nii():
    # Read NIfTI
    arr, meta = read_img(TEST_NII)
    assert arr is not None and arr.size > 0
    assert hasattr(meta, 'affine') or hasattr(meta, 'header')

    # Write NIfTI to temp file and read back
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, 'out.nii.gz')
        save_img(out_path, arr, meta)
        arr2, meta2 = read_img(out_path)
        assert np.allclose(arr, arr2)
        assert hasattr(meta2, 'affine') or hasattr(meta2, 'header')

def test_read_write_dicom():
    # Read DICOM directory
    arr, meta = read_img(TEST_DCM_DIR)
    assert arr is not None and arr.size > 0
    # Write DICOM to temp dir and read back
    with tempfile.TemporaryDirectory() as tmpdir:
        save_dir(tmpdir, arr, meta)
        arr2, meta2 = read_img(tmpdir)
        assert arr2 is not None and arr2.size > 0
        # DICOM metadata may not have affine, but should have some attributes
        assert hasattr(meta2, 'series_uid') or hasattr(meta2, 'header')
