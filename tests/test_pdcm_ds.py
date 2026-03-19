from __future__ import annotations

import pydicom
import pydicom.dataset

from medio.metadata.pdcm_ds import MultiFrameFileDataset, convert_ds


def _make_file_dataset(num_frames: int) -> pydicom.dataset.FileDataset:
    """Create a minimal FileDataset compatible with pydicom 2.x and 3.x."""
    ds = pydicom.Dataset()
    ds.NumberOfFrames = num_frames
    file_meta = pydicom.dataset.FileMetaDataset()
    return pydicom.dataset.FileDataset("test", ds, file_meta=file_meta)


class TestConvertDs:
    def test_single_frame_unchanged(self) -> None:
        fds = _make_file_dataset(1)
        result = convert_ds(fds)
        assert result.__class__ is pydicom.dataset.FileDataset

    def test_multi_frame_converted(self) -> None:
        fds = _make_file_dataset(5)
        result = convert_ds(fds)
        assert isinstance(result, MultiFrameFileDataset)
