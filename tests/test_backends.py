from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest

from medio.read_save import read_img, read_meta, save_dir, save_img

TEST_NII = os.path.join(os.path.dirname(__file__), "data", "test.nii.gz")
TEST_DCM_DIR = os.path.join(os.path.dirname(__file__), "data", "dcm")


class TestReadNifti:
    def test_read_nii(self) -> None:
        arr, meta = read_img(TEST_NII)
        assert arr is not None and arr.size > 0
        assert hasattr(meta, "affine")
        assert meta.coord_sys == "itk"

    def test_read_nii_nib_backend(self) -> None:
        arr, _ = read_img(TEST_NII, backend="nib")
        assert arr.ndim == 3

    def test_read_nii_itk_backend(self) -> None:
        arr, _ = read_img(TEST_NII, backend="itk")
        assert arr.ndim == 3

    def test_read_with_header(self) -> None:
        _, meta = read_img(TEST_NII, header=True)
        assert meta.header is not None

    def test_read_with_desired_ornt(self) -> None:
        _, meta = read_img(TEST_NII, desired_ornt="LPI")
        assert meta.ornt == "LPI"

    def test_read_nib_coord_sys(self) -> None:
        _, meta = read_img(TEST_NII, coord_sys="nib")
        assert meta.coord_sys == "nib"


class TestReadDicom:
    def test_read_dcm_dir(self) -> None:
        arr, _ = read_img(TEST_DCM_DIR)
        assert arr is not None and arr.size > 0

    def test_read_dcm_itk_backend(self) -> None:
        arr, _ = read_img(TEST_DCM_DIR, backend="itk")
        assert arr.ndim == 3

    def test_read_dcm_pdcm_backend(self) -> None:
        arr, _ = read_img(TEST_DCM_DIR, backend="pdcm")
        assert arr.ndim == 3


class TestSaveNifti:
    def test_write_read_roundtrip(self) -> None:
        arr, meta = read_img(TEST_NII)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.nii.gz")
            save_img(out_path, arr, meta)
            arr2, _ = read_img(out_path)
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
            arr2, _ = read_img(tmpdir)
            assert arr2.shape == arr.shape


class TestInvalidBackend:
    def test_invalid_read_backend(self) -> None:
        with pytest.raises(ValueError):
            read_img(TEST_NII, backend="invalid")  # type: ignore[call-overload]

    def test_invalid_save_backend(self) -> None:
        arr = np.zeros((10, 10, 10))
        meta_data = read_img(TEST_NII)[1]
        with pytest.raises(ValueError):
            save_img("/tmp/test.nii.gz", arr, meta_data, backend="invalid")  # type: ignore[arg-type]


class TestReadMetaOnly:
    def test_nii_spatial_shape_matches_full_read(self) -> None:
        arr, _ = read_img(TEST_NII)
        meta = read_meta(TEST_NII)
        assert meta.spatial_shape is not None
        assert meta.spatial_shape == arr.shape[:3]

    def test_nii_affine_matches_full_read(self) -> None:
        _, full_meta = read_img(TEST_NII)
        meta = read_meta(TEST_NII)
        np.testing.assert_allclose(meta.affine, full_meta.affine, atol=1e-5)

    def test_nii_coord_sys(self) -> None:
        meta = read_meta(TEST_NII)
        assert meta.coord_sys == "itk"

    def test_nii_spatial_shape_with_desired_ornt(self) -> None:
        arr, _ = read_img(TEST_NII, desired_ornt="LPI")
        meta = read_meta(TEST_NII, desired_ornt="LPI")
        assert meta.spatial_shape is not None
        assert meta.spatial_shape == arr.shape[:3]

    def test_nii_header_populated(self) -> None:
        meta = read_meta(TEST_NII, header=True)
        assert meta.header is not None
        assert isinstance(meta.header, dict)
        assert len(meta.header) > 0

    def test_nii_nib_backend_spatial_shape(self) -> None:
        arr, _ = read_img(TEST_NII, backend="nib")
        meta = read_meta(TEST_NII, backend="nib")
        assert meta.spatial_shape is not None
        assert meta.spatial_shape == arr.shape[:3]

    def test_nii_nib_backend_coord_sys_nib(self) -> None:
        meta = read_meta(TEST_NII, backend="nib", coord_sys="nib")
        assert meta.coord_sys == "nib"

    def test_dcm_dir_spatial_shape_matches_full_read(self) -> None:
        arr, _ = read_img(TEST_DCM_DIR)
        meta = read_meta(TEST_DCM_DIR)
        assert meta.spatial_shape is not None
        assert meta.spatial_shape == arr.shape[:3]

    def test_dcm_dir_affine_matches_full_read(self) -> None:
        _, full_meta = read_img(TEST_DCM_DIR)
        meta = read_meta(TEST_DCM_DIR)
        np.testing.assert_allclose(meta.affine, full_meta.affine, atol=1e-3)

    def test_dcm_dir_pdcm_backend_spatial_shape(self) -> None:
        arr, _ = read_img(TEST_DCM_DIR, backend="pdcm")
        meta = read_meta(TEST_DCM_DIR, backend="pdcm")
        assert meta.spatial_shape is not None
        assert meta.spatial_shape == arr.shape[:3]

    def test_dcm_dir_pdcm_affine_matches_itk(self) -> None:
        meta_itk = read_meta(TEST_DCM_DIR, backend="itk")
        meta_pdcm = read_meta(TEST_DCM_DIR, backend="pdcm")
        np.testing.assert_allclose(meta_itk.affine, meta_pdcm.affine, atol=1e-3)

    def test_invalid_backend(self) -> None:
        with pytest.raises(ValueError):
            read_meta(TEST_NII, backend="invalid")  # type: ignore[arg-type]
