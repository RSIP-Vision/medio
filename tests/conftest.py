from __future__ import annotations

import os
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
TEST_NII = DATA_DIR / "test.nii.gz"
TEST_DCM_DIR = DATA_DIR / "dcm"


@pytest.fixture
def nii_path() -> Path:
    return TEST_NII


@pytest.fixture
def dcm_dir() -> Path:
    return TEST_DCM_DIR


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path
