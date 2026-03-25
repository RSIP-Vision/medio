[![Python version](https://img.shields.io/pypi/pyversions/medio.svg)](https://pypi.org/project/medio)
[![PyPI version](https://badge.fury.io/py/medio.svg)](https://badge.fury.io/py/medio)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/RSIP-Vision/medio/blob/main/LICENSE)

# medio

**Medical image I/O for Python — read and write NIfTI, DICOM, MetaImage, and more in one consistent API.**

- One function reads any format; format auto-detected from path
- Returns a NumPy array + rich `MetaData` (affine, orientation, spacing) — no format-specific objects to unwrap
- Transparent coordinate system normalization between ITK and NiBabel conventions
- Metadata-only reads (`read_meta`) for large files when you only need spatial info

## Installation

```bash
pip install medio
```

## Usage

### Read and save any format

```python
import medio

arr, meta = medio.read_img('scan.nii.gz')
print(meta.ornt, meta.spacing)   # e.g. 'LPI', [0.5, 0.5, 1.0]

medio.save_img('out.mhd', arr, meta)
```

### Read metadata only — no pixel data loaded

```python
meta = medio.read_meta('large_scan.nii.gz')
print(meta.spatial_shape)    # (256, 256, 128)
print(meta.affine.spacing)   # [0.98, 0.98, 1.5]
```

### Reorient to a standard orientation

```python
arr, meta = medio.read_img('scan.nii.gz', desired_ornt='RAS')
# arr axes are reordered; meta.affine updated to match
```

### Write a DICOM series from a 3D array

```python
arr, meta = medio.read_img('scan.mhd')
medio.save_dir('dicom_out/', arr, meta)
```

### Spatial slicing with automatic affine update

```python
from medio.medimg import MedImg

mimg = MedImg(arr, meta)
cropped      = mimg[2:8, 3:7, :]    # origin updated
downsampled  = mimg[::2, ::2, ::1]  # spacing updated
```

---

## Supported Formats

| Format | Extensions | Default backend |
|--------|------------|-----------------|
| NIfTI | `.nii`, `.nii.gz` | ITK |
| DICOM | directory or `.dcm` | ITK |
| MetaImage | `.mhd`, `.mha` | ITK |
| NIfTI (NiBabel) | `.nii`, `.nii.gz` | `backend='nib'` |
| DICOM (pydicom) | `.dcm` | `backend='pdcm'` |
| Other ITK formats | `.png`, `.jpg`, … | ITK |

---

## API Reference

### `read_img`

```python
medio.read_img(input_path, desired_ornt=None, backend=None, dtype=None,
               header=False, channels_axis=-1, coord_sys='itk', **kwargs)
→ tuple[np.ndarray, MetaData]
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_path` | path-like | — | File or DICOM directory |
| `desired_ornt` | str \| None | `None` | Reorient to this axis code (e.g. `'RAS'`) |
| `backend` | str \| None | `None` | Force backend: `'itk'`, `'nib'`, `'pdcm'` |
| `dtype` | dtype \| None | `None` | Cast array to this dtype |
| `header` | bool | `False` | Include raw format header in `MetaData.header` |
| `channels_axis` | int \| None | `-1` | Axis for multi-channel (e.g. RGB) images |
| `coord_sys` | `'itk'` \| `'nib'` \| None | `'itk'` | Coordinate convention for orientation and metadata |

`**kwargs` are passed to the backend. ITK-specific: `pixel_type`, `fallback_only`, `series`. pydicom-specific: `globber`, `allow_default_affine`, `series`.

---

### `read_meta`

```python
medio.read_meta(input_path, desired_ornt=None, backend=None,
                header=False, coord_sys='itk', **kwargs)
→ MetaData
```

See `read_img` for parameters. Reads only spatial metadata without loading pixel data.

---

### `save_img`

```python
medio.save_img(filename, np_image, metadata, use_original_ornt=True,
               backend=None, dtype=None, channels_axis=None,
               mkdir=False, parents=False, **kwargs)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filename` | path-like | — | Output file path (format inferred from suffix) |
| `np_image` | ndarray | — | Image array |
| `metadata` | MetaData | — | Spatial metadata |
| `use_original_ornt` | bool | `True` | Reorient to `metadata.orig_ornt` before saving |
| `backend` | str \| None | `None` | Force backend: `'itk'` or `'nib'` |
| `dtype` | dtype \| None | `None` | Cast before saving |
| `channels_axis` | int \| None | `None` | Axis of channel dimension in `np_image` |
| `mkdir` | bool | `False` | Create the output directory if it doesn't exist |
| `parents` | bool | `False` | Create all missing parent directories |


---

### `save_dir`

```python
medio.save_dir(dirname, np_image, metadata, use_original_ornt=True,
               dtype=None, channels_axis=None, parents=False,
               exist_ok=False, allow_dcm_reorient=False, **kwargs)
```

Saves a 3D array as a DICOM series of 2D slices.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `dirname` | — | Output directory |
| `exist_ok` | `False` | Allow writing into an existing non-empty directory |
| `allow_dcm_reorient` | `False` | Reorient to nearest right-handed orientation if needed |
| `pattern` | `'IM{}.dcm'` | Filename pattern; `{}` is replaced with the slice number |
| `metadata_dict` | `None` | Override or add DICOM tags, e.g. `{'0008\|0060': 'US'}` |

---

### `MetaData`

```python
medio.MetaData(affine, coord_sys='itk', orig_ornt=None, header=None, spatial_shape=None)
```

| Property | Type | Description |
|----------|------|-------------|
| `affine` | `Affine` | 4×4 spatial transform (index space → physical space) |
| `coord_sys` | str | `'itk'` or `'nib'` |
| `ornt` | str | Current orientation code (e.g. `'LPI'`), derived from affine |
| `orig_ornt` | str | Orientation before any reorientation |
| `spacing` | ndarray | Voxel spacing — alias for `affine.spacing` |
| `header` | dict \| None | Raw format header (populated when `header=True` in `read_img`) |
| `spatial_shape` | tuple \| None | Image dimensions (populated by `read_meta`) |

Methods: `.convert(dest_coord_sys)` — in-place convention switch; `.clone()` — deep copy.

---

### `Affine`

A 4×4 NumPy array subclass with named spatial accessors.

```python
from medio import Affine
import numpy as np

aff = Affine(np.eye(4))
aff = Affine(direction=np.eye(3), spacing=[0.5, 0.5, 1.0], origin=[0., 0., 0.])
coord = aff.index2coord([4, 0, 9])   # map voxel index → physical coordinate
```

Properties: `.spacing`, `.origin`, `.direction` (all gettable and settable). Method: `.clone()`.

For a mathematical background see [NiBabel's affine documentation](https://nipy.org/nibabel/coordinate_systems.html#the-affine-matrix-as-a-transformation-between-spaces).

---

### `MedImg`

Container for an image array + metadata with spatially-aware indexing.

```python
from medio.medimg.medimg import MedImg

mimg = MedImg(arr, meta)                         # from array + metadata
mimg = MedImg.from_file('scan.mhd')   # load from file
```

Indexing crops or downsamples the array and updates the affine automatically:

| Indexing | Effect on metadata |
|----------|--------------------|
| `mimg[2:8, 3:7, :]` | origin updated to new start voxel |
| `mimg[::2, ::2, ::1]` | spacing scaled by step sizes |
| `mimg[..., 5:15]` | ellipsis supported |

Properties: `.np_image`, `.metadata`. Method: `.save(filename)`.

---

### Orientation conventions

medio uses **ITK convention** by default (`coord_sys='itk'`). 
Pass `coord_sys='nib'` to `read_img` / `read_meta` to work in NiBabel convention throughout.

---

## License

Apache 2.0 — see [LICENSE](https://github.com/RSIP-Vision/medio/blob/main/LICENSE).

Issues and contributions: [github.com/RSIP-Vision/medio/issues](https://github.com/RSIP-Vision/medio/issues)
