from __future__ import annotations

import numpy as np

from medio.metadata.affine import Affine


class TestAffineConstruction:
    def test_from_matrix(self) -> None:
        aff = Affine(np.eye(4))
        assert aff.shape == (4, 4)
        np.testing.assert_array_equal(aff, np.eye(4))

    def test_from_components(self) -> None:
        direction = np.eye(3)
        spacing = [0.5, 1.0, 2.0]
        origin = [10.0, 20.0, 30.0]
        aff = Affine(direction=direction, spacing=spacing, origin=origin)
        assert aff.shape == (4, 4)
        np.testing.assert_array_almost_equal(aff.origin, [10.0, 20.0, 30.0])
        np.testing.assert_array_almost_equal(aff.spacing, [0.5, 1.0, 2.0])

    def test_dim(self) -> None:
        aff = Affine(np.eye(4))
        assert aff.dim == 3

    def test_dim_2d(self) -> None:
        aff = Affine(np.eye(3))
        assert aff.dim == 2


class TestAffineDecomposition:
    def test_spacing(self) -> None:
        direction = np.eye(3)
        spacing = np.array([0.33, 1.0, 0.33])
        origin = np.array([-90.3, 10.0, 1.44])
        aff = Affine(direction=direction, spacing=spacing, origin=origin)
        np.testing.assert_array_almost_equal(aff.spacing, spacing)

    def test_direction(self) -> None:
        direction = np.eye(3)
        aff = Affine(direction=direction, spacing=[1, 1, 1], origin=[0, 0, 0])
        np.testing.assert_array_almost_equal(aff.direction, direction)

    def test_origin(self) -> None:
        origin = np.array([1.5, -2.5, 3.5])
        aff = Affine(direction=np.eye(3), spacing=[1, 1, 1], origin=origin)
        np.testing.assert_array_almost_equal(aff.origin, origin)

    def test_affine2comps_roundtrip(self) -> None:
        direction = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], dtype=float)
        spacing = np.array([0.5, 0.5, 1.0])
        origin = np.array([10.0, 20.0, 30.0])
        aff = Affine(direction=direction, spacing=spacing, origin=origin)
        d, s, o = Affine.affine2comps(aff)
        np.testing.assert_array_almost_equal(d, direction)
        np.testing.assert_array_almost_equal(s, spacing)
        np.testing.assert_array_almost_equal(o, origin)


class TestIndex2Coord:
    def test_identity(self) -> None:
        aff = Affine(np.eye(4))
        coord = aff.index2coord([3, 4, 5])
        np.testing.assert_array_almost_equal(coord, [3, 4, 5])

    def test_with_spacing_and_origin(self) -> None:
        aff = Affine(direction=np.eye(3), spacing=[0.33, 1, 0.33], origin=[-90.3, 10, 1.44])
        coord = aff.index2coord([4, 0, 9])
        np.testing.assert_array_almost_equal(coord, [-88.98, 10.0, 4.41])


class TestClone:
    def test_clone_is_independent(self) -> None:
        aff = Affine(np.eye(4))
        clone = aff.clone()
        clone.origin = [1, 2, 3]
        np.testing.assert_array_equal(aff.origin, [0, 0, 0])

    def test_clone_values_match(self) -> None:
        aff = Affine(direction=np.eye(3), spacing=[2, 3, 4], origin=[5, 6, 7])
        clone = aff.clone()
        np.testing.assert_array_almost_equal(clone.spacing, aff.spacing)
        np.testing.assert_array_almost_equal(clone.origin, aff.origin)


class TestSpacingSetter:
    def test_set_spacing(self) -> None:
        aff = Affine(direction=np.eye(3), spacing=[1, 1, 1], origin=[0, 0, 0])
        aff.spacing = np.array([2, 3, 4])
        np.testing.assert_array_almost_equal(aff.spacing, [2, 3, 4])

    def test_set_spacing_preserves_direction(self) -> None:
        direction = np.eye(3)
        aff = Affine(direction=direction, spacing=[1, 1, 1], origin=[0, 0, 0])
        aff.spacing = np.array([2, 2, 2])
        np.testing.assert_array_almost_equal(aff.direction, direction)


class TestDirectionSetter:
    def test_set_direction(self) -> None:
        aff = Affine(direction=np.eye(3), spacing=[1, 1, 1], origin=[0, 0, 0])
        new_dir = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], dtype=float)
        aff.direction = new_dir
        np.testing.assert_array_almost_equal(aff.direction, new_dir)


class TestMatmul:
    def test_matmul_returns_ndarray(self) -> None:
        aff = Affine(np.eye(4))
        result = aff @ np.ones(4)
        assert type(result) is np.ndarray


class TestGetitem:
    def test_getitem_returns_ndarray(self) -> None:
        aff = Affine(np.eye(4))
        # Row slicing should return plain np.ndarray, not Affine
        result = aff[0]
        assert type(result) is np.ndarray
        np.testing.assert_array_equal(result, [1.0, 0.0, 0.0, 0.0])
