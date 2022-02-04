import itk


def set_image_direction(image, direction):
    dim = 3
    direction_vnl_mat = itk.vnl_matrix_from_array(direction.astype('float').copy())  # copy is crucial for the float
    direction_itk = itk.Matrix[itk.D, dim, dim](direction_vnl_mat)
    image.SetDirection(direction_itk)


def get_image_direction(image):
    return itk.array_from_vnl_matrix(image.GetDirection().GetVnlMatrix().as_matrix())
