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
    specific derived classes.
    """

    @abstractmethod
    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        yield from ()

    def view(self, db: models.DB, location: Location) -> str:
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
            expr: The source literal
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
            A generator of strings, each of which is a concrete variable name

        Raises:
            PatchConcretizationError: If the scope of the variable can't be resolved
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
    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `StaticBufferSize` into its potential sizes.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is a concrete `sizeof(...)` expression

        Raises:
            PatchConcretizationError: If the scope of the location is not a function
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
    """
    Represents the possible binary math operators, along with their lhs and rhs expressions.
    """

    def __init__(self, lhs: Expression, rhs: Expression):
        """
        Create a new `BinaryMathOperator` with the given `lhs` and `rhs`.

        Args:
            lhs: An `Expression` to use for the left-hand side
            rhs: An `Expression` to use for the right-hand side
        """
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `BinaryMathOperator` into its possible operator expressions.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is a concrete binary math expression
        """
        lhs_exprs = self.lhs.concretize(db, location)
        rhs_exprs = self.rhs.concretize(db, location)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} + {rhs}"
            yield f"{lhs} - {rhs}"
            yield f"{lhs} / {rhs}"
            yield f"{lhs} * {rhs}"
            yield f"{lhs} << {rhs}"
            # TODO(ww): Missing for unknown reasons: >>, &, |, ^, %

    def view(self, db: models.DB, location: Location) -> str:
        return f"BinaryMathOperator({self.lhs.view(db, location)}, {self.lhs.view(db, location)})"


class BinaryBoolOperator(Expression):
    """
    Represents the possible binary boolean operators, along with their lhs and rhs expressions.
    """

    def __init__(self, lhs: Expression, rhs: Expression):
        """
        Create a new `BinaryBoolOperator` with the given `lhs` and `rhs`.

        Args:
            lhs: An `Expression` to use for the left-hand side
            rhs: An `Expression` to use for the right-hand side
        """
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `BinaryBoolOperator` into its possible operator expressions.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is a concrete binary boolean expression
        """
        lhs_exprs = self.lhs.concretize(db, location)
        rhs_exprs = self.rhs.concretize(db, location)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} == {rhs}"
            yield f"{lhs} != {rhs}"
            yield f"{lhs} <= {rhs}"
            yield f"{lhs} < {rhs}"
            yield f"{lhs} >= {rhs}"
            yield f"{lhs} > {rhs}"
            # TODO(ww): If location is in a C++ source file, maybe add <=>

    def view(self, db: models.DB, location: Location) -> str:
        return f"BinaryBoolOperator({self.lhs.view(db, location)}, {self.rhs.view(db, location)})"


class LessThanExpr(Expression):
    """
    Represents the less-than boolean operator, along with its lhs and rhs expressions.
    """

    def __init__(self, lhs: Expression, rhs: Expression):
        """
        Create a new `LessThanExpr` with the given `lhs` and `rhs`.

        Args:
            lhs: An `Expression` to use for the left-hand side.
            rhs: An `Expression` to use for the right-hand side.
        """
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `LessThanExpr` into its possible operator expressions.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is a concrete less-than boolean expression
        """

        lhs_exprs = self.lhs.concretize(db, location)
        rhs_exprs = self.rhs.concretize(db, location)
        for (lhs, rhs) in itertools.product(lhs_exprs, rhs_exprs):
            yield f"{lhs} < {rhs}"

    def view(self, db: models.DB, location: Location):
        self.lhs.view(db, location) + " < " + self.rhs.view(db, location)


class Statement(ABC):
    """
    Represents an source "statement".

    `Statement` is an abstract base whose interfaces should be consumed via specific
    derived classes.
    """

    @abstractmethod
    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        pass

    @abstractmethod
    def view(self, db: models.DB, location: Location):
        pass


class StatementList:
    """
    Represents a sequence of statements.
    """

    def __init__(self, *args):
        self.statements: List[Statement] = args

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `StatementList` into its possible statement seqences.

        This involves concretizing each statement and taking their unique
        product, such that every possible permutation of statements in the list
        is produced.

        Args:
            db: The AST database to concretize against
            locaton: The location to concretize at

        Returns:
            A generator of strings, each of which is a concreqte sequence of statements
        """
        concretized = [stmt.concretize(db, location) for stmt in self.statements]
        for items in set(itertools.product(*concretized)):
            yield "\n".join(items)

    def view(self, db: models.DB, location: Location) -> str:
        final_str = ""
        for stmt in self.statements:
            final_str += stmt.view(db, location) + "\n"
        return final_str


class IfStmt(Statement):
    """
    Represents an `if(...) { ... }` statement.
    """

    def __init__(self, cond_expr: Expression, *args: List[Statement]):
        """
        Creates a new `IfStmt`.

        Args:
            cond_expr: The expression to evaluate
            args: The statements to use in the body of the `if`
        """
        self.cond_expr = cond_expr
        self.statement_list = StatementList(*args)

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `IfStmt` into its possible statements.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is an `if` statement
        """
        cond_list = self.cond_expr.concretize(db, location)
        stmt_list = self.statement_list.concretize(db, location)
        for (cond, stmt) in itertools.product(cond_list, stmt_list):
            cand_str = "if (" + cond + ") {\n" + stmt + "\n}\n"
            yield cand_str

    def view(self, db: models.DB, location: Location) -> str:
        if_str = "if (" + self.cond_expr.view(db, location) + ") {\n"
        if_str += self.statement_list.view(db, location)
        if_str += "\n}\n"
        return if_str


class ElseStmt(Statement):
    """
    Represents an `else { ... }` statement.
    """

    def __init__(self, *args: List[Statement]):
        """
        Creates a new `ElseStmt`.

        Args:
            args: The statements to use in the body of the `else`
        """

        self.statement_list = StatementList(*args)

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `ElseStmt` into its possible statements.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is an `else` statement
        """
        stmt_list = self.statement_list.concretize(db, location)
        for stmt in stmt_list:
            cand_str = "else {\n" + stmt + "\n}\n"
            yield cand_str

    def view(self, db: models.DB, location: Location) -> str:
        return "else {\n" + self.statement_list.view(db, location) + "\n}\n"


class ReturnStmt(Statement):
    """
    Represents a `return ...;` statement.
    """

    def __init__(self, expr: Expression):
        """
        Creates a new `ReturnStmt`.

        Args:
            expr: The expression to concretize for the `return`
        """
        self.expr = expr

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `ReturnStmt` into its possible statements.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is an `return` statement
        """
        expr_list = self.expr.concretize(db, location)
        for exp in expr_list:
            candidate_str = f"return {exp};"
            yield candidate_str

    def view(self, db: models.DB, location: Location):
        return f"return {self.expr.view(db, location)};"


# TODO This should take a Node, which is something from... the DB? Maybe?
# TODO(ww): This should probably be renamed to ASTStmt or similar.
class NodeStmt(Statement):
    """
    Represents a statement from the AST database, identified by location.
    """

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `NodeStmt` into its concrete statement.

        Args:
            db: The AST database to concretize against
            location: The statement's location

        Returns:
            A generator of strings, whose single item is the extracted AST statement
        """
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


class FixPattern:
    """
    Represents a program "fix" that can be concretized into a sequence of candidate patches.
    """

    def __init__(self, *args: List[Statement]):
        """
        Create a new `FixPattern`.

        Args:
            args: The statements to use in the fix
        """
        self.statement_list = StatementList(*args)

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize this `FixPattern` into a sequence of candidate patches.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is a candidate patch
        """
        yield from self.statement_list.concretize(db, location)

    def view(self, db: models.DB, location: Location) -> str:
        return self.statement_list.view(db, location)


class PatchTemplate:
    """
    Represents a templatized patch, including a matcher callable.
    """

    def __init__(
        self, fix_pattern: FixPattern, matcher_func: Optional[Callable[[int, int], bool]] = None
    ):
        """
        Create a new `PatchTemplate`.

        Args:
            fix_pattern: The fix pattern to concretize into patches
            matcher_func: The callable to filter patch locations with, if any
        """
        self.matcher_func = matcher_func
        self.fix_pattern = fix_pattern

    def matches(self, line: int, col: int) -> bool:
        """
        Returns whether the given line and column is suitable for patch situation.

        Calls `self.matcher_func` internally, if supplied.

        Args:
            line: The line to patch on
            column: The column to patch on

        Returns:
            `True` if `matcher_func` was not supplied or returns `True`, `False` otherwise
        """
        if self.matcher_func is None:
            return True
        return self.matcher_func(line, col)

    def concretize(self, db: models.DB, location: Location) -> Iterator[str]:
        """
        Concretize the inner `FixPattern` into a sequence of patch candidates.

        Args:
            db: The AST database to concretize against
            location: The location to concretize at

        Returns:
            A generator of strings, each of which is a candidate patch
        """

        yield from self.fix_pattern.concretize(db, location)

    def view(self, db: models.DB, location: Location) -> str:
        return self.fix_pattern.view(db, location)
