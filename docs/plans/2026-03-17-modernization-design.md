# medio Modernization Design

**Date**: 2026-03-17
**Goal**: Modernize the project while keeping logic, API, and behavior the same.

## Decisions

- **Min Python**: 3.9+
- **Approach**: Big bang (single coordinated pass)
- **Dependencies**: All backends remain required; add numpy as explicit dep
- **Typing**: Strict, advanced (overloads, TypeGuard, Generic, Protocol, Literal, etc.)
- **Type checker**: ty in strict mode, blocks CI
- **Tests**: Unit + integration
- **CI**: GitHub Actions on PR + push to main, required to pass before merge
- **Release**: Tag-triggered PyPI publish via trusted publisher (OIDC)
- **Versioning**: Single source in pyproject.toml, read via importlib.metadata

## 1. Build System Migration

### pyproject.toml

- Build backend: `uv_build` (uv's native build backend)
- `requires-python = ">=3.9"`
- Version: single source in `[project].version`
- Runtime deps: itk, nibabel, pydicom, dicom-numpy, numpy
- Dev dependency groups: test (pytest), dev (ruff, ty)
- Remove hatch-specific config

### __init__.py

Replace hardcoded `__version__` with:
```python
from importlib.metadata import version
__version__ = version("medio")
```

### Other files

- Add `.python-version` file (e.g., "3.12")
- Remove `noxfile.py` (replaced by CI matrix)
- Keep `uv.lock` (regenerate after pyproject.toml changes)

## 2. Typing Strategy

### General

- `from __future__ import annotations` in every file
- `typing_extensions` for features unavailable in 3.9: Self, TypeAlias, override, TypeGuard, Unpack, TypedDict
- `py.typed` marker file for PEP 561

### Per-module plan

| Module | Advanced Typing |
|--------|----------------|
| `read_save.py` | `@overload` for `read_img()` — dispatches on `image_only: Literal[True/False]` and `header: Literal[True/False]`. Returns `ndarray`, `tuple[ndarray, MetaData[None]]`, or `tuple[ndarray, MetaData[HeaderDict]]`. |
| `backends/itk_io.py` | `@overload` on `read()` for `image_only`. `Literal` for orientation params. `TypeAlias` for ITK image types. |
| `backends/nib_io.py` | `@overload` on `read()` for `image_only`. `TypeAlias` for nibabel image types. |
| `backends/pdcm_io.py` | `@overload` on `read()` for `image_only`. `TypeGuard` for multi-frame checks. |
| `metadata/affine.py` | `Self` return type for `clone()`. `NDArray` typed arrays. |
| `metadata/metadata.py` | `Generic[H]` — `MetaData` parameterized by header type. `Literal` for coord system. |
| `metadata/itk_orientation.py` | `Literal` types for axis codes. Typed enums. |
| `metadata/pdcm_ds.py` | `@override` on property overrides. |
| `utils/two_way_dict.py` | `Generic[KT, VT]` — typed bidirectional dict. |
| `utils/files.py` | `TypeGuard` for `is_nifti()`, `is_dicom()`. |
| `utils/explicit_slicing.py` | Typed slice handling with proper tuple types. |
| `medimg/medimg.py` | `Self` on `__getitem__` return. Proper MetaData generics. |

## 3. Tooling Configuration

All in `pyproject.toml`:

### Ruff
```toml
[tool.ruff]
target-version = "py39"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "TCH", "RUF"]

[tool.ruff.format]
quote-style = "double"
```

### ty
```toml
[tool.ty]
python-version = "3.9"
```
Strict mode — errors block CI.

### pytest
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

## 4. Test Strategy

### Structure
```
tests/
    conftest.py              # Shared fixtures
    data/                    # Existing test data
    test_read_write.py       # Existing integration tests (refactored)
    test_affine.py           # Affine class unit tests
    test_metadata.py         # MetaData class unit tests
    test_convert_nib_itk.py  # Coordinate conversion unit tests
    test_itk_orientation.py  # Orientation code unit tests
    test_medimg.py           # MedImg slicing/cropping unit tests
    test_files.py            # File type detection unit tests
    test_two_way_dict.py     # TwoWayDict unit tests
    test_explicit_slicing.py # Slice handling unit tests
    test_dcm_uid.py          # DICOM UID generation unit tests
    test_pdcm_ds.py          # MultiFrameFileDataset unit tests
    test_backends.py         # Per-backend integration tests
```

### Coverage areas
- Affine: construction, decomposition, index2coord, clone, edge cases
- MetaData: construction w/ and w/o header, orientation, coord system, generic typing
- Coordinate conversion: inv_axcodes, convert_affine, round-trips
- Orientation: all 48 codes, two-way lookup
- MedImg: slicing preserves metadata, downsampling updates spacing
- Utils: is_nifti/is_dicom, TwoWayDict, explicit_inds edge cases
- Backends: read/write round-trips per backend
- read_save: top-level API with different parameter combinations

## 5. GitHub CI

### `.github/workflows/ci.yml`

Triggers on: PR to any branch, push to main.

Jobs:
1. **lint**: `ruff check` + `ruff format --check`
2. **typecheck**: `ty` (strict)
3. **test**: matrix over Python 3.9/3.10/3.11/3.12, runs pytest

All jobs must pass. Configure branch protection rules on GitHub to require these checks before merge.

### `.github/workflows/release.yml`

Triggers on: tag push matching `v*`.

Jobs:
1. Runs lint + typecheck + test
2. `uv build`
3. Publish to PyPI via trusted publisher (OIDC — no API tokens)

## 6. Additional Items

- Add `numpy` as explicit runtime dependency
- Add `py.typed` marker file
- Add `.python-version` file
- Fix version mismatch (single source in pyproject.toml)
- Drop Python 3.7/3.8 conditional pytest dependency
