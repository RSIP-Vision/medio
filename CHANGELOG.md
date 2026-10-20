# Changelog

## Unreleased

### Fixed

- **A DICOM series with a negative `SpacingBetweenSlices` is no longer mirrored along the slice axis
  by the ITK backend** ([#24](https://github.com/RSIP-Vision/medio/issues/24)). Some GE scanners
  (e.g. Discovery CT750 HD) write a negative value. ITK turned it into a negated slice direction, so
  slice `k` was placed at `origin - k*spacing` instead of `origin + k*spacing` (on a real 821-slice CT,
  the last slice was ~1 m from its true position). The voxels and origin were correct and the slice
  positions consistent, so series validation could not catch it. `read_img` and `read_meta` now point
  the slice axis from the first to the last `ImagePositionPatient`, with or without
  `validate_series`. The pydicom backend had the same sign error for a single slice; both backends now
  ignore the tag's sign.
- **`keep_dominant_geometry=True` no longer reads the remaining slices in scrambled order (ITK
  backend).** When the localizer is listed first, GDCM cannot sort the series by position and falls
  back to lexical file names (`IM1, IM10, IM100, …`). Dropping the localizer kept that order, so the
  slices were stacked out of order with a wrong spacing. Series files are now re-sorted along the slice
  normal whenever their order is not monotonic; a monotonic order is kept as given.

## 0.7.0

### Breaking

- **DICOM series are now geometrically validated, and an inconsistent series raises instead of
  returning a wrong image.** Reading a DICOM directory whose slices do not form a single consistent
  3D volume now raises `medio.InconsistentSeriesError` (a `ValueError` subclass).

  Grouping slices by Series Instance UID does not identify a volume: scanners emit a localizer/scout
  slice under the *same* Series Instance UID, Series Number and Series Description as the acquisition
  it belongs to. Including it corrupts the derived geometry, because the slice spacing is computed
  across the whole set — one distant off-axis slice stretches every voxel along the slice axis. On a
  real clinical CT this silently turned a 0.700 mm spacing into 0.81662 mm, a 16.7% geometric error,
  with no error and no exception.

  The underlying libraries do not catch this: ITK's `ImageSeriesReader` only emits a
  `Non uniform sampling or missing slices detected` **warning** and proceeds.

  Three invariants are enforced, each a property any single 3D volume must have:
  1. all slices share one orientation (direction cosines),
  2. all slices share one in-plane geometry (pixel spacing, rows, columns),
  3. slice positions are uniformly spaced along the slice normal (this also catches missing and
     duplicated slices, not only localizers).

  Agreement between the derived spacing and the `SliceThickness` tag is deliberately **not**
  required: gapped and overlapping reconstructions are legitimate, so `SliceThickness != spacing` is
  not an inconsistency.

  Tolerances are calibrated against 68 real CT series, in which healthy series deviate from a uniform
  gap by at most 1e-3 relative (median 5e-14) and per-slice orientation by at most 3.4e-5 degrees,
  while a genuinely broken stack deviated by 9.7e-1. The defaults sit about 10x above observed noise
  and 100x below a real defect.

  **To restore the previous behaviour**, pass `validate_series=False`. This returns the same
  (incorrect) geometry as before rather than a repaired one — an explicit opt-out means exactly what
  it says.

### Added

- `keep_dominant_geometry=False` on `read_img` / `read_meta` for DICOM directories: read only the
  slices sharing the dominant geometry, discarding e.g. a localizer. It filters first and then still
  validates what remains, so it never hides a genuine gap in the slices it keeps.
- `medio.InconsistentSeriesError`, and the `medio.utils.dcm_series` module holding the validator.
  Error messages name the offending files, report observed versus expected slice gaps, and state how
  to bypass the check.

### Fixed

- `read_meta(backend='pdcm')` and `read_img(backend='pdcm')` no longer disagree on the same
  directory. Previously `read_img` delegated to `dicom_numpy`, which validates, while `read_meta`
  used an internal affine computation that did not — so one raised and the other silently returned a
  corrupted affine. Both share the validator now.
- `read_meta(backend='pdcm')` on a series whose localizer sorts first by `InstanceNumber` no longer
  derives the affine origin from that slice.
