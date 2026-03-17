from __future__ import annotations

from typing import Generic, TypeVar

KT = TypeVar("KT")
VT = TypeVar("VT")


class TwoWayDict(dict[KT | VT, KT | VT], Generic[KT, VT]):
    """Dictionary which contains key-value + value-key pairs: {key: value, value: key}"""

    def __setitem__(self, key: KT | VT, value: KT | VT) -> None:
        # Remove any previous connections with these values
        if key in self:
            del self[key]
        if value in self:
            del self[value]
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

    def __delitem__(self, key: KT | VT) -> None:
        dict.__delitem__(self, self[key])
        dict.__delitem__(self, key)

    def __len__(self) -> int:
        """Returns the number of connections"""
        return dict.__len__(self) // 2
