import os

import itk
import numpy as np
import pandas as pd

from medio.tests.itk_dcm_orientations.orientations_utils import (ornt_list, ornt_direction_dict, is_right_handed_ornt,
                                                                 direction2ornt)
from medio.tests.itk_dcm_orientations.itk_utils import set_image_direction, get_image_direction


def get_saved_ornt(image, desired_ornt, remove=True):
    filename = desired_ornt + '.dcm'
    desired_direction = ornt_direction_dict[desired_ornt]
    set_image_direction(image, desired_direction)
    itk.imwrite(image, filename)
    saved_image = itk.imread(filename)
    if remove:
        os.remove(filename)
    saved_direction = get_image_direction(saved_image)
    is_equal = np.array_equal(saved_direction, desired_direction)
    if is_equal:
        saved_ornt = desired_ornt
    else:
        saved_ornt = direction2ornt(saved_direction)
    return saved_ornt, is_equal


arr = np.random.randint(0, 256, size=(10, 30, 25), dtype='uint8')  # (slices, cols, rows)
arr_rgb = np.random.randint(0, 256, size=(10, 30, 25, 3), dtype='uint8')  # (slices, cols, rows, channels)
img = itk.image_from_array(arr)
img_rgb = itk.image_from_array(arr_rgb, is_vector=True)

df = pd.DataFrame(columns=['Orientation',
                           'Right/Left-handed orientation',
                           'Success',
                           'Saved orientation',
                           'RGB success',
                           'RGB saved orientation'
                           ])

for ornt in ornt_list:
    state_dict = dict.fromkeys(df.columns)
    state_dict['Orientation'] = ornt
    state_dict['Right/Left-handed orientation'] = 'R' if is_right_handed_ornt(ornt) else 'L'
    # test 3d dicom
    state_dict['Saved orientation'], state_dict['Success'] = get_saved_ornt(img, ornt)
    # test 3d RGB dicom
    state_dict['RGB saved orientation'], state_dict['RGB success'] = get_saved_ornt(img_rgb, ornt)
    df = df.append(state_dict, ignore_index=True)

df.sort_values('Right/Left-handed orientation', ascending=False, inplace=True)
df.to_csv('itk_dcm_orientations.csv', index=False)

right_handed = np.array(df['Right/Left-handed orientation'] == 'R')
success = np.array(df['Success'])
rgb_success = np.array(df['RGB success'])
rai_ornt = np.array(df['Orientation'] == 'RAI')

print('Right-handed == Success:', np.array_equal(right_handed, success))
print('Right-handed == RGB success:', np.array_equal(right_handed, rgb_success))
print('\'RAI\' orientation == RGB success:', np.array_equal(rai_ornt, rgb_success))
