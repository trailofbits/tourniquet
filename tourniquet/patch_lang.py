from abc import ABC
from typing import List, Optional

from .node import *

"""
PatchTemplate MatcherPattern, ReplacementPattern
  FixPattern: ASTSelector

  ReplacementPattern: StmtList
  ifStmt : if ( Expression ) {
 	StmtList
  }
  ElseStmt else {
  	StmtList
  }
  returnStmt: return Expression
  StmtList: //lists are just variadic templates/functions
  		Stmt
  		Stmt StmtList

  Stmt: //Statements reduce to an anonymous function
   ifStmt
   elseStmt
   returnStmt

  Expression:
  	bufferSize <-- Some symbol denotating buffer size
    symbol <-- Some symbol like x etc
    errorReturn val
    lessThanExpr

    lessThanExpr:
  	    Expression '<' Expression
"""


class Expression(ABC):
    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        pass

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return "Expression()"


# TODO For these base types when you concretize them return a list of potential values
# by querying the DB or having some preset
class Variable(Expression):
    # Query DB for all variables within scope at the line number.
    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        # return "Variable()"
        pass

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return "Variable()"


class BufferSize(Expression):
    # Query for all static array types and return list of sizeof()..
    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        # return "BufferSize()"
        pass

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return "BufferSize()"


class ErrorReturn(Expression):
    # Trigger the error analysis or just look for returns
    # State that it cannot be found, will have to ask.
    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        # return "ErrorReturn()"
        pass

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return "ErrorReturn()"


class BinaryOperator(Expression):
    # Really return [+, -, /, *, <<]
    def __init__(self, lhs: Expression, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        pass

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return "BinaryOperator(" + self.lhs.view(line, col, db_context, module_name) \
               + "," + self.rhs.view(line, col, db_context, module_name) + ")"


class LessThanExpr(Expression):
    def __init__(self, lhs: Expression, rhs: Expression):
        self.lhs = lhs
        self.rhs = rhs

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        return self.lhs.concretize(line, col, db_context, module_name) + " < " + self.rhs.concretize(line, col,
                                                                                                     db_context,
                                                                                                     module_name)

    def view(self, line: int, col: int, db_context, module_name):
        self.lhs.view(line, col, db_context, module_name) + " < " + self.rhs.view(line, col, db_context, module_name)


class Statement(ABC):
    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        pass

    def view(self, line: int, col: int, db_context, module_name):
        pass


# TODO return List of Strings from concretize.
class StatementList:
    def __init__(self, *argv):
        self.statements = []
        for arg in argv:
            self.statements.append(arg)

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        for stmt in self.statements:
            str_result = stmt.concretize(line, col, db_context, module_name)
        return ["nop"]

    def view(self, line: int, col: int, db_context, module_name) -> str:
        final_str = ""
        for stmt in self.statements:
            final_str += stmt.view(line, col, db_context, module_name) + "\n"
        return final_str


class IfStmt(Statement):
    def __init__(self, cond_expr: Expression, statement_list: StatementList):
        self.cond_expr = cond_expr
        self.statement_list = statement_list

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        # if_str = "if (" + self.cond_expr.concretize(line, col, db_context, module_name) + ") {\n"
        # if_str += self.statement_list.concretize(line, col, db_context, module_name)
        # if_str += "}\n"
        # return if_str
        pass

    def view(self, line: int, col: int, db_context, module_name) -> str:
        if_str = "if (" + self.cond_expr.view(line, col, db_context, module_name) + ") {\n"
        if_str += self.statement_list.concretize(line, col, db_context, module_name)
        if_str += "}\n"
        return if_str


class ElseStmt(Statement):
    def __init__(self, statement_list: StatementList):
        self.statement_list = statement_list

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        # return "else {\n" + self.statement_list.concretize(line, col, db_context, module_name) + "}\n"
        pass

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return "else {\n" + self.statement_list.view(line, col, db_context, module_name) + "}\n"


class ReturnStmt(Statement):
    def __init__(self, expr: Expression):
        self.expr = expr

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        pass
        # return "return " + self.expr.concretize(line, col, db_context, module_name) + ";"

    def view(self, line: int, col: int, db_context, module_name):
        return f"return  {self.expr.view(line, col, db_context, module_name)};"


# TODO This should take a Node, which is something from... the DB? Maybe?
class NodeStmt(Statement):
    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        return ["NodeStmt()"]

    def view(self, line, col, db_context, module_name) -> str:
        # Fetch and create a node.
        return "NodeStmt()"

    def fetch_node(self, line, col, db_context, module_name) -> Node:
        cursor = db_context.cursor()
        SQL_QUERY_LINE_MAP = """
            SELECT func_name FROM '{}' WHERE line={} AND col={};
        """
        # TODO Have this be inside the new DB class later
        fetch_query = SQL_QUERY_LINE_MAP.format(
            module_name + "_line_map", line, col)
        function_info = cursor.execute(fetch_query)
        print(function_info)
        return function_info


# Call patcher new pattern, then have the patcher add it to the list.
class FixPattern:
    def __init__(self, statement_list: StatementList):
        self.statement_list = statement_list

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        return self.statement_list.concretize(line, col, db_context, module_name)

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return self.statement_list.view(line, col, db_context, module_name)


class PatchTemplate:
    # TODO Think of better API
    def __init__(self, name: str, matcher_func, fix_pattern: FixPattern):
        self.matcher_func = matcher_func
        self.fix_pattern = fix_pattern
        self.template_name = name

    def matches(self, line: int, col: int) -> bool:
        matches: bool = self.matcher_func(line, col)
        return matches

    def concretize(self, line: int, col: int) -> List[str]:
        return []

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return self.fix_pattern.view(line, col, db_context, module_name)
