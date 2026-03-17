from __future__ import annotations

import numpy as np
import pytest

from medio.metadata.affine import Affine
from medio.metadata.metadata import (
    MetaData,
    check_dcm_ornt,
    flip_last_axcodes,
    is_right_handed_axcodes,
)


class TestMetaDataConstruction:
    def test_basic(self) -> None:
        aff = Affine(np.eye(4))
        meta = MetaData(aff, coord_sys="itk")
        assert meta.coord_sys == "itk"
        assert meta.header is None

    def test_with_header(self) -> None:
        aff = Affine(np.eye(4))
        header = {"key": "value"}
        meta = MetaData(aff, coord_sys="itk", header=header)
        assert meta.header == {"key": "value"}

    def test_with_orig_ornt(self) -> None:
        aff = Affine(np.eye(4))
        meta = MetaData(aff, orig_ornt="LPI", coord_sys="itk")
        assert meta.orig_ornt == "LPI"

    def test_invalid_coord_sys(self) -> None:
        aff = Affine(np.eye(4))
        with pytest.raises(ValueError):
            MetaData(aff, coord_sys="invalid")  # type: ignore[arg-type]

    def test_accepts_ndarray(self) -> None:
        meta = MetaData(np.eye(4), coord_sys="itk")
        assert isinstance(meta.affine, Affine)


class TestMetaDataConvert:
    def test_convert_itk_to_nib(self) -> None:
        aff = Affine(np.eye(4))
        meta = MetaData(aff, coord_sys="itk")
        meta.convert("nib")
        assert meta.coord_sys == "nib"

    def test_convert_noop(self) -> None:
        aff = Affine(np.eye(4))
        meta = MetaData(aff, coord_sys="itk")
        orig_affine = meta.affine.copy()
        meta.convert("itk")
        np.testing.assert_array_equal(meta.affine, orig_affine)

    def test_convert_roundtrip(self) -> None:
        aff = Affine(direction=np.eye(3), spacing=[0.5, 0.5, 1.0], origin=[10, 20, 30])
        meta = MetaData(aff, orig_ornt="LPI", coord_sys="itk")
        orig_affine = meta.affine.copy()
        meta.convert("nib")
        meta.convert("itk")
        np.testing.assert_array_almost_equal(meta.affine, orig_affine)


class TestMetaDataClone:
    def test_clone_independent(self) -> None:
        aff = Affine(np.eye(4))
        meta = MetaData(aff, orig_ornt="LPI", coord_sys="itk", header={"a": 1})
        clone = meta.clone()
        clone.affine.origin = [1, 2, 3]
        np.testing.assert_array_equal(meta.affine.origin, [0, 0, 0])

    def test_clone_header_copy(self) -> None:
        meta = MetaData(Affine(np.eye(4)), coord_sys="itk", header={"a": [1, 2]})
        clone = meta.clone()
        clone.header["a"].append(3)  # type: ignore[union-attr]
        assert meta.header["a"] == [1, 2]  # type: ignore[index]


class TestMetaDataSpacing:
    def test_spacing(self) -> None:
        aff = Affine(direction=np.eye(3), spacing=[0.5, 1.0, 2.0], origin=[0, 0, 0])
        meta = MetaData(aff, coord_sys="itk")
        np.testing.assert_array_almost_equal(meta.spacing, [0.5, 1.0, 2.0])


class TestMetaDataRepr:
    def test_repr_has_info(self) -> None:
        aff = Affine(np.eye(4))
        meta = MetaData(aff, coord_sys="itk")
        r = repr(meta)
        assert "Affine" in r
        assert "itk" in r


class TestIsRightHanded:
    # Convention: I=[0,0,+1], S=[0,0,-1], so RAI=right-handed, RAS=left-handed
    def test_right_handed(self) -> None:
        assert is_right_handed_axcodes("RAI")
        assert is_right_handed_axcodes("LPI")
        assert is_right_handed_axcodes("AIR")

    def test_left_handed(self) -> None:
        assert not is_right_handed_axcodes("RAS")
        assert not is_right_handed_axcodes("LPS")

    def test_2d_always_right(self) -> None:
        assert is_right_handed_axcodes("RA")

    def test_invalid_length(self) -> None:
        with pytest.raises(ValueError):
            is_right_handed_axcodes("RASI")


class TestFlipLastAxcodes:
    def test_flip(self) -> None:
        assert flip_last_axcodes("RAS") == "RAI"
        assert flip_last_axcodes("LPI") == "LPS"


class TestCheckDcmOrnt:
    def test_right_handed_passthrough(self) -> None:
        meta = MetaData(Affine(np.eye(4)), orig_ornt="LPI", coord_sys="itk")
        result = check_dcm_ornt("LPI", meta)
        assert result == "LPI"

    def test_left_handed_raises(self) -> None:
        meta = MetaData(Affine(np.eye(4)), orig_ornt="LPS", coord_sys="itk")
        with pytest.raises(ValueError):
            check_dcm_ornt("LPS", meta)

    def test_left_handed_allow_reorient(self) -> None:
        meta = MetaData(Affine(np.eye(4)), orig_ornt="LPS", coord_sys="itk")
        result = check_dcm_ornt("LPS", meta, allow_dcm_reorient=True)
        assert is_right_handed_axcodes(result)
