"""Series-geometry validation: a DICOM directory must describe ONE consistent 3D volume.

The bug these tests lock down: a sagittal localizer sharing the axial SeriesInstanceUID was read
into the volume, silently inflating the derived slice spacing (real case: 0.700mm -> 0.81662mm, a
16.7% geometric error on a clinical scan). Grouping by SeriesInstanceUID cannot separate it, and ITK
only emits a warning, so every read path returned a corrupted volume without failing.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Literal

import numpy as np
import pydicom
import pydicom.uid
import pytest

import medio
from medio.utils.dcm_series import InconsistentSeriesError

if TYPE_CHECKING:
    from pathlib import Path

CLEAN_N = 150
CLEAN_SPACING = 0.312999993562698


def _copy_clean(dcm_dir: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted(dcm_dir.glob("*.dcm")):
        shutil.copyfile(f, dest / f.name)
    return dest


def _add_localizer(series_dir: Path) -> Path:
    """Append a scout slice that mimics the real defect: different orientation and pixel spacing,
    a position far outside the stack, but the SAME SeriesInstanceUID and matching Rows/Columns."""
    src = sorted(series_dir.glob("*.dcm"))[0]
    ds = pydicom.dcmread(src)
    ds.ImageOrientationPatient = [0, 1, 0, 0, 0, -1]  # sagittal, vs the axial [-1,0,0, 0,-1,0]
    ds.PixelSpacing = [0.4925, 0.4925]
    pos = [float(x) for x in ds.ImagePositionPatient]
    ds.ImagePositionPatient = [pos[0], pos[1], pos[2] + 60.0]  # well beyond the axial range
    ds.InstanceNumber = 1  # the real localizer sorted first by InstanceNumber
    ds.SOPInstanceUID = pydicom.uid.generate_uid()
    out = series_dir / "LOCALIZER.dcm"
    ds.save_as(out)
    return out


def _drop_middle_slice(series_dir: Path) -> None:
    """Create a genuine gap in an otherwise consistent stack (orientation stays uniform)."""
    files = sorted(series_dir.glob("*.dcm"), key=lambda p: float(pydicom.dcmread(p).ImagePositionPatient[2]))
    files[len(files) // 2].unlink()


@pytest.fixture
def clean_series(dcm_dir: Path, tmp_path: Path) -> Path:
    return _copy_clean(dcm_dir, tmp_path / "clean")


@pytest.fixture
def contaminated_series(dcm_dir: Path, tmp_path: Path) -> Path:
    d = _copy_clean(dcm_dir, tmp_path / "contaminated")
    _add_localizer(d)
    return d


@pytest.mark.parametrize("backend", ["itk", "pdcm"])
def test_clean_series_still_reads(clean_series: Path, backend: Literal["itk", "pdcm"]) -> None:
    """Validation must not disturb healthy data — real series are uniform to ~1e-12, far inside
    tolerance."""
    img, md = medio.read_img(clean_series, backend=backend)
    assert img.shape[2] == CLEAN_N
    assert float(np.asarray(md.spacing)[2]) == pytest.approx(CLEAN_SPACING, rel=1e-6)


@pytest.mark.parametrize("backend", ["itk", "pdcm"])
def test_localizer_in_series_hard_fails(contaminated_series: Path, backend: Literal["itk", "pdcm"]) -> None:
    with pytest.raises(InconsistentSeriesError) as exc:
        medio.read_img(contaminated_series, backend=backend)
    msg = str(exc.value)
    assert "LOCALIZER.dcm" in msg, "the offending file must be named so it can be investigated"
    assert "validate_series" in msg, "the error must state how to bypass it"


@pytest.mark.parametrize("backend", ["itk", "pdcm"])
def test_read_meta_fails_the_same_way(contaminated_series: Path, backend: Literal["itk", "pdcm"]) -> None:
    """read_meta previously disagreed with read_img on the pdcm backend — one raised, one did not.
    Both paths share the validator now, so they cannot diverge."""
    with pytest.raises(InconsistentSeriesError):
        medio.read_meta(contaminated_series, backend=backend)


def test_bypass_restores_the_previous_behaviour(contaminated_series: Path) -> None:
    """The escape hatch must actually return the old (wrong) geometry rather than a repaired one --
    callers opting out are asking for exactly what they got before."""
    img, md = medio.read_img(contaminated_series, backend="itk", validate_series=False)
    assert img.shape[2] == CLEAN_N + 1
    assert float(np.asarray(md.spacing)[2]) != pytest.approx(CLEAN_SPACING, rel=1e-3)


@pytest.mark.parametrize("backend", ["itk", "pdcm"])
def test_opt_in_filter_drops_the_localizer(contaminated_series: Path, backend: Literal["itk", "pdcm"]) -> None:
    img, md = medio.read_img(contaminated_series, backend=backend, keep_dominant_geometry=True)
    assert img.shape[2] == CLEAN_N
    assert float(np.asarray(md.spacing)[2]) == pytest.approx(CLEAN_SPACING, rel=1e-6)


def test_missing_slice_fails_even_with_uniform_orientation(clean_series: Path) -> None:
    """A real archive case (CT_00120) is non-uniform *within* one orientation — 96.8% gap deviation
    from missing slices. Orientation checks alone would pass it."""
    _drop_middle_slice(clean_series)
    with pytest.raises(InconsistentSeriesError) as exc:
        medio.read_img(clean_series, backend="itk")
    assert "spacing" in str(exc.value).lower() or "uniform" in str(exc.value).lower()


def test_filter_does_not_mask_a_genuine_gap(clean_series: Path) -> None:
    """keep_dominant_geometry removes off-geometry slices; it must NOT paper over a real gap in the
    slices that remain, or it becomes the silent behaviour we are removing."""
    _drop_middle_slice(clean_series)
    with pytest.raises(InconsistentSeriesError):
        medio.read_img(clean_series, backend="itk", keep_dominant_geometry=True)


def test_single_file_read_is_unaffected(nii_path: Path) -> None:
    img, _ = medio.read_img(nii_path)
    assert img.ndim >= 3
