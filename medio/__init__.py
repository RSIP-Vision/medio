from __future__ import annotations

from importlib.metadata import version

from medio.backends.itk_io import ItkIO
from medio.medimg import MedImg
from medio.metadata.affine import Affine
from medio.metadata.metadata import CoordSys, MetaData
from medio.read_save import read_img, read_meta, save_dir, save_img

__version__ = version("medio")

__all__ = [
    "Affine",
    "CoordSys",
    "ItkIO",
    "MedImg",
    "MetaData",
    "__version__",
    "read_img",
    "read_meta",
    "save_dir",
    "save_img",
]
