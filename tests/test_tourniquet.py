import logging
import os

import pytest

from tourniquet import Tourniquet
from tourniquet.patch_lang import *

logger = logging.getLogger("tourniquet_test:")
TEST_DIR = os.path.realpath(os.path.dirname(__file__))
TEST_FILE_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "test_files"))

#############################
#      Tests go here        #
#############################


def test_tourniquet_extract_simple():
    logger.info("Testing extraction of simple types")

    # No DB name for now
    test_extractor = Tourniquet("test.db")
    test_file = os.path.join(TEST_FILE_DIR, "patch_test.c")
    extraction_results: dict = test_extractor.extract_ast(test_file)
    # Look for the four variables
    assert "main" in extraction_results
    assert "global" in extraction_results
    entries = extraction_results["main"]
    # Fold all vars into single list
    var_list = [item for entry in entries if "var_type" in entry for item in entry]
    # Test locals
    assert "buff" in var_list
    assert "len" in var_list
    assert "buff_len" in var_list
    assert "pov" in var_list
    # Get function parameters
    assert "argc" in var_list
    assert "argv" in var_list
    # The global should be there too :)
    globals = extraction_results["global"]
    global_var_list = [item for entry in globals for item in entry]
    assert "pass" in global_var_list


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
    test_file = os.path.join(TEST_FILE_DIR, "patch_test.c")
    new_template = PatchTemplate("testme", lambda x, y: True, FixPattern(NodeStmt()))
    test_extractor.add_new_template(new_template)
    assert len(test_extractor.patch_templates) == 1
    # view_str = test_extractor.view_template()
