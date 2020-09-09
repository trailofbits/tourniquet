from tourniquet import Tourniquet
from tourniquet.location import Location as L
from tourniquet.location import SourceCoordinate as SC
from tourniquet.patch_lang import (
    BinaryBoolOperator,
    BinaryMathOperator,
    ElseStmt,
    FixPattern,
    IfStmt,
    LessThanExpr,
    Lit,
    NodeStmt,
    ReturnStmt,
    StaticBufferSize,
    Variable
)


def test_concretize_lit():
    lit = Lit("1")
    assert set(lit.concretize(None, None)) == {"1"}


def test_concretize_variable(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    variable = Variable()
    location = L(test_file, SC(23, 3))
    concretized = set(variable.concretize(tourniquet.db, location))
    assert len(concretized) == 6
    assert concretized == {"argc", "argv", "buff", "buff_len", "pov", "len"}


def test_concretize_staticbuffersize(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    sbs = StaticBufferSize()
    location = L(test_file, SC(23, 3))
    concretized = set(sbs.concretize(tourniquet.db, location))
    assert concretized == {"sizeof(buff)"}


def test_concretize_binarymathoperator():
    bmo = BinaryMathOperator(Lit("1"), Lit("2"))
    concretized = set(bmo.concretize(None, None))
    assert concretized == {"1 + 2", "1 - 2", "1 / 2", "1 * 2", "1 << 2"}


def test_concretize_binarybooloperator():
    bbo = BinaryBoolOperator(Lit("1"), Lit("2"))
    concretized = set(bbo.concretize(None, None))
    assert concretized == {"1 == 2", "1 != 2", "1 <= 2", "1 < 2", "1 >= 2", "1 > 2"}


def test_concretize_lessthanexpr():
    lte = LessThanExpr(Lit("1"), Lit("2"))
    concretized = set(lte.concretize(None, None))
    assert concretized == {"1 < 2"}


def test_concretize_nodestmt(test_files, tmp_db):
    tourniquet = Tourniquet(tmp_db)
    test_file = test_files / "patch_test.c"
    tourniquet.collect_info(test_file)

    node = NodeStmt()
    location = L(test_file, SC(23, 3))
    concretized = list(node.concretize(tourniquet.db, location))
    assert len(concretized) == 1
    assert concretized[0] == "char buff[10];"


def test_concretize_ifstmt():
    ifs = IfStmt(Lit("1"), Lit("bark;"))
    assert set(ifs.concretize(None, None)) == {"if (1) {\nbark;\n}\n"}


def test_concretize_elsestmt():
    elses = ElseStmt(Lit("bark;"))
    assert set(elses.concretize(None, None)) == {"else {\nbark;\n}\n"}


def test_concretize_returnstmt():
    rets = ReturnStmt(Lit("foo"))
    assert set(rets.concretize(None, None)) == {"return foo;"}


# TODO(ww): Tests for:
# * Statement
# * StatementList
# * PatchTemplate


def test_fixpattern():
    fp = FixPattern(IfStmt(Lit("1"), Lit("exit(1);")), ElseStmt(Lit("exit(2);")))
    concretized = list(fp.concretize(None, None))
    assert len(concretized) == 1
    assert concretized[0] == "if (1) {\nexit(1);\n}\n\nelse {\nexit(2);\n}\n"
