from __future__ import annotations

from medio.metadata.dcm_uid import MEDIO_ROOT_UID, generate_uid


class TestGenerateUid:
    def test_has_prefix(self) -> None:
        uid = generate_uid()
        assert uid.startswith(MEDIO_ROOT_UID)

    def test_unique(self) -> None:
        uid1 = generate_uid()
        uid2 = generate_uid()
        assert uid1 != uid2

    def test_valid_uid_chars(self) -> None:
        uid = generate_uid()
        assert all(c in "0123456789." for c in uid)

    def test_max_length(self) -> None:
        uid = generate_uid()
        assert len(uid) <= 64
