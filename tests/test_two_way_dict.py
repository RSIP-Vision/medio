from __future__ import annotations

from medio.utils.two_way_dict import TwoWayDict


class TestTwoWayDict:
    def test_setitem_getitem(self) -> None:
        d: TwoWayDict[str, int] = TwoWayDict()
        d["a"] = 1
        assert d["a"] == 1
        assert d[1] == "a"

    def test_len(self) -> None:
        d: TwoWayDict[str, int] = TwoWayDict()
        d["a"] = 1
        d["b"] = 2
        assert len(d) == 2

    def test_delitem(self) -> None:
        d: TwoWayDict[str, int] = TwoWayDict()
        d["a"] = 1
        del d["a"]
        assert "a" not in d
        assert 1 not in d
        assert len(d) == 0

    def test_delitem_reverse(self) -> None:
        d: TwoWayDict[str, int] = TwoWayDict()
        d["a"] = 1
        del d[1]
        assert "a" not in d
        assert 1 not in d

    def test_overwrite_key(self) -> None:
        d: TwoWayDict[str, int] = TwoWayDict()
        d["a"] = 1
        d["a"] = 2
        assert d["a"] == 2
        assert d[2] == "a"
        assert 1 not in d

    def test_overwrite_value(self) -> None:
        d: TwoWayDict[str, int] = TwoWayDict()
        d["a"] = 1
        d["b"] = 1
        assert d["b"] == 1
        assert d[1] == "b"
        assert "a" not in d

    def test_empty(self) -> None:
        d: TwoWayDict[str, int] = TwoWayDict()
        assert len(d) == 0
