from pydicom.dataset import FileDataset


def convert_ds(dataset):
    """
    Convert a dicom file with shared functional groups sequence into a class which enables shorter access to its
    properties. This is intended primarily for a single dicom file which includes several frames/slices.
    Usage example:
    >>> ds = pydicom.dcmread('single_dicom_file/I0')
    >>> ds = convert_ds(ds)
    >>> print(ds.PixelSpacing)
    """
    if hasattr(dataset, 'SharedFunctionalGroupsSequence') and len(dataset.SharedFunctionalGroupsSequence) > 0:
        dataset.__class__ = FramedFileDataset
    return dataset


class FramedFileDataset(FileDataset):
    """This class enables shorter access to basic properties of pydicom dataset of a certain type"""
    @property
    def ImageOrientationPatient(self):
        return self.SharedFunctionalGroupsSequence[0].PlaneOrientationSequence[0].ImageOrientationPatient

    @property
    def PixelSpacing(self):
        return self.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].PixelSpacing

    @property
    def SliceThickness(self):
        return self.SharedFunctionalGroupsSequence[0].PixelMeasuresSequence[0].SliceThickness

    @property
    def RescaleIntercept(self):
        return self.SharedFunctionalGroupsSequence[0].PixelValueTransformationSequence[0].RescaleIntercept

    @property
    def RescaleSlope(self):
        return self.SharedFunctionalGroupsSequence[0].PixelValueTransformationSequence[0].RescaleSlope

    @property
    def ImagePositionPatient(self):
        """Note: this property returns only the position of the first slice"""
        return self.PerFrameFunctionalGroupsSequence[0].PlanePositionSequence[0].ImagePositionPatient

    def slice_positions(self):
        """Return a list of the slices' position"""
        return [seq.PlanePositionSequence[0].ImagePositionPatient for seq in self.PerFrameFunctionalGroupsSequence]

    def del_intensity_trans(self):
        """Delete the pixel value transformation sequence from dataset"""
        del self.SharedFunctionalGroupsSequence[0].PixelValueTransformationSequence
