import itertools
from abc import ABC, abstractmethod
from typing import Callable, Iterator, List, Optional

from . import models
from .error import PatchConcretizationError
from .location import Location


class Expression(ABC):
    """
    Represents an abstract source "expression".

    `Expression` is an abstract base class whose interfaces should be consumed via
    specific base classes.
    """

    @abstractmethod
    def concretize(self, db, location: Location) -> Iterator[str]:
        yield from ()

    def view(self, db, location: Location) -> str:
        return "Expression()"


class Lit(Expression):
    """
    Represents a literal source string.

    Template authors can use this to insert pre-formed source code, or code that doesn't need
    to be concretized by location.
    """

    def __init__(self, expr: str):
        """
        Create a new `Lit` with the given source string.

        Args:
            expr: The source literal.
        """
        self.expr = expr

    def concretize(self, _db, _location) -> Iterator[str]:
        """
        Concretize this literal into its underlying source string.
        """
        yield self.expr

    def view(self, _db, _location):
        return f"Lit({self.expr})"


class Variable(Expression):
    """
    Represents an abstract source variable.
    """

    # NOTE(ww): This is probably slightly unsound, in terms of concretizations
    # produced: the set of variables in a function is not the set of variables
    # guaranteed to be in scope at a line number.
    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `Variable` into its potential names.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is a concrete variable name.

        Raises:
            PatchConcretizationError: If the scope of the variable can't be resolved.
        """

        # TODO(ww): We should also concretize with the available globals.
        function = db.function_at(location)
        if function is None:
            raise PatchConcretizationError(
                f"no function contains ({location.line}, {location.column})"
            )

        for var_decl in function.var_decls:
            yield var_decl.name

    def view(self, _db, _location) -> str:
        return "Variable()"


class StaticBufferSize(Expression):
    """
    Represents an abstract "sizeof(...)" expression.
    """

    # Query for all static array types and return list of sizeof()..
    def concretize(self, db, location: Location) -> Iterator[str]:
        """
        Concretize this `StaticBufferSize` into its potential sizes.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is a concrete `sizeof(...)` expression.

        Raises:
            PatchConcretizationError: If the scope of the location is not a function.
        """

        # TODO(ww): We should also concretize with available globals.
        function = db.function_at(location)

        if function is None:
            raise PatchConcretizationError(
                f"no function contains ({location.line}, {location.column})"
            )

        for var_decl in function.var_decls:
            if not var_decl.is_array:
                continue
            yield f"sizeof({var_decl.name})"

    def view(self, _db, _location) -> str:
        return "StaticBufferSize()"


class BinaryMathOperator(Expression):
    # Really return [+, -, /, *, <<]
    def __init__(self, lhs: Expression, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, db, location: Location) -> Iterator[str]:
        lhs_exprs = self.lhs.concretize(db, location)
        rhs_exprs = self.rhs.concretize(db, location)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} + {rhs}"
            yield f"{lhs} - {rhs}"
            yield f"{lhs} / {rhs}"
            yield f"{lhs} * {rhs}"
            yield f"{lhs} << {rhs}"

    def view(self, db, location: Location) -> str:
        return f"BinaryMathOperator({self.lhs.view(db, location)}, {self.lhs.view(db, location)})"


class BinaryBoolOperator(Expression):
    # Really return [==, !=, <=, <, >=, >]
    def __init__(self, lhs: Expression, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, db, location: Location) -> Iterator[str]:
        lhs_exprs = self.lhs.concretize(db, location)
        rhs_exprs = self.rhs.concretize(db, location)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} == {rhs}"
            yield f"{lhs} != {rhs}"
            yield f"{lhs} <= {rhs}"
            yield f"{lhs} < {rhs}"
            yield f"{lhs} >= {rhs}"
            yield f"{lhs} > {rhs}"

    def view(self, db, location: Location) -> str:
        return f"BinaryBoolOperator({self.lhs.view(db, location)}, {self.rhs.view(db, location)})"


class LessThanExpr(Expression):
    def __init__(self, lhs: Expression, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, db, location: Location) -> Iterator[str]:
        lhs_exprs = self.lhs.concretize(db, location)
        rhs_exprs = self.rhs.concretize(db, location)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} < {rhs}"

    def view(self, db, location: Location):
        self.lhs.view(db, location) + " < " + self.rhs.view(db, location)


class Statement(ABC):
    def concretize(self, db, location: Location) -> Iterator[str]:
        pass

    def view(self, db, location: Location):
        pass


class StatementList:
    def __init__(self, *args):
        self.statements: List[Statement] = []
        for arg in args:
            for i in arg:
                self.statements.append(i)

    def concretize(self, db, location: Location) -> Iterator[str]:
        concretized = [stmt.concretize(db, location) for stmt in self.statements]
        for items in set(itertools.product(*concretized)):
            yield "\n".join(items)

    def view(self, db, location: Location) -> str:
        final_str = ""
        for stmt in self.statements:
            final_str += stmt.view(db, location) + "\n"
        return final_str


class IfStmt(Statement):
    def __init__(self, cond_expr: Expression, *args):
        self.cond_expr = cond_expr
        self.statement_list = StatementList(args)

    def concretize(self, db, location: Location) -> Iterator[str]:
        cond_list = self.cond_expr.concretize(db, location)
        stmt_list = self.statement_list.concretize(db, location)
        for (cond, stmt) in itertools.product(cond_list, stmt_list):
            cand_str = "if (" + cond + ") {\n" + stmt + "\n}\n"
            yield cand_str

    def view(self, db, location: Location) -> str:
        if_str = "if (" + self.cond_expr.view(db, location) + ") {\n"
        if_str += self.statement_list.view(db, location)
        if_str += "\n}\n"
        return if_str


class ElseStmt(Statement):
    def __init__(self, *args):
        self.statement_list = StatementList(args)

    def concretize(self, db, location: Location) -> Iterator[str]:
        stmt_list = self.statement_list.concretize(db, location)
        for stmt in stmt_list:
            cand_str = "else {\n" + stmt + "\n}\n"
            yield cand_str

    def view(self, db, location: Location) -> str:
        return "else {\n" + self.statement_list.view(db, location) + "\n}\n"


class ReturnStmt(Statement):
    def __init__(self, expr: Expression):
        self.expr = expr

    def concretize(self, db, location: Location) -> Iterator[str]:
        expr_list = self.expr.concretize(db, location)
        for exp in expr_list:
            candidate_str = f"return {exp};"
            yield candidate_str

    def view(self, db, location: Location):
        return f"return {self.expr.view(db, location)};"


# TODO This should take a Node, which is something from... the DB? Maybe?
class NodeStmt(Statement):
    def concretize(self, db, location: Location) -> Iterator[str]:
        source_info = self.fetch_node(db, location)
        yield source_info

    def view(self, db, location) -> str:
        # Fetch and create a node.
        source_info = self.fetch_node(db, location)
        return source_info

    def fetch_node(self, db, location) -> str:
        """
        Fetches the statement at the given location.

        Args:
            db: The AST database to query against.
            location: The location of the statement.

        Returns:
            The statement, including trailing semicolon.

        Raises:
            PatchConcretizationError: If there is no statement at the supplied location.
        """
        statement = db.statement_at(location)
        if statement is None:
            raise PatchConcretizationError(f"no statement at ({location.line}, {location.column})")

        if statement.expr.endswith(";"):
            return statement.expr
        else:
            return f"{statement.expr};"


# Call patcher new pattern, then have the patcher add it to the list.
class FixPattern:
    # Take a *argv and just pass it to make a statement list :)
    def __init__(self, *args):
        self.statement_list = StatementList(args)

    def concretize(self, db, location: Location) -> Iterator[str]:
        yield from self.statement_list.concretize(db, location)

    def view(self, db, location: Location) -> str:
        return self.statement_list.view(db, location)


class PatchTemplate:
    # TODO Think of better API
    def __init__(
        self, fix_pattern: FixPattern, matcher_func: Optional[Callable[[int, int], bool]] = None
    ):
        self.matcher_func = matcher_func
        self.fix_pattern = fix_pattern

    def matches(self, line: int, col: int) -> bool:
        if self.matcher_func is None:
            return True
        return self.matcher_func(line, col)

    def concretize(self, db, location: Location) -> Iterator[str]:
        yield from self.fix_pattern.concretize(db, location)

    def view(self, db, location: Location) -> str:
        return self.fix_pattern.view(db, location)
