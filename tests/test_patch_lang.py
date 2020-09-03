from tourniquet import Tourniquet
from tourniquet.patch_lang import (
    BinaryBoolOperator,
    BinaryMathOperator,
    ElseStmt,
    FixPattern,
    IfStmt,
    LessThanExpr,
    Lit,
    NodeStmt,
    PatchTemplate,
    StaticBufferSize,
    Variable
)


def test_concretize_lit():
    lit = Lit("1")
    assert set(lit.concretize(None, None, None, None)) == {"1"}


def test_concretize_variable(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    variable = Variable()
    concretized = set(variable.concretize(23, 3, tourniquet.db, str(test_file)))
    assert len(concretized) == 6
    assert concretized == {"argc", "argv", "buff", "buff_len", "pov", "len"}


def test_concretize_staticbuffersize(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    sbs = StaticBufferSize()
    concretized = set(sbs.concretize(23, 3, tourniquet.db, str(test_file)))
    assert concretized == {"sizeof(buff)"}


def test_concretize_binarymathoperator():
    bmo = BinaryMathOperator(Lit("1"), Lit("2"))
    concretized = set(bmo.concretize(None, None, None, None))
    assert concretized == {"1 + 2", "1 - 2", "1 / 2", "1 * 2", "1 << 2"}


def test_concretize_binarybooloperator():
    bbo = BinaryBoolOperator(Lit("1"), Lit("2"))
    concretized = set(bbo.concretize(None, None, None, None))
    assert concretized == {"1 == 2", "1 != 2", "1 <= 2", "1 < 2", "1 >= 2", "1 > 2"}


def test_concretize_lessthanexpr():
    lte = LessThanExpr(Lit("1"), Lit("2"))
    concretized = set(lte.concretize(None, None, None, None))
    assert concretized == {"1 < 2"}


def test_concretize_nodestmt(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    node = NodeStmt()
    concretized = list(node.concretize(23, 3, tourniquet.db, str(test_file)))
    assert len(concretized) == 1
    assert concretized[0] == "char buff[10];;"


# TODO(ww): Tests for:
# * Statement
# * StatementList
# * IfStmt
# * ElseStmt
# * ReturnStmt


def test_fixpattern():
    fp = FixPattern(IfStmt(Lit("1"), Lit("exit(1);")), ElseStmt(Lit("exit(2);")))
    concretized = list(fp.concretize(None, None, None, None))
    assert len(concretized) == 1
    assert (
        concretized[0]
        == """if (1) {
exit(1);
}

else {
exit(2);
}
"""
    )


def test_patch():
    _ = FixPattern
    _ = PatchTemplate
