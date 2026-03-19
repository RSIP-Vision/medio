from __future__ import annotations

import pytest

from medio.utils.explicit_slicing import explicit_inds


class TestExplicitInds:
    def test_full_slices(self) -> None:
        shape = (10, 20, 30)
        key = (slice(None), slice(None), slice(None))
        start, stop, stride = explicit_inds(key, shape)
        assert start == [0, 0, 0]
        assert stop == [10, 20, 30]
        assert stride == [1, 1, 1]

    def test_integer_index(self) -> None:
        shape = (10, 20, 30)
        key = (5, slice(None), slice(None))
        start, stop, stride = explicit_inds(key, shape)
        assert start == [5, 0, 0]
        assert stop == [6, 20, 30]
        assert stride == [1, 1, 1]

    def test_slice_with_step(self) -> None:
        shape = (10, 20, 30)
        key = (slice(None), slice(2, 18, 3), slice(None))
        start, stop, stride = explicit_inds(key, shape)
        assert start == [0, 2, 0]
        assert stop == [10, 18, 30]
        assert stride == [1, 3, 1]

    def test_ellipsis_at_start(self) -> None:
        shape = (10, 20, 30)
        key = (Ellipsis, slice(5, 25))
        start, stop, stride = explicit_inds(key, shape)
        assert start == [0, 0, 5]
        assert stop == [10, 20, 25]
        assert stride == [1, 1, 1]

    def test_ellipsis_in_middle(self) -> None:
        shape = (10, 20, 30)
        key = (2, Ellipsis, slice(0, 10))
        start, stop, stride = explicit_inds(key, shape)
        assert start == [2, 0, 0]
        assert stop == [3, 20, 10]
        assert stride == [1, 1, 1]

    def test_negative_slice(self) -> None:
        shape = (10, 20, 30)
        key = (slice(None), slice(None), slice(2, -2))
        start, stop, stride = explicit_inds(key, shape)
        assert start == [0, 0, 2]
        assert stop == [10, 20, 28]
        assert stride == [1, 1, 1]

    def test_downsampling(self) -> None:
        shape = (100, 200, 300)
        key = (slice(None, None, 2), slice(None, None, 3), slice(None, None, 5))
        start, stop, stride = explicit_inds(key, shape)
        assert start == [0, 0, 0]
        assert stop == [100, 200, 300]
        assert stride == [2, 3, 5]

    def test_unsupported_key_raises(self) -> None:
        shape = (10, 20, 30)
        key = ([1, 2, 3], slice(None), slice(None))
        with pytest.raises(NotImplementedError):
            explicit_inds(key, shape)
