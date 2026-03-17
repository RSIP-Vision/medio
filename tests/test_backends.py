from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest

from medio.read_save import read_img, save_dir, save_img

TEST_NII = os.path.join(os.path.dirname(__file__), "data", "test.nii.gz")
TEST_DCM_DIR = os.path.join(os.path.dirname(__file__), "data", "dcm")


class TestReadNifti:
    def test_read_nii(self) -> None:
        arr, meta = read_img(TEST_NII)
        assert arr is not None and arr.size > 0
        assert hasattr(meta, "affine")
        assert meta.coord_sys == "itk"

    def test_read_nii_nib_backend(self) -> None:
        arr, meta = read_img(TEST_NII, backend="nib")
        assert arr.ndim == 3

    def test_read_nii_itk_backend(self) -> None:
        arr, meta = read_img(TEST_NII, backend="itk")
        assert arr.ndim == 3

    def test_read_with_header(self) -> None:
        arr, meta = read_img(TEST_NII, header=True)
        assert meta.header is not None

    def test_read_with_desired_ornt(self) -> None:
        arr, meta = read_img(TEST_NII, desired_ornt="LPI")
        assert meta.ornt == "LPI"

    def test_read_nib_coord_sys(self) -> None:
        arr, meta = read_img(TEST_NII, coord_sys="nib")
        assert meta.coord_sys == "nib"


class TestReadDicom:
    def test_read_dcm_dir(self) -> None:
        arr, meta = read_img(TEST_DCM_DIR)
        assert arr is not None and arr.size > 0

    def test_read_dcm_itk_backend(self) -> None:
        arr, meta = read_img(TEST_DCM_DIR, backend="itk")
        assert arr.ndim == 3

    def test_read_dcm_pdcm_backend(self) -> None:
        arr, meta = read_img(TEST_DCM_DIR, backend="pdcm")
        assert arr.ndim == 3


class TestSaveNifti:
    def test_write_read_roundtrip(self) -> None:
        arr, meta = read_img(TEST_NII)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.nii.gz")
            save_img(out_path, arr, meta)
            arr2, meta2 = read_img(out_path)
            np.testing.assert_allclose(np.asarray(arr, dtype=float), np.asarray(arr2, dtype=float), atol=1e-5)

    def test_write_with_mkdir(self) -> None:
        arr, meta = read_img(TEST_NII)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "sub", "out.nii.gz")
            save_img(out_path, arr, meta, mkdir=True, parents=True)
            assert os.path.exists(out_path)

    def test_write_with_dtype(self) -> None:
        arr, meta = read_img(TEST_NII)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.nii.gz")
            save_img(out_path, arr, meta, dtype=np.float32)
            arr2, _ = read_img(out_path)
            assert arr2.dtype == np.float32


class TestSaveDicomDir:
    def test_save_dcm_roundtrip(self) -> None:
        arr, meta = read_img(TEST_DCM_DIR)
        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir(tmpdir, arr, meta)
            arr2, meta2 = read_img(tmpdir)
            assert arr2.shape == arr.shape


class TestInvalidBackend:
    def test_invalid_read_backend(self) -> None:
        with pytest.raises(ValueError):
            read_img(TEST_NII, backend="invalid")

    def test_invalid_save_backend(self) -> None:
        arr = np.zeros((10, 10, 10))
        meta_data = read_img(TEST_NII)[1]
        with pytest.raises(ValueError):
            save_img("/tmp/test.nii.gz", arr, meta_data, backend="invalid")
