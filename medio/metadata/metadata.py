from __future__ import annotations

import pprint
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Generic, Literal, cast

import numpy as np
from nibabel import aff2axcodes

from medio.metadata.affine import Affine
from medio.metadata.convert_nib_itk import convert_affine, convert_nib_itk, inv_axcodes

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from typing_extensions import Self, TypeVar

    H = TypeVar("H", default=Any, covariant=True)
else:
    from typing import TypeVar

    H = TypeVar("H")

HeaderDict = dict[str, object]
CoordSys = Literal["itk", "nib"]


class MetaData(Generic[H]):
    affine: Affine
    orig_ornt: str | None
    coord_sys: CoordSys
    header: H | None
    spatial_shape: tuple[int, ...] | None
    _ornt: str | None

    def __init__(
        self,
        affine: Affine | NDArray[np.floating],
        orig_ornt: str | None = None,
        coord_sys: CoordSys = "itk",
        header: H | None = None,
        spatial_shape: tuple[int, ...] | None = None,
    ) -> None:
        """
        Initialize medical image's metadata
        :param affine: affine matrix of class Affine, numpy float array of shape (4, 4)
        :param orig_ornt: orientation string code, str of length 3 or None (was not computed because the image was not
        reoriented)
        :param coord_sys: 'itk' or 'nib', the coordinate system of the given affine and orientation: itk or nib (nifti)
        :param header: additional metadata dictionary with string keys
        """
        if not isinstance(affine, Affine):
            affine = Affine(affine)
        self.affine = affine
        self.orig_ornt = orig_ornt
        self._ornt = None
        self.coord_sys = self.check_valid_coord_sys(coord_sys)
        self.header = header
        self.spatial_shape = spatial_shape

    @staticmethod
    def check_valid_coord_sys(coord_sys: str) -> CoordSys:
        if coord_sys not in ("itk", "nib"):
            raise ValueError('Metadata coord_sys must be "itk" or "nib"')
        return cast("CoordSys", coord_sys)

    def __repr__(self) -> str:
        sep = " " if self.header is None else "\n"
        spatial_shape_str = f"\nSpatial shape: {self.spatial_shape}" if self.spatial_shape is not None else ""
        return (
            f"Affine:\n"
            f"{self.affine}\n"
            f"Spacing: {self.spacing}\n"
            f"Coordinate system: {self.coord_sys}\n"
            f"Orientation: {self.ornt}\n"
            f"Original orientation: {self.orig_ornt}"
            f"{spatial_shape_str}\n"
            f"Header:{sep}"
            f"{pprint.pformat(self.header, indent=4)}"
        )

    def convert(self, dest_coord_sys: CoordSys) -> None:
        """
        Converts the metadata coordinate system in-place to dest_coord_sys. Affects affine, ornt and orig_ornt
        :param dest_coord_sys: the destination coordinate system - 'itk' or 'nib' (nifti)
        """
        MetaData.check_valid_coord_sys(dest_coord_sys)  # runtime validation
        if dest_coord_sys != self.coord_sys:
            self.affine, self._ornt, self.orig_ornt = convert_nib_itk(self.affine, self._ornt, self.orig_ornt)
            self.coord_sys = dest_coord_sys

    def clone(self) -> Self:
        cloned = MetaData(
            affine=self.affine.clone(),
            orig_ornt=self.orig_ornt,
            coord_sys=self.coord_sys,
            header=deepcopy(self.header),
            spatial_shape=self.spatial_shape,
        )
        return cloned  # type: ignore[return-value]

    def get_ornt(self) -> str:
        """Returns current orientation based on the affine and coordinate system"""
        if self.coord_sys == "nib":
            return "".join(aff2axcodes(self.affine))
        else:  # "itk"
            return inv_axcodes("".join(aff2axcodes(convert_affine(self.affine))))

    @property
    def ornt(self) -> str:
        if self._ornt is None:
            self._ornt = self.get_ornt()
            # if self.orig_ornt is also None, the affine was not reoriented and the original orientation is the same
            if self.orig_ornt is None:
                self.orig_ornt = self._ornt
        return self._ornt

    @property
    def spacing(self) -> NDArray[np.floating]:
        return self.affine.spacing

    def is_right_handed_ornt(self) -> bool:
        """Check whether the affine orientation is right or left handed. The sign of the triple product of the
        direction matrix is calculated with a determinant. It should be +1 or -1 because it is a rotation matrix.
        +1 (-1) indicates right (left) handed orientation.
        To be used primarily before saving a dicom file or series"""
        if self.affine.dim != 3:
            raise ValueError("Right handed orientation is relevant only to a 3d space")
        return np.linalg.det(self.affine.direction) > 0


def is_right_handed_axcodes(axcodes: str) -> bool:
    if len(axcodes) == 2:
        return True
    if len(axcodes) != 3:
        raise ValueError(f'Invalid axcodes (not length 3 or 2): "{axcodes}"')
    letter_vec_dict = {
        "R": [1, 0, 0],
        "L": [-1, 0, 0],
        "A": [0, 1, 0],
        "P": [0, -1, 0],
        "I": [0, 0, 1],
        "S": [0, 0, -1],
    }
    u, v, n = [letter_vec_dict[letter] for letter in axcodes]
    ornt_sign = np.dot(np.cross(u, v), n)
    if ornt_sign not in (-1, 1):
        raise ValueError(f'Invalid axcodes: "{axcodes}"')
    return ornt_sign == 1


def flip_last_axcodes(axcodes: str) -> str:
    return axcodes[:-1] + inv_axcodes(axcodes[-1])


def check_dcm_ornt(desired_ornt: str | None, metadata: MetaData[Any], allow_dcm_reorient: bool = False) -> str:
    """Check whether the orientation desired_ornt is right handed before saving image as a dicom
    :param desired_ornt: the desired orientation for the saver
    :param metadata: if desired_ornt is None (not set), use metadata.ornt
    :param allow_dcm_reorient: whether to allow automatic reorientation to a right handed orientation or not
    :return: right handed desired_ornt or ValueError
    """
    # first set the desired orientation
    if desired_ornt is None:
        desired_ornt = metadata.ornt
    if is_right_handed_axcodes(desired_ornt):
        return desired_ornt
    else:
        right_handed_ornt = flip_last_axcodes(desired_ornt)
        if allow_dcm_reorient:
            return right_handed_ornt
        else:
            raise ValueError(
                f'The desired orientation "{desired_ornt}" is left handed, whereas saving dicom is '
                f"possible only with a right handed orientation. \nYou can either pass the saver "
                f"parameter allow_dcm_reorient=True to allow automatic reorientation (in this case to "
                f'"{right_handed_ornt}"), or \nreorient yourself before saving the image as a dicom.'
            )
