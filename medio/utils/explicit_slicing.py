def explicit_inds(key, shape):
    """Make getitem key explicit in the context of numpy ndarrays basic slicing and indexing"""
    ndim = len(shape)
    # set defaults
    start = [0] * ndim
    stop = list(shape)
    stride = [1] * ndim

    def update(i, k):
        """Update start, stop, stride at index i based on k"""
        if isinstance(k, int):
            start[i], stop[i] = k, k + 1
        elif isinstance(k, slice):
            start[i], stop[i], stride[i] = k.indices(shape[i])
        else:
            raise NotImplementedError(f'The indexing key \'{k}\' is not supported.')

    i = 0
    for k in key:
        if k is Ellipsis:
            # loop in reverse order
            i = ndim - 1
            for k_r in key[::-1]:
                if k_r is Ellipsis:
                    break
                else:
                    update(i, k_r)
                    i -= 1
            break
        else:
            update(i, k)
            i += 1

    return start, stop, stride
