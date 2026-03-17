from __future__ import annotations

import numpy as np

from medio.metadata.affine import Affine
from medio.metadata.convert_nib_itk import convert_affine, convert_nib_itk, inv_axcodes


class TestInvAxcodes:
    def test_basic(self) -> None:
        assert inv_axcodes("RAS") == "LPI"
        assert inv_axcodes("LPI") == "RAS"
        assert inv_axcodes("SPL") == "IAR"

    def test_none(self) -> None:
        assert inv_axcodes(None) is None

    def test_single_char(self) -> None:
        assert inv_axcodes("R") == "L"
        assert inv_axcodes("S") == "I"

    def test_roundtrip(self) -> None:
        assert inv_axcodes(inv_axcodes("RAS")) == "RAS"


class TestConvertAffine:
    def test_identity_3d(self) -> None:
        aff = np.eye(4)
        result = convert_affine(aff)
        expected = np.diag([-1, -1, 1, 1]).astype(float)
        np.testing.assert_array_almost_equal(result, expected)

    def test_identity_2d(self) -> None:
        aff = np.eye(3)
        result = convert_affine(aff)
        expected = np.diag([-1, -1, 1]).astype(float)
        np.testing.assert_array_almost_equal(result, expected)

    def test_roundtrip(self) -> None:
        aff = np.array([
            [0.5, 0, 0, 10],
            [0, 0.5, 0, 20],
            [0, 0, 1, 30],
            [0, 0, 0, 1],
        ], dtype=float)
        result = convert_affine(convert_affine(aff))
        np.testing.assert_array_almost_equal(result, aff)

    def test_preserves_affine_type(self) -> None:
        aff = Affine(np.eye(4))
        result = convert_affine(aff)
        assert isinstance(result, Affine)


class TestConvertNibItk:
    def test_with_axcodes(self) -> None:
        aff = Affine(np.eye(4))
        _, new_axcodes = convert_nib_itk(aff, "RAS")
        assert new_axcodes == "LPI"

    def test_with_none_axcodes(self) -> None:
        aff = Affine(np.eye(4))
        _, new_axcodes = convert_nib_itk(aff, None)
        assert new_axcodes is None

    def test_roundtrip(self) -> None:
        aff = Affine(direction=np.eye(3), spacing=[0.5, 0.5, 1.0], origin=[10, 20, 30])
        result = convert_nib_itk(aff, "LPI", "RAS")
        new_aff = result[0]
        new_ornt = result[1]
        new_orig = result[2]
        assert isinstance(new_aff, (np.ndarray, Affine))
        assert isinstance(new_ornt, (str, type(None)))
        assert isinstance(new_orig, (str, type(None)))
        result2 = convert_nib_itk(new_aff, new_ornt, new_orig)
        final_aff = result2[0]
        final_ornt = result2[1]
        final_orig = result2[2]
        np.testing.assert_array_almost_equal(np.asarray(final_aff), np.asarray(aff))
        assert final_ornt == "LPI"
        assert final_orig == "RAS"
