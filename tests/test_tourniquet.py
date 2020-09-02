from pathlib import Path

import pytest

from tourniquet import Tourniquet
from tourniquet.models import Function, Global, Module
from tourniquet.patch_lang import FixPattern, NodeStmt, PatchTemplate

TEST_DIR = Path(__file__).resolve().parent
TEST_FILE_DIR = TEST_DIR / "test_files"


def test_tourniquet_extract_ast(tmp_db):
    # No DB name for now
    test_extractor = Tourniquet(tmp_db)
    test_file = TEST_FILE_DIR / "patch_test.c"
    ast_dict: dict = test_extractor._extract_ast(test_file)

    # The dictionary produced from the AST has three top-level keys:
    # module_name, globals, and functions.
    assert "module_name" in ast_dict
    assert "globals" in ast_dict
    assert "functions" in ast_dict

    # The module name is our source file.
    assert ast_dict["module_name"] == str(test_file)

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


def test_tourniquet_db(tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = TEST_FILE_DIR / "patch_test.c"
    tourniquet.collect_info(test_file)

    module = tourniquet.db.query(Module).filter_by(name=str(test_file)).one()
    assert len(module.functions) == 1

    pass_ = tourniquet.db.query(Global).filter_by(name="pass").one()
    assert pass_.name == "pass"
    assert pass_.type_ == "char *"
    assert pass_.start_line == 20
    assert pass_.start_column == 1
    assert pass_.end_line == 20
    assert pass_.end_column == 14
    assert not pass_.is_array
    assert pass_.size == 8

    main = tourniquet.db.query(Function).filter_by(name="main").one()
    assert main.name == "main"
    assert main.start_line == 22
    assert main.start_column == 1
    assert main.end_line == 38
    assert main.end_column == 1
    assert len(main.var_decls) == 6
    assert len(main.calls) == 4
    assert len(main.statements) == 10


def test_tourniquet_extract_ast_invalid_file(tmp_db):
    test_extractor = Tourniquet(tmp_db)
    test_file = TEST_FILE_DIR / "does-not-exist"
    with pytest.raises(FileNotFoundError):
        test_extractor._extract_ast(test_file)


def test_register_template(tmp_db):
    test_extractor = Tourniquet(tmp_db)
    new_template = PatchTemplate(lambda x, y: True, FixPattern(NodeStmt()))
    test_extractor.register_template("testme", new_template)
    assert len(test_extractor.patch_templates) == 1
