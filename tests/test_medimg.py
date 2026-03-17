from __future__ import annotations

import numpy as np
import pytest

from medio.metadata.affine import Affine
from medio.metadata.metadata import MetaData
from medio.medimg.medimg import MedImg


class TestMedImgConstruction:
    def test_from_array_and_metadata(self) -> None:
        arr = np.zeros((10, 20, 30))
        meta = MetaData(Affine(np.eye(4)), coord_sys="itk")
        mimg = MedImg(arr, meta)
        assert mimg.np_image.shape == (10, 20, 30)

    def test_from_file(self, nii_path) -> None:  # type: ignore[no-untyped-def]
        mimg = MedImg(None, None, filename=nii_path)
        assert mimg.np_image is not None
        assert mimg.np_image.ndim == 3


class TestMedImgSlicing:
    def test_basic_crop(self) -> None:
        arr = np.arange(1000).reshape(10, 10, 10).astype(float)
        aff = Affine(direction=np.eye(3), spacing=[1.0, 1.0, 1.0], origin=[0.0, 0.0, 0.0])
        meta = MetaData(aff, coord_sys="itk")
        mimg = MedImg(arr, meta)
        cropped = mimg[2:8, 3:7, 1:9]
        assert cropped.np_image.shape == (6, 4, 8)

    def test_crop_updates_origin(self) -> None:
        arr = np.zeros((10, 10, 10))
        aff = Affine(direction=np.eye(3), spacing=[2.0, 2.0, 2.0], origin=[0.0, 0.0, 0.0])
        meta = MetaData(aff, coord_sys="itk")
        mimg = MedImg(arr, meta)
        cropped = mimg[5:, :, :]
        np.testing.assert_array_almost_equal(cropped.metadata.affine.origin, [10.0, 0.0, 0.0])

    def test_downsample_updates_spacing(self) -> None:
        arr = np.zeros((100, 100, 100))
        aff = Affine(direction=np.eye(3), spacing=[1.0, 1.0, 1.0], origin=[0.0, 0.0, 0.0])
        meta = MetaData(aff, coord_sys="itk")
        mimg = MedImg(arr, meta)
        downsampled = mimg[::2, ::3, ::5]
        np.testing.assert_array_almost_equal(downsampled.metadata.affine.spacing, [2.0, 3.0, 5.0])

    def test_ellipsis(self) -> None:
        arr = np.zeros((10, 20, 30))
        aff = Affine(direction=np.eye(3), spacing=[1.0, 1.0, 1.0], origin=[0.0, 0.0, 0.0])
        meta = MetaData(aff, coord_sys="itk")
        mimg = MedImg(arr, meta)
        cropped = mimg[..., 5:15]
        assert cropped.np_image.shape == (10, 20, 10)

    def test_slicing_preserves_coord_sys(self) -> None:
        arr = np.zeros((10, 10, 10))
        aff = Affine(direction=np.eye(3), spacing=[1.0, 1.0, 1.0], origin=[0.0, 0.0, 0.0])
        meta = MetaData(aff, coord_sys="itk")
        mimg = MedImg(arr, meta)
        cropped = mimg[2:8, :, :]
        assert cropped.metadata.coord_sys == "itk"


class TestMedImgSave:
    def test_save_roundtrip(self, nii_path, tmp_dir) -> None:  # type: ignore[no-untyped-def]
        mimg = MedImg(None, None, filename=nii_path)
        out = tmp_dir / "out.nii.gz"
        mimg.save(out)
        mimg2 = MedImg(None, None, filename=out)
        np.testing.assert_array_almost_equal(
            np.asarray(mimg.np_image, dtype=float), np.asarray(mimg2.np_image, dtype=float)
        )
