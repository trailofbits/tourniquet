import logging
import os

import pytest

from tourniquet import Tourniquet
from tourniquet.patch_lang import FixPattern, NodeStmt, PatchTemplate

logger = logging.getLogger(__name__)

TEST_DIR = os.path.realpath(os.path.dirname(__file__))
TEST_FILE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "test_files"))

#############################
#      Tests go here        #
#############################


def test_tourniquet_extract_ast():
    logger.info("Testing extraction of simple types")

    # No DB name for now
    test_extractor = Tourniquet("test.db")
    test_file = os.path.join(TEST_FILE_DIR, "patch_test.c")
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


def test_tourniquet_extract_badfile():
    logger.info("Testing extract error handling")
    test_extractor = Tourniquet("test.db")
    test_file = os.path.join(TEST_FILE_DIR, "")
    with pytest.raises(FileNotFoundError):
        test_extractor.extract_ast(test_file)
    with pytest.raises(FileNotFoundError):
        test_extractor.extract_ast("")


def test_new_template():
    test_extractor = Tourniquet("test.db")
    os.path.join(TEST_FILE_DIR, "patch_test.c")
    new_template = PatchTemplate("testme", lambda x, y: True, FixPattern(NodeStmt()))
    test_extractor.add_new_template(new_template)
    assert len(test_extractor.patch_templates) == 1
    # view_str = test_extractor.view_template()
