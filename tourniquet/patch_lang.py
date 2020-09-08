import itertools
from abc import ABC, abstractmethod
from typing import Iterator, List

from . import models


class Expression(ABC):
    @abstractmethod
    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        yield from ()

    def view(self, line: int, col: int, db, module_name) -> str:
        return "Expression()"


class Lit(Expression):
    def __init__(self, expr: str):
        self.expr = expr

    def concretize(self, _line, _col, _db, _module_name) -> Iterator[str]:
        yield self.expr

    def view(self, _line, _col, _db, _module_name):
        return f"Lit({self.expr})"


# TODO For these base types when you concretize them return a list of potential values
# by querying the DB or having some preset
class Variable(Expression):
    # Query DB for all variables within scope at the line number.
    # TODO(ww): This is probably slightly unsound, in terms of concretizations
    # produced: the set of variables in a function is not the set of variables
    # guaranteed to be in scope at a line number.
    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        # TODO(ww): Should we also concretize with available globals?
        function = (
            db.query(models.Function)
            .filter(
                (module_name == models.Function.module_name)
                & (line >= models.Function.start_line)
                & (col >= models.Function.start_column)
                & (
                    ((line == models.Function.end_line) & (col <= models.Function.end_column))
                    | ((line < models.Function.end_line))
                )
            )
            .one_or_none()
        )

        if function is None:
            # TODO(ww): Custom error.
            raise ValueError(f"no function contains ({line}, {col})")

        for var_decl in function.var_decls:
            yield var_decl.name

    def view(self, line: int, col: int, db, _module_name) -> str:
        return "Variable()"


class StaticBufferSize(Expression):
    # Query for all static array types and return list of sizeof()..
    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        # TODO(ww): Should we also concretize with available globals?
        function = (
            db.query(models.Function)
            .filter(
                (module_name == models.Function.module_name)
                & (line >= models.Function.start_line)
                & (col >= models.Function.start_column)
                & (
                    ((line == models.Function.end_line) & (col <= models.Function.end_column))
                    | ((line < models.Function.end_line))
                )
            )
            .one_or_none()
        )

        if function is None:
            # TODO(ww): Custom error.
            raise ValueError(f"no function contains ({line}, {col})")

        for var_decl in function.var_decls:
            if not var_decl.is_array:
                continue
            yield f"sizeof({var_decl.name})"

    def view(self, line: int, col: int, db, module_name) -> str:
        return "StaticBufferSize()"


class BinaryMathOperator(Expression):
    # Really return [+, -, /, *, <<]
    def __init__(self, lhs: Expression, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        lhs_exprs = self.lhs.concretize(line, col, db, module_name)
        rhs_exprs = self.rhs.concretize(line, col, db, module_name)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} + {rhs}"
            yield f"{lhs} - {rhs}"
            yield f"{lhs} / {rhs}"
            yield f"{lhs} * {rhs}"
            yield f"{lhs} << {rhs}"

    def view(self, line: int, col: int, db, module_name) -> str:
        return (
            f"BinaryMathOperator({self.lhs.view(line, col, db, module_name)}, "
            f"{self.lhs.view(line, col, db, module_name)})"
        )


class BinaryBoolOperator(Expression):
    # Really return [==, !=, <=, <, >=, >]
    def __init__(self, lhs: Expression, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        lhs_exprs = self.lhs.concretize(line, col, db, module_name)
        rhs_exprs = self.rhs.concretize(line, col, db, module_name)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} == {rhs}"
            yield f"{lhs} != {rhs}"
            yield f"{lhs} <= {rhs}"
            yield f"{lhs} < {rhs}"
            yield f"{lhs} >= {rhs}"
            yield f"{lhs} > {rhs}"

    def view(self, line: int, col: int, db, module_name) -> str:
        return (
            f"BinaryBoolOperator({self.lhs.view(line, col, db, module_name)}, "
            f"{self.rhs.view(line, col, db, module_name)})"
        )


class LessThanExpr(Expression):
    def __init__(self, lhs: Expression, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        lhs_exprs = self.lhs.concretize(line, col, db, module_name)
        rhs_exprs = self.rhs.concretize(line, col, db, module_name)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} < {rhs}"

    def view(self, line: int, col: int, db, module_name):
        self.lhs.view(line, col, db, module_name) + " < " + self.rhs.view(
            line, col, db, module_name
        )


class Statement(ABC):
    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        pass

    def view(self, line: int, col: int, db, module_name):
        pass


class StatementList:
    def __init__(self, *args):
        self.statements: List[Statement] = []
        for arg in args:
            for i in arg:
                self.statements.append(i)

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        concretized = [stmt.concretize(line, col, db, module_name) for stmt in self.statements]
        for items in set(itertools.product(*concretized)):
            yield "\n".join(items)

    def view(self, line: int, col: int, db, module_name) -> str:
        final_str = ""
        for stmt in self.statements:
            final_str += stmt.view(line, col, db, module_name) + "\n"
        return final_str


class IfStmt(Statement):
    def __init__(self, cond_expr: Expression, *args):
        self.cond_expr = cond_expr
        self.statement_list = StatementList(args)

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        cond_list = self.cond_expr.concretize(line, col, db, module_name)
        stmt_list = self.statement_list.concretize(line, col, db, module_name)
        for (cond, stmt) in itertools.product(cond_list, stmt_list):
            cand_str = "if (" + cond + ") {\n" + stmt + "\n}\n"
            yield cand_str

    def view(self, line: int, col: int, db, module_name) -> str:
        if_str = "if (" + self.cond_expr.view(line, col, db, module_name) + ") {\n"
        if_str += self.statement_list.view(line, col, db, module_name)
        if_str += "\n}\n"
        return if_str


class ElseStmt(Statement):
    def __init__(self, *args):
        self.statement_list = StatementList(args)

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        stmt_list = self.statement_list.concretize(line, col, db, module_name)
        for stmt in stmt_list:
            cand_str = "else {\n" + stmt + "\n}\n"
            yield cand_str

    def view(self, line: int, col: int, db, module_name) -> str:
        return "else {\n" + self.statement_list.view(line, col, db, module_name) + "\n}\n"


class ReturnStmt(Statement):
    def __init__(self, expr: Expression):
        self.expr = expr

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        expr_list = self.expr.concretize(line, col, db, module_name)
        for exp in expr_list:
            candidate_str = f"return {exp};"
            yield candidate_str

    def view(self, line: int, col: int, db, module_name):
        return f"return  {self.expr.view(line, col, db, module_name)};"


# TODO This should take a Node, which is something from... the DB? Maybe?
class NodeStmt(Statement):
    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        source_info = self.fetch_node(line, col, db, module_name)
        yield source_info

    def view(self, line, col, db, module_name) -> str:
        # Fetch and create a node.
        source_info = self.fetch_node(line, col, db, module_name)
        return source_info

    def fetch_node(self, line, col, db, module_name) -> str:
        statement = (
            db.query(models.Statement)
            .filter(
                (models.Statement.module_name == module_name)
                & (models.Statement.start_line == line)
                & (models.Statement.start_column == col)
            )
            .one_or_none()
        )
        if statement is None:
            raise ValueError(f"no statement at ({line}, {col})")

        if statement.expr.endswith(";"):
            return statement.expr
        else:
            return f"{statement.expr};"


# Call patcher new pattern, then have the patcher add it to the list.
class FixPattern:
    # Take a *argv and just pass it to make a statement list :)
    def __init__(self, *args):
        self.statement_list = StatementList(args)

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        yield from self.statement_list.concretize(line, col, db, module_name)

    def view(self, line: int, col: int, db, module_name) -> str:
        return self.statement_list.view(line, col, db, module_name)


class PatchTemplate:
    # TODO Think of better API
    def __init__(self, matcher_func, fix_pattern: FixPattern):
        self.matcher_func = matcher_func
        self.fix_pattern = fix_pattern

    def matches(self, line: int, col: int) -> bool:
        matches: bool = self.matcher_func(line, col)
        return matches

    def concretize(self, line: int, col: int, db, module_name) -> Iterator[str]:
        yield from self.fix_pattern.concretize(line, col, db, module_name)

    def view(self, line: int, col: int, db, module_name) -> str:
        return self.fix_pattern.view(line, col, db, module_name)
