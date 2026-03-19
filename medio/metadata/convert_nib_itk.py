"""
NiBabel <-> ITK orientation and affine conversion utilities.
The conventions of nibabel and itk are different and this module supplies functions which convert between
these conventions.

Orientation
-----------
In nibabel each axis code indicates the ending direction - RAS+: L -> R, P -> A, I -> S
In itk it corresponds to the converse of nibabel - RAS: R -> L, A -> P, S -> I

Affine
------
In itk, the direction matrix (3x3 upper left affine with unit spacings) of RAS orientation image is:
[[1, 0, 0],
 [0, 1, 0],
 [0, 0, -1]]

In nibabel it is LPI+:
[[-1, 0, 0],
 [0, -1, 0],
 [0, 0, -1]]

The matrix convert_aff_mat accounts for this difference (for all possible orientations, not only RAS).

Usage
=====
Works both ways: itk -> nib and nib -> itk, the usage is the same:
>>> new_affine, new_axcodes = convert_nib_itk(affine, axcodes)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

import numpy as np
from numpy.typing import NDArray
from typing_extensions import TypeVar, TypeVarTuple, Unpack

from medio.metadata.affine import Affine
from medio.utils.two_way_dict import TwoWayDict

# store compactly axis directions codes
axes_inv = TwoWayDict()
axes_inv["R"] = "L"
axes_inv["A"] = "P"
axes_inv["S"] = "I"


@overload
def inv_axcodes(axcodes: str) -> str: ...


@overload
def inv_axcodes(axcodes: None) -> None: ...


@overload
def inv_axcodes(axcodes: str | None) -> str | None: ...


def inv_axcodes(axcodes: str | None) -> str | None:
    """Inverse axes codes chars, for example: SPL -> IAR"""
    if axcodes is None:
        return None
    new_axcodes = ""
    for code in axcodes:
        new_axcodes += axes_inv[code]
    return new_axcodes


AffineOrNdarray = TypeVar("AffineOrNdarray", Affine, NDArray[np.floating])


def convert_affine(affine: AffineOrNdarray) -> AffineOrNdarray:
    # conversion matrix of the affine from itk to nibabel and vice versa
    convert_aff_mat = np.diag([-1, -1, 1, 1])
    # for 2d image:
    if affine.shape[0] == 3:
        convert_aff_mat = np.diag([-1, -1, 1])
    new_affine = convert_aff_mat @ affine
    if isinstance(affine, Affine):
        return Affine(new_affine)
    return new_affine


VariadicAxCodes = TypeVarTuple("VariadicAxCodes")


if TYPE_CHECKING:
    import collections.abc as cx
    from typing import Any, Protocol

    F = TypeVar("F", bound=cx.Callable[..., Any])

    class _ConvertNibItkFunc(Protocol):
        def __call__(self, affine: AffineOrNdarray, *axcodes: str | None) -> Any: ...

    def _type_check_axcodes(f: F, /) -> F | _ConvertNibItkFunc:
        """Decorate a function to make it only accept variadic positional `axcodes` arguments of type `str` or `None`"""
        return f
else:

    def _type_check_axcodes(f, /):
        return f


@_type_check_axcodes
def convert_nib_itk(
    affine: AffineOrNdarray, *axcodes: Unpack[VariadicAxCodes]
) -> tuple[AffineOrNdarray, Unpack[VariadicAxCodes]]:
    """Convert affine and orientations (original and current orientations) from nibabel to itk and vice versa"""
    new_affine = convert_affine(affine)
    new_axcodes = []
    for axcode in axcodes:
        new_axcodes += [inv_axcodes(axcode)]

    return (new_affine, *new_axcodes)
