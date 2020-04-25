"""
This module is based on the C++ ITK code - itkSpatialOrientation.h
"""

import itertools
from enum import IntEnum

from medio.utils.two_way_dict import TwoWayDict


class AxCodes(IntEnum):
    UNKNOWN = 0
    R = 2  # Right
    L = 3  # Left
    P = 4  # Posterior
    A = 5  # Anterior
    I = 8  # Inferior
    S = 9  # Superior


class AxMajorness(IntEnum):
    Primary = 0
    Secondary = 8
    Tertiary = 16


class ItkOrientationCode:
    INVALID = AxCodes.UNKNOWN
    # 48 valid orientations are added as attributes


def itk_orientation_code(ax_code):
    """ax_code is string or tuple of valid orientation, e.g. 'LPI', ('A', 'R', 'S')"""
    prime, second, tertiary = [getattr(AxCodes, axis) for axis in ax_code]
    return (prime << AxMajorness.Primary) + (second << AxMajorness.Secondary) + (tertiary << AxMajorness.Tertiary)


# adding all 48 possible orientation codes to ItkOrientationCode class

ax_codes_iter = itertools.chain(
    *map(itertools.permutations,
         itertools.product(('R', 'L'), ('A', 'P'), ('I', 'S'))
         ))

# two way dictionary that translates itk numerical orientation codes to orientation strings and vice versa
codes_str_dict = TwoWayDict()
codes_str_dict[None] = None

for ax_code in ax_codes_iter:
    ax_code_str = ''.join(ax_code)
    code = itk_orientation_code(ax_code)
    setattr(ItkOrientationCode, ax_code_str, code)
    codes_str_dict[ax_code_str] = code
