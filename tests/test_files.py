from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from medio.utils.files import is_dicom, is_nifti, make_dir, make_empty_dir


class TestIsNifti:
    def test_nii_gz(self, tmp_path: Path) -> None:
        f = tmp_path / "test.nii.gz"
        f.write_bytes(b"")
        assert is_nifti(f)

    def test_nii(self, tmp_path: Path) -> None:
        f = tmp_path / "test.nii"
        f.write_bytes(b"")
        assert is_nifti(f)

    def test_hdr(self, tmp_path: Path) -> None:
        f = tmp_path / "test.hdr"
        f.write_bytes(b"")
        assert is_nifti(f)

    def test_dcm_not_nifti(self, tmp_path: Path) -> None:
        f = tmp_path / "test.dcm"
        f.write_bytes(b"")
        assert not is_nifti(f)

    def test_no_exist_check(self) -> None:
        assert is_nifti("/nonexistent/file.nii.gz", check_exist=False)

    def test_nonexistent_file(self) -> None:
        assert not is_nifti("/nonexistent/file.nii.gz", check_exist=True)


class TestIsDicom:
    def test_dcm(self, tmp_path: Path) -> None:
        f = tmp_path / "test.dcm"
        f.write_bytes(b"")
        assert is_dicom(f)

    def test_dicom(self, tmp_path: Path) -> None:
        f = tmp_path / "test.dicom"
        f.write_bytes(b"")
        assert is_dicom(f)

    def test_nii_not_dicom(self, tmp_path: Path) -> None:
        f = tmp_path / "test.nii.gz"
        f.write_bytes(b"")
        assert not is_dicom(f)

    def test_no_exist_check(self) -> None:
        assert is_dicom("/nonexistent/file.dcm", check_exist=False)


class TestMakeDir:
    def test_make_empty_dir(self, tmp_path: Path) -> None:
        d = tmp_path / "newdir"
        make_empty_dir(d)
        assert d.is_dir()

    def test_make_empty_dir_already_empty(self, tmp_path: Path) -> None:
        d = tmp_path / "newdir"
        d.mkdir()
        make_empty_dir(d)  # should not raise
        assert d.is_dir()

    def test_make_empty_dir_not_empty(self, tmp_path: Path) -> None:
        d = tmp_path / "newdir"
        d.mkdir()
        (d / "file.txt").write_text("content")
        with pytest.raises(FileExistsError):
            make_empty_dir(d)

    def test_make_dir_exist_ok(self, tmp_path: Path) -> None:
        d = tmp_path / "newdir"
        d.mkdir()
        (d / "file.txt").write_text("content")
        make_dir(d, exist_ok=True)  # should not raise

    def test_make_dir_parents(self, tmp_path: Path) -> None:
        d = tmp_path / "a" / "b" / "c"
        make_dir(d, parents=True)
        assert d.is_dir()
