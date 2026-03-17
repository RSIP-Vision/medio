from __future__ import annotations

from medio.metadata.itk_orientation import (
    AxCodes,
    ItkOrientationCode,
    codes_str_dict,
    itk_orientation_code,
)


class TestItkOrientationCode:
    def test_known_code(self) -> None:
        code = itk_orientation_code("RAS")
        assert isinstance(code, int)
        assert code == ItkOrientationCode.RAS  # type: ignore[attr-defined]

    def test_tuple_input(self) -> None:
        code = itk_orientation_code(("L", "P", "I"))
        assert code == ItkOrientationCode.LPI  # type: ignore[attr-defined]

    def test_all_48_codes(self) -> None:
        # There should be 48 valid orientations + None mapping
        assert len(codes_str_dict) >= 48

    def test_two_way_lookup(self) -> None:
        code = itk_orientation_code("RAS")
        assert codes_str_dict["RAS"] == code
        assert codes_str_dict[code] == "RAS"

    def test_codes_str_dict_none(self) -> None:
        assert codes_str_dict[None] is None

    def test_all_codes_unique(self) -> None:
        codes = []
        for key in codes_str_dict:
            if isinstance(key, str):
                codes.append(codes_str_dict[key])
        assert len(codes) == len(set(codes))

    def test_invalid_attribute(self) -> None:
        assert ItkOrientationCode.INVALID == AxCodes.UNKNOWN
