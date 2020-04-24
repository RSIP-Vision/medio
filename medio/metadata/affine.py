import numpy as np


class Affine(np.ndarray):
    """
    Class for general (d+1)x(d+1) affine matrices, and in particular d=3 (3d space)
    Usage examples:
    >>> affine1 = Affine(np.eye(4))
    >>> affine2 = Affine(direction=np.eye(3), spacing=[0.33, 1, 0.33], origin=[-90.3, 10, 1.44])
    >>> index = [4, 2, 9]
    >>> coord = affine2.index2coord(index)
    """

    # keys for the origin and M matrix parts in the affine matrix
    _origin_key = (slice(-1), -1)
    _m_key = (slice(-1), slice(-1))

    def __new__(cls, affine=None, *, direction=None, spacing=None, origin=None):
        """
        Construct a numpy array of class Affine. Initialize Affine in one of the following ways:
        1. (d+1)x(d+1) matrix as affine (d is the dimension of the space)
        2. affine=None and construction from direction, spacing and origin parameters
        :param affine: (d+1)x(d+1) affine matrix, comprised of the M matrix and origin shift b: y = M*x + b
        x is the index vector of length d and y is the corresponding physical coordinates vector of the same length
        :param direction: dxd direction matrix (only rotations without scaling)
        :param spacing: scaling of the axes - vector of length d
        :param origin: the origin - b in the formula above - vector of length d (or a scalar)
        :return:
        """
        if affine is None:
            affine = cls.construct_affine(direction, spacing, origin)
        obj = np.asarray(affine).view(cls)  # return array view of type Affine
        return obj
    
    def __init__(self, affine=None, *, direction=None, spacing=None, origin=None):
        self.dim = self.shape[0] - 1
        if affine is None:
            self._spacing = np.asarray(spacing)
            self._direction = np.asarray(direction)
        else:
            self._spacing = self.affine2spacing(self)
            self._direction = self.affine2direction(self, self.spacing)

    def index2coord(self, index_vector):
        """Return y according to y = M*x + b"""
        return self._m_matrix @ index_vector + self.origin

    def __matmul__(self, other):
        return super().__matmul__(other).view(np.ndarray)

    def __getitem__(self, item):
        return super().__getitem__(item).view(np.ndarray)

    # Affine properties in addition to the numpy array
    @property
    def origin(self):
        return self[self._origin_key]

    @origin.setter
    def origin(self, value):
        self[self._origin_key] = value

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, value):
        value = np.asarray(value)
        self._m_matrix = self._m_matrix @ np.diag(value / self._spacing)
        self._spacing = np.abs(value)  # the spacing must be positive (or at least nonnegative)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        value = np.asarray(value)
        self._m_matrix = value @ np.diag(self.spacing)
        self._direction = value

    # Internal property - m matrix
    @property
    def _m_matrix(self):
        return self[self._m_key]

    @_m_matrix.setter
    def _m_matrix(self, value):
        self[self._m_key] = value

    # Static methods for affine construction and components
    @staticmethod
    def construct_affine(direction, spacing, origin):
        direction = np.asarray(direction)
        dim = direction.shape[0]
        affine = np.eye(dim + 1)
        affine[Affine._m_key] = direction @ np.diag(spacing)
        affine[Affine._origin_key] = origin
        return affine

    @staticmethod
    def affine2origin(affine):
        return affine[Affine._origin_key]

    @staticmethod
    def affine2spacing(affine):
        dim = affine.shape[0] - 1
        return np.linalg.norm(affine[Affine._m_key] @ np.eye(dim), axis=0)

    @staticmethod
    def affine2direction(affine, spacing=None):
        if spacing is None:
            spacing = Affine.affine2spacing(affine)
        return affine[Affine._m_key] @ np.diag(1 / spacing)

    @staticmethod
    def affine2comps(affine, spacing=None):
        if spacing is None:
            spacing = Affine.affine2spacing(affine)
        return Affine.affine2direction(affine, spacing), spacing, Affine.affine2origin(affine)
