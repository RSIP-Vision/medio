"""A DICOM read must place every slice at its own ImagePositionPatient, whatever the SpacingBetweenSlices tag says.

The bug these tests lock down (issue #24): GE scanners (e.g. Discovery CT750 HD) write a *negative*
SpacingBetweenSlices. GDCMImageIO reports it as a negative z spacing, which ITK turns into a negated
slice direction. ImageSeriesReader then overrides the spacing magnitude from the slice positions but
keeps that negated direction, so slice k lands at origin - k*spacing instead of origin + k*spacing.
On a real 821-slice CT the last slice ended up ~1 m from its true position. The voxels and the origin
are right and every slice position is consistent, so series validation cannot see it.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Literal

import numpy as np
import pydicom
import pytest

import medio

if TYPE_CHECKING:
    from pathlib import Path

    from medio.metadata.metadata import MetaData

CLEAN_N = 150
CLEAN_SPACING = 0.312999993562698


def _copy_with_spacing_between_slices(dcm_dir: Path, dest: Path, value: float) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(dcm_dir.glob("*.dcm")):
        ds = pydicom.dcmread(f)
        ds.SpacingBetweenSlices = value
        ds.save_as(dest / f.name)
    return dest


def _slice_positions(series_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    """The lowest and highest ImagePositionPatient along the slice normal: the two ends of the volume."""
    datasets = [pydicom.dcmread(f, stop_before_pixels=True) for f in series_dir.glob("*.dcm")]
    iop = np.asarray(datasets[0].ImageOrientationPatient, float)
    normal = np.cross(iop[:3], iop[3:])
    positions = sorted((np.asarray(ds.ImagePositionPatient, float) for ds in datasets), key=lambda p: p @ normal)
    return positions[0], positions[-1]


def _world_ends(md: MetaData, n_slices: int) -> tuple[np.ndarray, np.ndarray]:
    """World (LPS) position of the first and last slice according to the affine, lowest first along z-index."""
    first = (md.affine @ [0, 0, 0, 1])[:3]
    last = (md.affine @ [0, 0, n_slices - 1, 1])[:3]
    return first, last


def _assert_ends_match_ipp(md: MetaData, series_dir: Path) -> None:
    lo, hi = _slice_positions(series_dir)
    first, last = _world_ends(md, CLEAN_N)
    ends = sorted([first, last], key=lambda p: float(p @ (hi - lo)))
    np.testing.assert_allclose(ends[0], lo, atol=1e-3)
    np.testing.assert_allclose(ends[1], hi, atol=1e-3)


@pytest.fixture
def negative_sbs_series(dcm_dir: Path, tmp_path: Path) -> Path:
    return _copy_with_spacing_between_slices(dcm_dir, tmp_path / "neg", -CLEAN_SPACING)


@pytest.mark.parametrize("backend", ["itk", "pdcm"])
@pytest.mark.parametrize("validate_series", [True, False])
def test_read_img_places_slices_at_their_ipp(
    negative_sbs_series: Path, backend: Literal["itk", "pdcm"], validate_series: bool
) -> None:
    """The fix is not part of validation: opting out of the consistency checks must not bring back a mirrored volume."""
    img, md = medio.read_img(negative_sbs_series, backend=backend, validate_series=validate_series)
    assert img.shape[2] == CLEAN_N
    _assert_ends_match_ipp(md, negative_sbs_series)
    assert float(np.asarray(md.spacing)[2]) == pytest.approx(CLEAN_SPACING, rel=1e-6)


@pytest.mark.parametrize("backend", ["itk", "pdcm"])
def test_read_meta_places_slices_at_their_ipp(negative_sbs_series: Path, backend: Literal["itk", "pdcm"]) -> None:
    md = medio.read_meta(negative_sbs_series, backend=backend)
    _assert_ends_match_ipp(md, negative_sbs_series)


def test_backends_agree_on_negative_spacing(negative_sbs_series: Path) -> None:
    img_itk, md_itk = medio.read_img(negative_sbs_series, backend="itk")
    img_pdcm, md_pdcm = medio.read_img(negative_sbs_series, backend="pdcm")
    np.testing.assert_allclose(md_itk.affine, md_pdcm.affine, atol=1e-4)
    np.testing.assert_array_equal(img_itk, img_pdcm)


def test_reorientation_after_fix_is_consistent(negative_sbs_series: Path, dcm_dir: Path) -> None:
    """Reorienting runs after the read, so it must start from the corrected direction: a mirrored
    input would make OrientImageFilter flip the voxels the wrong way."""
    img_neg, md_neg = medio.read_img(negative_sbs_series, backend="itk", desired_ornt="RAS")
    img_ref, md_ref = medio.read_img(dcm_dir, backend="itk", desired_ornt="RAS")
    np.testing.assert_allclose(md_neg.affine, md_ref.affine, atol=1e-4)
    np.testing.assert_array_equal(img_neg, img_ref)


@pytest.mark.parametrize("backend", ["itk", "pdcm"])
@pytest.mark.parametrize("as_file", [False, True], ids=["dir", "file"])
@pytest.mark.parametrize("reader", ["read_img", "read_meta"])
def test_single_slice_keeps_the_iop_normal(
    dcm_dir: Path, tmp_path: Path, backend: Literal["itk", "pdcm"], as_file: bool, reader: str
) -> None:
    """With one slice there is no second position to compare to, so the slice axis must follow the
    orientation normal (row x col), as it does when SpacingBetweenSlices is positive."""
    one = tmp_path / "one"
    one.mkdir()
    src = sorted(dcm_dir.glob("*.dcm"))[0]
    shutil.copyfile(src, one / src.name)
    path = one / src.name if as_file else one

    def read_affine() -> np.ndarray:
        if reader == "read_img":
            return medio.read_img(path, backend=backend)[1].affine
        return medio.read_meta(path, backend=backend).affine

    aff_pos = read_affine()
    _copy_with_spacing_between_slices(one, one, -CLEAN_SPACING)
    aff_neg = read_affine()
    np.testing.assert_allclose(aff_neg, aff_pos, atol=1e-4)
