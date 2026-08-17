"""Geometric validation of a DICOM series: does this set of slices describe ONE 3D volume?

Grouping slices by Series Instance UID is not sufficient. Scanners do emit a localizer/scout under
the *same* Series Instance UID, Series Number and Series Description as the acquisition it belongs
to, differing only in orientation and pixel spacing. Such a slice is not part of the volume, and
including it corrupts the derived geometry: the slice spacing is computed across the whole set, so
one distant off-axis slice silently stretches every voxel along the slice axis.

That failure is silent by default in the underlying libraries -- ITK's ImageSeriesReader only emits
a "Non uniform sampling or missing slices detected" *warning* and proceeds -- which makes it exactly
the kind of defect that reaches downstream measurements unnoticed. Hence the checks here are
hard-failing, with an explicit opt-out.

Three invariants are enforced, all properties any single 3D volume must have:
  1. every slice shares one orientation (direction cosines),
  2. every slice shares one in-plane geometry (pixel spacing, rows, columns),
  3. slice positions along the slice normal are uniformly spaced.

Deliberately NOT enforced: agreement between the derived spacing and the SliceThickness tag. Gapped
and overlapping reconstructions are legitimate and common, so `SliceThickness != spacing` is not an
inconsistency -- treating it as one would reject valid data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pydicom

if TYPE_CHECKING:
    import os
    from collections.abc import Iterable, Sequence

    from numpy.typing import NDArray


# Tolerances calibrated against 68 real CT series: healthy series deviate from a uniform gap by
# <= 1e-3 relative (median 5e-14), and their per-slice orientation varies by <= 3.4e-5 degrees. A
# genuinely broken stack in the same sample deviated by 9.7e-1. These defaults therefore sit ~10x
# above observed noise and ~100x below a real defect.
DEFAULT_SPACING_RTOL = 1e-2
DEFAULT_SPACING_ATOL = 1e-4  # mm; keeps sub-micron noise on very thin slices from tripping the check
DEFAULT_ANGLE_TOL_DEG = 1e-3

_GEOMETRY_TAGS = [
    "ImageOrientationPatient",
    "ImagePositionPatient",
    "PixelSpacing",
    "Rows",
    "Columns",
]

_BYPASS_HINT = (
    "Pass validate_series=False to read it anyway (the geometry will be wrong), or "
    "keep_dominant_geometry=True to read only the slices that share the dominant geometry."
)


class InconsistentSeriesError(ValueError):
    """A DICOM series does not describe a single consistent 3D volume.

    Subclasses ValueError so that callers already handling malformed input keep working.
    """


@dataclass(frozen=True)
class SliceGeometry:
    """The geometry of one slice, plus a human-readable key for error messages."""

    key: str
    orientation: tuple[float, ...]
    position: tuple[float, ...]
    pixel_spacing: tuple[float, float]
    shape: tuple[int, int]

    @property
    def normal(self) -> NDArray[np.float64]:
        row, col = np.asarray(self.orientation[:3], float), np.asarray(self.orientation[3:], float)
        n = np.cross(row, col)
        norm = float(np.linalg.norm(n))
        if norm == 0:
            raise InconsistentSeriesError(f"Degenerate ImageOrientationPatient in {self.key}: {self.orientation}")
        return n / norm

    @property
    def in_plane(self) -> tuple[float, float, int, int]:
        """The properties that must match for slices to stack into one array."""
        return (*self.pixel_spacing, *self.shape)


def geometry_from_dataset(ds: pydicom.Dataset, key: str) -> SliceGeometry | None:
    """None when the dataset carries no slice geometry (e.g. a non-image DICOM object)."""
    if not hasattr(ds, "ImageOrientationPatient") or not hasattr(ds, "ImagePositionPatient"):
        return None
    ornt = tuple(float(x) for x in ds.ImageOrientationPatient)
    pos = tuple(float(x) for x in ds.ImagePositionPatient)
    spacing = getattr(ds, "PixelSpacing", None)
    pixel_spacing = (float(spacing[0]), float(spacing[1])) if spacing is not None else (1.0, 1.0)
    shape = (int(getattr(ds, "Rows", 0)), int(getattr(ds, "Columns", 0)))
    if len(ornt) != 6 or len(pos) != 3:
        return None
    return SliceGeometry(key=key, orientation=ornt, position=pos, pixel_spacing=pixel_spacing, shape=shape)


def geometry_from_file(path: str | os.PathLike[str]) -> SliceGeometry | None:
    """Read only the geometry tags, so validating a series stays cheap next to reading pixels."""
    try:
        ds = pydicom.dcmread(str(path), stop_before_pixels=True, specific_tags=_GEOMETRY_TAGS)
    except Exception:
        return None
    return geometry_from_dataset(ds, key=str(path))


def geometries_from_files(paths: Iterable[str | os.PathLike[str]]) -> list[SliceGeometry]:
    return [g for g in (geometry_from_file(p) for p in paths) if g is not None]


def select_dominant(geometries: Sequence[SliceGeometry]) -> tuple[list[SliceGeometry], list[SliceGeometry]]:
    """Split into the slices sharing the most common (orientation, in-plane geometry) and the rest.

    Ties are broken deterministically by the first-seen group, so repeated reads of one directory
    always yield the same volume.
    """
    if not geometries:
        return [], []
    order: list[tuple[tuple[float, ...], tuple[float, float, int, int]]] = []
    counts: dict[tuple[tuple[float, ...], tuple[float, float, int, int]], int] = {}
    for g in geometries:
        key = (_rounded_orientation(g.orientation), g.in_plane)
        if key not in counts:
            order.append(key)
            counts[key] = 0
        counts[key] += 1
    best = max(order, key=lambda k: counts[k])
    keep, drop = [], []
    for g in geometries:
        (keep if (_rounded_orientation(g.orientation), g.in_plane) == best else drop).append(g)
    return keep, drop


def _rounded_orientation(orientation: tuple[float, ...], decimals: int = 5) -> tuple[float, ...]:
    """Group orientations robustly: stored cosines carry float noise well below any real difference."""
    return tuple(round(float(x), decimals) for x in orientation)


def validate_series(
    geometries: Sequence[SliceGeometry],
    *,
    spacing_rtol: float = DEFAULT_SPACING_RTOL,
    spacing_atol: float = DEFAULT_SPACING_ATOL,
    angle_tol_deg: float = DEFAULT_ANGLE_TOL_DEG,
) -> None:
    """Raise InconsistentSeriesError unless the slices describe one consistent 3D volume."""
    if len(geometries) < 2:
        return  # a single slice has no inter-slice geometry to be inconsistent about

    _check_in_plane(geometries)
    _check_orientation(geometries, angle_tol_deg)
    _check_uniform_spacing(geometries, spacing_rtol, spacing_atol)


def _check_in_plane(geometries: Sequence[SliceGeometry]) -> None:
    groups: dict[tuple[float, float, int, int], list[str]] = {}
    for g in geometries:
        groups.setdefault(g.in_plane, []).append(g.key)
    if len(groups) == 1:
        return
    majority = max(groups, key=lambda k: len(groups[k]))
    lines = [
        f"  {in_plane} : {len(keys)} slice(s), e.g. {_sample(keys)}"
        for in_plane, keys in sorted(groups.items(), key=lambda kv: -len(kv[1]))
    ]
    raise InconsistentSeriesError(
        "DICOM series mixes different in-plane geometry (pixel spacing, rows, columns), so the "
        "slices do not form a single volume.\n"
        "Groups as (row_spacing, col_spacing, rows, columns):\n" + "\n".join(lines) + f"\n"
        f"The dominant geometry is {majority}. This usually means a localizer/scout slice shares the "
        f"Series Instance UID with the acquisition.\n" + _BYPASS_HINT
    )


def _check_orientation(geometries: Sequence[SliceGeometry], angle_tol_deg: float) -> None:
    reference = geometries[0].normal
    offenders: list[tuple[str, float]] = []
    for g in geometries[1:]:
        cos = float(np.clip(np.dot(g.normal, reference), -1.0, 1.0))
        angle = float(np.degrees(np.arccos(abs(cos))))
        if angle > angle_tol_deg:
            offenders.append((g.key, angle))
    if not offenders:
        return
    worst = sorted(offenders, key=lambda t: -t[1])
    listed = "\n".join(f"  {key} : {angle:.4f} deg from the first slice" for key, angle in worst[:5])
    more = f"\n  ... and {len(worst) - 5} more" if len(worst) > 5 else ""
    raise InconsistentSeriesError(
        f"DICOM series mixes slice orientations: {len(offenders)} of {len(geometries)} slice(s) are "
        f"not parallel to the first (tolerance {angle_tol_deg} deg). A single 3D volume cannot "
        f"contain slices at different orientations; this is typically a localizer/scout slice "
        f"sharing the Series Instance UID with the acquisition.\n" + listed + more + "\n" + _BYPASS_HINT
    )


def _check_uniform_spacing(geometries: Sequence[SliceGeometry], rtol: float, atol: float) -> None:
    normal = geometries[0].normal
    projected = sorted((float(np.dot(np.asarray(g.position, float), normal)), g.key) for g in geometries)
    positions = np.array([p for p, _ in projected])
    keys = [k for _, k in projected]
    gaps = np.diff(positions)

    duplicates = [(keys[i], keys[i + 1]) for i, gap in enumerate(gaps) if abs(gap) <= atol]
    if duplicates:
        listed = "\n".join(f"  {a}\n  {b}" for a, b in duplicates[:3])
        raise InconsistentSeriesError(
            f"DICOM series contains {len(duplicates)} pair(s) of slices at the same position along the "
            f"slice normal, so the slice spacing is undefined. Duplicated positions:\n" + listed + "\n" + _BYPASS_HINT
        )

    median_gap = float(np.median(gaps))
    if median_gap <= 0:
        raise InconsistentSeriesError(
            f"DICOM series has a non-positive median slice gap ({median_gap}); slice positions are "
            f"not monotonic along the slice normal.\n" + _BYPASS_HINT
        )
    tolerance = max(atol, rtol * abs(median_gap))
    deviation = np.abs(gaps - median_gap)
    bad = np.nonzero(deviation > tolerance)[0]
    if bad.size == 0:
        return
    listed = "\n".join(
        f"  gap {float(gaps[i]):.6f} mm (expected ~{median_gap:.6f}) between\n    {keys[i]}\n    {keys[i + 1]}"
        for i in bad[:3]
    )
    more = f"\n  ... and {bad.size - 3} more" if bad.size > 3 else ""
    raise InconsistentSeriesError(
        f"DICOM series is not uniformly sampled along the slice axis: {bad.size} of {gaps.size} gap(s) "
        f"deviate from the median gap of {median_gap:.6f} mm by more than {tolerance:.6f} mm "
        f"(rtol={rtol}, atol={atol}). Reading it would assign every voxel a wrong slice spacing. "
        f"This is usually a missing slice, a duplicated slice, or an extra off-axis slice.\n"
        + listed
        + more
        + "\n"
        + _BYPASS_HINT
    )


def resolve_series_files(
    filenames: Sequence[str],
    validate: bool = True,
    keep_dominant_geometry: bool = False,
    **tolerances: float,
) -> list[str]:
    """Return the filenames to read, applying the optional dominant-geometry filter and validation.

    Order of operations matters: filtering happens first so that a discarded localizer does not make
    the uniformity check fail, but validation still runs on what remains -- otherwise the filter
    would quietly accept a stack with a genuine gap, reintroducing the silence this module removes.
    """
    if not validate and not keep_dominant_geometry:
        return list(filenames)

    geometries = geometries_from_files(filenames)
    if not geometries:
        return list(filenames)  # nothing to check (e.g. non-DICOM inputs)

    kept = geometries
    if keep_dominant_geometry:
        kept, _dropped = select_dominant(geometries)
    if validate:
        validate_series(kept, **tolerances)

    if not keep_dominant_geometry:
        return list(filenames)
    keep_keys = {g.key for g in kept}
    return [f for f in filenames if str(f) in keep_keys]


def resolve_series_datasets(
    slices: Sequence[pydicom.Dataset],
    validate: bool = True,
    keep_dominant_geometry: bool = False,
    **tolerances: float,
) -> list[pydicom.Dataset]:
    """Dataset-based counterpart of resolve_series_files, for the pydicom backend."""
    if not validate and not keep_dominant_geometry:
        return list(slices)

    pairs = [(ds, geometry_from_dataset(ds, key=_dataset_key(ds, i))) for i, ds in enumerate(slices)]
    geometries = [g for _, g in pairs if g is not None]
    if not geometries:
        return list(slices)

    kept_geoms = geometries
    if keep_dominant_geometry:
        kept_geoms, _dropped = select_dominant(geometries)
    if validate:
        validate_series(kept_geoms, **tolerances)

    if not keep_dominant_geometry:
        return list(slices)
    keep_keys = {g.key for g in kept_geoms}
    return [ds for ds, g in pairs if g is not None and g.key in keep_keys]


def _dataset_key(ds: pydicom.Dataset, index: int) -> str:
    """Datasets may carry no filename, so fall back to something a human can still act on."""
    filename = getattr(ds, "filename", None)
    if filename:
        return str(filename)
    uid = getattr(ds, "SOPInstanceUID", None)
    return f"SOPInstanceUID={uid}" if uid else f"slice #{index}"


def _sample(keys: Sequence[str], limit: int = 2) -> str:
    shown = ", ".join(keys[:limit])
    return shown + (f" (+{len(keys) - limit} more)" if len(keys) > limit else "")
