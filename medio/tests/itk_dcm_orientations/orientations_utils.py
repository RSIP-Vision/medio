import itertools

import numpy as np

letter_vec_dict = {'R': [1, 0, 0],
                   'L': [-1, 0, 0],
                   'A': [0, 1, 0],
                   'P': [0, -1, 0],
                   'I': [0, 0, 1],
                   'S': [0, 0, -1]
                   }


def ornt2direction(ornt):
    return np.array([letter_vec_dict[letter] for letter in ornt]).T


ornt_iter = itertools.chain(
    *map(itertools.permutations,
         itertools.product(('R', 'L'), ('A', 'P'), ('I', 'S'))
         ))

# two way dictionary that translates itk orientation codes to direction matrices
ornt_direction_dict = dict()
ornt_list = []

for ornt_tup in ornt_iter:
    ornt = ''.join(ornt_tup)
    ornt_list += [ornt]
    ornt_direction_dict[ornt] = ornt2direction(ornt)


def is_right_handed_ornt(ornt):
    direction = ornt_direction_dict[ornt]
    det = np.linalg.det(direction)
    assert det in [-1, 1]  # check that the direction matrix is valid
    return det == 1


def direction2ornt(direction):
    for key, val in ornt_direction_dict.items():
        if np.array_equal(direction, val):
            return key
    raise ValueError('Invalid direction')
