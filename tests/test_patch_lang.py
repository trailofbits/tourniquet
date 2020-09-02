from tourniquet import Tourniquet
from tourniquet.patch_lang import FixPattern, NodeStmt, PatchTemplate


def test_concretize_nodestmt(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    node = NodeStmt()
    concretized = list(node.concretize(23, 3, tourniquet.db, str(test_file)))
    assert len(concretized) == 1
    assert concretized[1] == "char buff[10];;"


def test_patch():
    _ = FixPattern
    _ = PatchTemplate
