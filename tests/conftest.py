from pathlib import Path

import pytest

TEST_DIR = Path(__file__).resolve().parent
TEST_FILE_DIR = TEST_DIR / "test_files"


@pytest.fixture
def test_files() -> Path:
    return TEST_FILE_DIR


@pytest.fixture
def tmp_db(tmp_path) -> Path:
    return tmp_path.with_suffix(".db")
