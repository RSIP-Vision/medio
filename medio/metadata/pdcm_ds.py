from __future__ import annotations

from pydicom.dataset import FileDataset
from pydicom.valuerep import DSfloat
from typing_extensions import override


def convert_ds(dataset: FileDataset) -> FileDataset | MultiFrameFileDataset:
    """
    Convert a dicom file with shared functional groups sequence into a class which enables shorter access to its
    properties. This is intended primarily for a single dicom file which includes several frames/slices.
    Usage example:
    >>> import pydicom
    >>> ds = pydicom.dcmread('single_dicom_file/I0')
    >>> ds = convert_ds(ds)
    >>> print(ds.PixelSpacing)
    """
    if dataset.get("NumberOfFrames", 1) > 1:
        dataset.__class__ = MultiFrameFileDataset
    return dataset


class MultiFrameFileDataset(FileDataset):
    """This class enables shorter access to basic properties of pydicom dataset of a certain type"""

    @property
    @override
    def ImageOrientationPatient(self) -> list[DSfloat]:  # type: ignore[override]
        return self.SharedFunctionalGroupsSequence[0].PlaneOrientationSequence[0].ImageOrientationPatient

    @property
    @override
    def PixelSpacing(self) -> list[DSfloat]:  # type: ignore[override]
        return self.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].PixelSpacing

    @property
    @override
    def SpacingBetweenSlices(self) -> DSfloat:  # type: ignore[override]
        return self.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].SpacingBetweenSlices

    @property
    @override
    def SliceThickness(self) -> DSfloat:  # type: ignore[override]
        return self.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].SliceThickness

    @property
    @override
    def RescaleIntercept(self) -> DSfloat:  # type: ignore[override]
        return self.SharedFunctionalGroupsSequence[0].PixelValueTransformationSequence[0].RescaleIntercept

    @property
    @override
    def RescaleSlope(self) -> DSfloat:  # type: ignore[override]
        return self.SharedFunctionalGroupsSequence[0].PixelValueTransformationSequence[0].RescaleSlope

    @property
    @override
    def ImagePositionPatient(self) -> list[DSfloat]:  # type: ignore[override]
        """Note: this property returns only the position of the first slice"""
        return self.PerFrameFunctionalGroupsSequence[0].PlanePositionSequence[0].ImagePositionPatient

    def slice_positions(self) -> list[list[DSfloat]]:
        """Return a list of the slices' position"""
        return [seq.PlanePositionSequence[0].ImagePositionPatient for seq in self.PerFrameFunctionalGroupsSequence]

    def slice_position(self, index: int) -> list[DSfloat]:
        """Return the slice position according to the slice index"""
        return self.PerFrameFunctionalGroupsSequence[index].PlanePositionSequence[0].ImagePositionPatient

    def del_intensity_trans(self) -> None:
        """Delete the pixel value transformation sequence from dataset"""
        del self.SharedFunctionalGroupsSequence[0].PixelValueTransformationSequence
