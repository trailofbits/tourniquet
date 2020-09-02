from pathlib import Path

import pytest

from tourniquet import Tourniquet
from tourniquet.patch_lang import FixPattern, NodeStmt, PatchTemplate

TEST_DIR = Path(__file__).resolve().parent
TEST_FILE_DIR = TEST_DIR / "test_files"


def test_tourniquet_extract_ast(tmp_path):
    # No DB name for now
    test_extractor = Tourniquet(tmp_path)
    test_file = TEST_FILE_DIR / "patch_test.c"
    ast_dict: dict = test_extractor._extract_ast(test_file)

    # The dictionary produced from the AST has three top-level keys:
    # module_name, globals, and functions.
    assert "module_name" in ast_dict
    assert "globals" in ast_dict
    assert "functions" in ast_dict

    # The module name is our source file.
    assert ast_dict["module_name"] == test_file

    # Everything in globals is a "var_type".
    assert all(global_[0] == "var_type" for global_ in ast_dict["globals"])

    # There's at least one global named "pass".
    assert any(global_[5] == "pass" for global_ in ast_dict["globals"])

    # There's a "main" function in the "functions" dictionary.
    assert "main" in ast_dict["functions"]
    main = ast_dict["functions"]["main"]

    # There are 4 variables in "main", plus "argc" and "argv".
    main_vars = [var_decl[5] for var_decl in main if var_decl[0] == "var_type"]
    assert set(main_vars) == {"argc", "argv", "buff", "buff_len", "pov", "len"}


def test_tourniquet_extract_ast_invalid_file(tmp_path):
    test_extractor = Tourniquet(tmp_path)
    test_file = TEST_FILE_DIR / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        test_extractor._extract_ast(test_file)


def test_new_template(tmp_path):
    test_extractor = Tourniquet(tmp_path)
    new_template = PatchTemplate("testme", lambda x, y: True, FixPattern(NodeStmt()))
    test_extractor.add_new_template(new_template)
    assert len(test_extractor.patch_templates) == 1
