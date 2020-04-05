import itk
import numpy as np


img = itk.image_from_array(np.zeros((30, 30, 30), dtype='uint16'))
mdict = img.GetMetaDataDictionary()

key_intercept = "0028|1052"
mobj_intercept = itk.MetaDataObject[itk.F].New()
mobj_intercept.SetMetaDataObjectValue(-1024)

key_rescale = "0028|1053"
mobj_rescale = itk.MetaDataObject[itk.F].New()
mobj_rescale.SetMetaDataObjectValue(1.0)

key_rescale_type = "0028|1054"
mobj_rescale_type = itk.MetaDataObject[itk.string].New()
mobj_rescale_type.SetMetaDataObjectValue("HU")

mdict.Set(key_intercept, mobj_intercept)
mdict.Set(key_rescale, mobj_rescale)
mdict.Set(key_rescale_type, mobj_rescale_type)

img.SetMetaDataDictionary(mdict)

itk.imwrite(img, 'C:/Users/Jonathan/try.dcm')

# mdict_img = img.GetMetaDataDictionary()
# mdict_img

# image_type = type(img)
# writer = itk.ImageFileWriter[image_type].New()
# writer.UseInputMetaDataDictionaryOn()
# writer.SetFileName('C:/Users/Jonathan/try.dcm')
# writer.SetInput(img)
# writer.Update()
