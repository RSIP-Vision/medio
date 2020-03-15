import SimpleITK as sitk
from pathlib import Path
import numpy as np
import time


class SItkIO:
    pixel_type = sitk.sitkInt16
    coord_sys = 'itk'

    @staticmethod
    def pack2image(np_image, affine):
        image = SItkIO.array_to_sitk_img(np_image.astype('int16'))
        direction, spacing, origin = affine.direction, affine.spacing, affine.origin
        image.SetSpacing(spacing.astype('float'))
        image.SetOrigin(origin.astype('float'))
        image.SetDirection(direction.flatten().astype('float'))
        return image

    @staticmethod
    def sitk_img_to_array(img_sitk):
        """Swap the axes to make the third axis the z axis (inferior - superior) in RAS orientation"""
        img_array = sitk.GetArrayFromImage(img_sitk)
        reordered = np.swapaxes(img_array, 0, 2).copy()
        return reordered

    @staticmethod
    def array_to_sitk_img(img_array):
        reordered = np.swapaxes(img_array, 0, 2).copy()
        img_sitk = sitk.GetImageFromArray(reordered)
        return img_sitk

    @staticmethod
    def save_img(output_filename, image_np, affine):
        """
        Saves a Numpy image to a file - also dicom file if ends with .dcm
        :param output_filename:
        :param image_np: numpy ndarray image
        :param affine: the affine of class Affine
        :return:
        """
        image = SItkIO.pack2image(image_np, affine)
        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()

        mod_date = time.strftime("%Y%m%d")
        mod_time = time.strftime("%H%M%S")
        image.SetMetaData("0008|0012", mod_date)  # Instance Creation Date
        image.SetMetaData("0008|0013", mod_time)  # Instance Creation Time
        image.SetMetaData("0020|000e", "1.2.826.0.1.3680043.2.1125." + mod_date + ".1" + mod_time)

        writer.SetFileName(output_filename)
        writer.Execute(image)

    @staticmethod
    def save_series_files_dcm_slices(np_image, metadata_dict={}, pixdim=None, output_folder=None, output_filename='I'):
        # TODO: UNDER CONSTRUCTION
        # Read the original series. First obtain the series file names using the
        # image series reader.
        # data_directory = sys.argv[1]
        # series_IDs = sitk.ImageSeriesReader.GetGDCMSeriesIDs(data_directory)
        # if not series_IDs:
        #     print("ERROR: given directory \"" + data_directory + "\" does not contain a DICOM series.")
        #     sys.exit(1)
        # series_file_names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(data_directory, series_IDs[0])
        #
        # series_reader = sitk.ImageSeriesReader()
        # series_reader.SetFileNames(series_file_names)

        # Configure the reader to load all of the DICOM tags (public+private):
        # By default tags are not loaded (saves time).
        # By default if tags are loaded, the private tags are not loaded.
        # We explicitly configure the reader to load tags, including the
        # private ones.
        # series_reader.MetaDataDictionaryArrayUpdateOn()
        # series_reader.LoadPrivateTagsOn()
        # image3D = series_reader.Execute()

        # Modify the image (blurring)
        # filtered_image = sitk.DiscreteGaussian(image3D)

        # Write the 3D image as a series
        # IMPORTANT: There are many DICOM tags that need to be updated when you modify an
        #            original image. This is a delicate opration and requires knowlege of
        #            the DICOM standard. This example only modifies some. For a more complete
        #            list of tags that need to be modified see:
        #                           http://gdcm.sourceforge.net/wiki/index.php/Writing_DICOM

        writer = sitk.ImageFileWriter()
        # Use the study/series/frame of reference information given in the meta-data
        # dictionary and not the automatically generated information from the file IO
        writer.KeepOriginalImageUIDOn()

        # Copy relevant tags from the original meta-data dictionary (private tags are also
        # accessible).
        # tags_to_copy = ["0010|0010",  # Patient Name
        #                 "0010|0020",  # Patient ID
        #                 "0010|0030",  # Patient Birth Date
        #                 "0020|000D",  # Study Instance UID, for machine consumption
        #                 "0020|0010",  # Study ID, for human consumption
        #                 "0008|0020",  # Study Date
        #                 "0008|0030",  # Study Time
        #                 "0008|0050",  # Accession Number
        #                 "0008|0060"  # Modality
        #                 ]

        modification_time = time.strftime("%H%M%S")
        modification_date = time.strftime("%Y%m%d")

        # Copy some of the tags and add the relevant tags indicating the change.
        # For the series instance UID (0020|000e), each of the components is a number, cannot start
        # with zero, and separated by a '.' We create a unique series ID using the date and time.
        # tags of interest:
        # direction = np_image.GetDirection()
        # series_tag_values = [(k, series_reader.GetMetaData(0, k)) for k in tags_to_copy if
        #                      series_reader.HasMetaDataKey(0, k)] + \
        #                     [("0008|0031", modification_time),  # Series Time
        #                      ("0008|0021", modification_date),  # Series Date
        #                      ("0008|0008", "DERIVED\\SECONDARY"),  # Image Type
        #                      ("0020|000e", "1.2.826.0.1.3680043.2.1125." + modification_date + ".1" + modification_time),
        #                      Series Instance UID
        #                      ("0020|0037",
        #                       '\\'.join(map(str, (direction[0], direction[3], direction[6],  # Image Orientation (Patient)
        #                                           direction[1], direction[4], direction[7])))),
        #                      ("0008|103e",
        #                       series_reader.GetMetaData(0, "0008|103e") + " Processed-SimpleITK")]  # Series Description

        cast_filter = sitk.CastImageFilter()
        cast_filter.SetOutputPixelType(sitk.sitkInt16)
        print(metadata_dict.pop("0020|000e", None))

        print(metadata_dict)
        sitk_img = sitk.GetImageFromArray(np_image)
        for i in range(np_image.shape[-1]):
            image_slice = sitk.GetImageFromArray(np_image[:, :, i])
            # Tags shared by the series.
            # for tag, value in series_tag_values:
            #     image_slice.SetMetaData(tag, value)
            # Slice specific tags.

            image_slice = cast_filter.Execute(image_slice)
            for k in metadata_dict:
                image_slice.SetMetaData(k, metadata_dict[k])

            image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d"))  # Instance Creation Date
            image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S"))  # Instance Creation Time
            image_slice.SetMetaData("0020|1041", str(i*pixdim[2]))
            image_slice.SetMetaData("0020|0032", '\\'.join(
                map(str, sitk_img.TransformIndexToPhysicalPoint((0, 0, i)))))  # Image Position (Patient)
            image_slice.SetMetaData("0020,0011", str(i))
            # image_slice.SetMetaData("0020|0032", '\\'.join(
            #     map(str, filtered_image.TransformIndexToPhysicalPoint((0, 0, i)))))  # Image Position (Patient)
            image_slice.SetMetaData("0020|0013", str(i))  # Instance Number

            image_slice.SetSpacing(pixdim)
            image_slice.SetMetaData("0018,0050", str(pixdim[2]))  # slice thickness

            # Write to the output directory and add the extension dcm, to force writing in DICOM format.
            writer.SetFileName(str(Path(output_folder) / (output_filename + '_' + str(i) + '.dcm')))

            image_slice.SetMetaData("0020|000e",
                                    "1.2.826.0.1.3680043.2.1125." + modification_date + ".1" + modification_time)
            # print(str(i) + ': ' + image_slice.GetMetaData("0020|000e"))
            # print(str(pixdim))
            writer.Execute(image_slice)

    @staticmethod
    def save_dcm_dir(dirname, image):
        """Write sitk image as dicom series in new/existing directory dirname
         Note: image should be of supported type, for example int16"""

        def write_slice(dirname, sitk_image, i, series_tag_values):
            image_slice = sitk_image[:, :, i]

            # Tags shared by the series.
            list(map(lambda tag_value: image_slice.SetMetaData(tag_value[0], tag_value[1]), series_tag_values))

            # Slice specific tags.
            image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d"))  # Instance Creation Date
            image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S"))  # Instance Creation Time

            # Setting the type to CT preserves the slice location.
            image_slice.SetMetaData("0008|0060", "CT")  # set the type to CT so the thickness is carried over

            # (0020, 0032) image position patient determines the 3D spacing between slices.
            image_slice.SetMetaData("0020|0032", '\\'.join(
                map(str, sitk_image.TransformIndexToPhysicalPoint((0, 0, i)))))  # Image Position (Patient)
            image_slice.SetMetaData("0020,0013", str(i))  # Instance Number

            # Write to the output directory and add the extension dcm, to force writing in DICOM format.
            writer.SetFileName(str(Path(dirname) / (str(i) + '.dcm')))
            writer.Execute(image_slice)

        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()

        modification_time = time.strftime("%H%M%S")
        modification_date = time.strftime("%Y%m%d")

        direction = image.GetDirection()
        series_tag_values = [("0008|0031", modification_time),  # Series Time
                             ("0008|0021", modification_date),  # Series Date
                             ("0008|0008", "DERIVED\\SECONDARY"),  # Image Type
                             ("0020|000e",
                              "1.2.826.0.1.3680043.2.1125." + modification_date + ".1" + modification_time),
                             # Series Instance UID
                             ("0020|0037",
                              '\\'.join(
                                  map(str, (direction[0], direction[3], direction[6],  # Image Orientation (Patient)
                                            direction[1], direction[4], direction[7])))),
                             # ("0008|103e", "Created-SimpleITK")  # Series Description
                             ]

        # Write slices to output directory
        list(map(lambda i: write_slice(dirname, image, i, series_tag_values), range(image.GetDepth())))
