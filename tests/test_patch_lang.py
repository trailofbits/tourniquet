from tourniquet import Tourniquet
from tourniquet.patch_lang import FixPattern, NodeStmt, PatchTemplate, Variable


def test_concretize_variable(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    variable = Variable()
    concretized = set(variable.concretize(23, 3, tourniquet.db, str(test_file)))
    assert len(concretized) == 6
    assert concretized == {"argc", "argv", "buff", "buff_len", "pov", "len"}


def test_concretize_staticbuffersize(test_files, tmp_db):
    pass


def test_concretize_binarymathoperator(test_files, tmp_db):
    pass


def test_concretize_nodestmt(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    node = NodeStmt()
    concretized = list(node.concretize(23, 3, tourniquet.db, str(test_file)))
    assert len(concretized) == 1
    assert concretized[0] == "char buff[10];;"


def test_patch():
    _ = FixPattern
    _ = PatchTemplate
