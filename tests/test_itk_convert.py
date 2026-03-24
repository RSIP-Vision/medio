from __future__ import annotations

import itk
import numpy as np

from medio.backends.itk_io import ItkIO
from medio.metadata.affine import Affine
from medio.metadata.convert_nib_itk import inv_axcodes
from medio.metadata.metadata import MetaData
from medio.read_save import read_img


class TestFromItkImg:
    def test_array_matches_read_img(self, nii_path) -> None:
        """from_itk_img returns same array as read_img for the same file."""
        np_ref, _ = read_img(nii_path)
        itk_img = itk.imread(str(nii_path))
        np_img, _ = ItkIO.from_itk_img(itk_img)
        np.testing.assert_array_equal(np_img, np_ref)

    def test_affine_matches_read_img(self, nii_path) -> None:
        """from_itk_img returns same affine as read_img for the same file."""
        _, meta_ref = read_img(nii_path)
        itk_img = itk.imread(str(nii_path))
        _, meta = ItkIO.from_itk_img(itk_img)
        np.testing.assert_allclose(meta.affine, meta_ref.affine, atol=1e-5)

    def test_default_coord_sys_is_itk(self, nii_path) -> None:
        """Default coord_sys is 'itk'."""
        itk_img = itk.imread(str(nii_path))
        _, meta = ItkIO.from_itk_img(itk_img)
        assert meta.coord_sys == "itk"

    def test_coord_sys_nib(self, nii_path) -> None:
        """coord_sys='nib' returns nibabel-convention metadata."""
        itk_img = itk.imread(str(nii_path))
        _, meta = ItkIO.from_itk_img(itk_img, coord_sys="nib")
        assert meta.coord_sys == "nib"

    def test_desired_ornt_itk_convention(self, nii_path) -> None:
        """desired_ornt in ITK convention is applied and ornt reflects it."""
        itk_img = itk.imread(str(nii_path))
        _, meta = ItkIO.from_itk_img(itk_img, desired_ornt="LPI", coord_sys="itk")
        assert meta.ornt == "LPI"

    def test_desired_ornt_nib_convention(self, nii_path) -> None:
        """When coord_sys='nib', desired_ornt is in NiBabel convention."""
        itk_img = itk.imread(str(nii_path))
        # 'RAS' in nibabel == 'LPI' in itk
        _, meta = ItkIO.from_itk_img(itk_img, desired_ornt="RAS", coord_sys="nib")
        assert meta.coord_sys == "nib"
        assert meta.ornt == "RAS"

    def test_nib_and_itk_ornt_are_inverses(self, nii_path) -> None:
        """Orientation reported in nib and itk mode are inverses of each other."""
        itk_img = itk.imread(str(nii_path))
        _, meta_itk = ItkIO.from_itk_img(itk_img, coord_sys="itk")
        _, meta_nib = ItkIO.from_itk_img(itk_img, coord_sys="nib")
        assert meta_nib.ornt == inv_axcodes(meta_itk.ornt)

    def test_coord_sys_none_returns_itk_convention(self, nii_path) -> None:
        """coord_sys=None skips conversion and returns ITK convention."""
        itk_img = itk.imread(str(nii_path))
        _, meta_none = ItkIO.from_itk_img(itk_img, coord_sys=None)
        _, meta_itk = ItkIO.from_itk_img(itk_img, coord_sys="itk")
        np.testing.assert_array_equal(meta_none.affine, meta_itk.affine)
        assert meta_none.coord_sys == "itk"

    def test_original_itk_image_not_mutated(self, nii_path) -> None:
        """Reorientation inside from_itk_img must not mutate the source itk.Image."""
        itk_img = itk.imread(str(nii_path))
        orig_dir = itk.array_from_vnl_matrix(itk_img.GetDirection().GetVnlMatrix().as_matrix()).copy()
        orig_origin = np.array(itk_img.GetOrigin()).copy()
        ItkIO.from_itk_img(itk_img, desired_ornt="LPI")
        new_dir = itk.array_from_vnl_matrix(itk_img.GetDirection().GetVnlMatrix().as_matrix())
        new_origin = np.array(itk_img.GetOrigin())
        np.testing.assert_array_equal(orig_dir, new_dir)
        np.testing.assert_array_equal(orig_origin, new_origin)

    def test_orig_ornt_preserved_after_reorientation(self, nii_path) -> None:
        """orig_ornt holds the pre-reorientation orientation."""
        itk_img = itk.imread(str(nii_path))
        _, meta_default = ItkIO.from_itk_img(itk_img)
        orig_ornt = meta_default.ornt
        _, meta_reoriented = ItkIO.from_itk_img(itk_img, desired_ornt="LPI")
        assert meta_reoriented.orig_ornt == orig_ornt


class TestToItkImg:
    def test_array_values_preserved(self, nii_path) -> None:
        """to_itk_img embeds the numpy array correctly."""
        np_img, meta = read_img(nii_path)
        itk_img = ItkIO.to_itk_img(np_img, meta)
        result = ItkIO.itk_img_to_array(itk_img)
        np.testing.assert_array_equal(np_img, result)

    def test_affine_applied_correctly(self, nii_path) -> None:
        """to_itk_img sets spacing, origin, and direction from the affine."""
        np_img, meta = read_img(nii_path)
        itk_img = ItkIO.to_itk_img(np_img, meta)
        result_affine = ItkIO.get_img_aff(itk_img)
        np.testing.assert_allclose(result_affine, meta.affine, atol=1e-5)

    def test_does_not_mutate_metadata(self, nii_path) -> None:
        """to_itk_img never modifies the caller's MetaData object."""
        np_img, meta = read_img(nii_path)
        orig_coord_sys = meta.coord_sys
        orig_affine = meta.affine.copy()
        ItkIO.to_itk_img(np_img, meta)
        assert meta.coord_sys == orig_coord_sys
        np.testing.assert_array_equal(meta.affine, orig_affine)

    def test_works_with_nib_coord_sys(self, nii_path) -> None:
        """to_itk_img correctly converts a nib-convention MetaData to ITK affine."""
        np_img, meta_nib = read_img(nii_path, coord_sys="nib")
        assert meta_nib.coord_sys == "nib"
        itk_img = ItkIO.to_itk_img(np_img, meta_nib)
        meta_itk = meta_nib.clone()
        meta_itk.convert("itk")
        result_affine = ItkIO.get_img_aff(itk_img)
        np.testing.assert_allclose(result_affine, meta_itk.affine, atol=1e-5)

    def test_returns_itk_image_with_spatial_interface(self, nii_path) -> None:
        """Return value is a valid ITK image with spatial attribute methods."""
        np_img, meta = read_img(nii_path)
        itk_img = ItkIO.to_itk_img(np_img, meta)
        assert hasattr(itk_img, "GetSpacing")
        assert hasattr(itk_img, "GetDirection")
        assert hasattr(itk_img, "GetOrigin")

    def test_synthetic_image(self) -> None:
        """Works with a fully synthetic array and Affine (no files)."""
        arr = np.arange(24, dtype=np.int16).reshape(2, 3, 4)
        aff = Affine(direction=np.eye(3), spacing=[1.0, 2.0, 3.0], origin=[10.0, 20.0, 30.0])
        meta = MetaData(aff, coord_sys="itk")
        itk_img = ItkIO.to_itk_img(arr, meta)
        result = ItkIO.itk_img_to_array(itk_img)
        np.testing.assert_array_equal(arr, result)
        result_aff = ItkIO.get_img_aff(itk_img)
        np.testing.assert_allclose(result_aff.spacing, [1.0, 2.0, 3.0], atol=1e-6)
        np.testing.assert_allclose(result_aff.origin, [10.0, 20.0, 30.0], atol=1e-6)


class TestComponentsAxis:
    def test_from_itk_img_moves_components_to_requested_axis(self) -> None:
        """from_itk_img moves vector image components to the requested axis."""
        # arr shape: (components=3, x=2, y=3, z=4) — components at DEFAULT_COMPONENTS_AXIS=0
        arr = np.arange(72, dtype=np.uint8).reshape(3, 2, 3, 4)
        itk_img = itk.image_from_array(arr.T.copy(), is_vector=True)
        np_img, _ = ItkIO.from_itk_img(itk_img, components_axis=-1)
        assert np_img.shape == (2, 3, 4, 3)
        assert np_img.shape[-1] == 3

    def test_to_itk_img_and_from_itk_img_components_roundtrip(self) -> None:
        """medio -> ITK -> medio preserves vector image data with components_axis."""
        arr = np.arange(72, dtype=np.uint8).reshape(2, 3, 4, 3)  # components last
        aff = Affine(direction=np.eye(3), spacing=[1.0, 1.0, 1.0], origin=[0.0, 0.0, 0.0])
        meta = MetaData(aff, coord_sys="itk")
        itk_img = ItkIO.to_itk_img(arr, meta, components_axis=-1)
        result, _ = ItkIO.from_itk_img(itk_img, components_axis=-1)
        np.testing.assert_array_equal(arr, result)


class TestRoundtrip:
    def test_itk_to_medio_to_itk_array(self, nii_path) -> None:
        """ITK -> medio -> ITK preserves voxel data."""
        itk_orig = itk.imread(str(nii_path))
        np_img, meta = ItkIO.from_itk_img(itk_orig)
        itk_rt = ItkIO.to_itk_img(np_img, meta)
        np.testing.assert_array_equal(
            ItkIO.itk_img_to_array(itk_orig),
            ItkIO.itk_img_to_array(itk_rt),
        )

    def test_itk_to_medio_to_itk_affine(self, nii_path) -> None:
        """ITK -> medio -> ITK preserves spatial metadata."""
        itk_orig = itk.imread(str(nii_path))
        np_img, meta = ItkIO.from_itk_img(itk_orig)
        itk_rt = ItkIO.to_itk_img(np_img, meta)
        np.testing.assert_allclose(
            ItkIO.get_img_aff(itk_orig),
            ItkIO.get_img_aff(itk_rt),
            atol=1e-5,
        )

    def test_medio_to_itk_to_medio_array(self, nii_path) -> None:
        """medio -> ITK -> medio preserves voxel data."""
        np_orig, meta = read_img(nii_path)
        itk_img = ItkIO.to_itk_img(np_orig, meta)
        np_rt, _ = ItkIO.from_itk_img(itk_img)
        np.testing.assert_array_equal(np_orig, np_rt)

    def test_medio_to_itk_to_medio_affine(self, nii_path) -> None:
        """medio -> ITK -> medio preserves the affine."""
        np_orig, meta = read_img(nii_path)
        itk_img = ItkIO.to_itk_img(np_orig, meta)
        _, meta_rt = ItkIO.from_itk_img(itk_img)
        np.testing.assert_allclose(meta.affine, meta_rt.affine, atol=1e-5)

    def test_roundtrip_with_nib_coord_sys(self, nii_path) -> None:
        """Round-trip starting from nib-convention metadata."""
        np_orig, meta_nib = read_img(nii_path, coord_sys="nib")
        itk_img = ItkIO.to_itk_img(np_orig, meta_nib)
        np_rt, meta_rt = ItkIO.from_itk_img(itk_img, coord_sys="nib")
        np.testing.assert_array_equal(np_orig, np_rt)
        np.testing.assert_allclose(meta_nib.affine, meta_rt.affine, atol=1e-5)
