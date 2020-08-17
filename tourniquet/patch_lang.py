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
    def __init__(self, *args):
        self.statements = []
        for arg in args:
            print(arg)
            print("Appending arg!")
            self.statements.append(*arg)

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        """
         ifStmt(), elseStmt()
         ifStmt().concretize = List[]..
         elseStmt().concretize = List[]..

         [] <- empty list
         read first list
         [c1, c2, c3]
         second
         [c1d1, c1d2, c1d3]
        """
        ret_list = []
        temp_list = []
        for stmt in self.statements:
            temp_result = stmt.concretize(line, col, db_context, module_name)
            # if temp_list is empty
            if len(temp_list) == 0:
                for x in temp_result:
                    temp_list.append(x)
            # if there is stuff in it, we must make permutations
            else:
                new_list = []
                for item in temp_list:
                    for new in temp_result:
                        new_list.append(f"{item}\n{new}")
                # Update list
                temp_list = new_list
        return ret_list

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


# TODO Same here, make these take a *args
class ElseStmt(Statement):
    def __init__(self, statement_list: StatementList):
        self.statement_list = statement_list

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        ret_list = []
        stmt_list = self.statement_list.concretize(line, col, db_context, module_name)
        for stmt in stmt_list:
            cand_str = "else {\n" + stmt + "}\n"
            ret_list.append(cand_str)
        return ret_list

    def view(self, line: int, col: int, db_context, module_name) -> str:
        return "else {\n" + self.statement_list.view(line, col, db_context, module_name) + "}\n"


class ReturnStmt(Statement):
    def __init__(self, expr: Expression):
        self.expr = expr

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        ret_list = []
        expr_list = self.expr.concretize(line, col, db_context, module_name)
        for exp in expr_list:
            candidate_str = f"return {exp};"
            ret_list.append(candidate_str)
        return ret_list

    def view(self, line: int, col: int, db_context, module_name):
        return f"return  {self.expr.view(line, col, db_context, module_name)};"


# TODO This should take a Node, which is something from... the DB? Maybe?
class NodeStmt(Statement):
    def __init__(self):
        return

    def concretize(self, line: int, col: int, db_context, module_name) -> List[str]:
        source_info = self.fetch_node(line, col, db_context, module_name)
        return [source_info]

    def view(self, line, col, db_context, module_name) -> str:
        # Fetch and create a node.
        source_info = self.fetch_node(line, col, db_context, module_name)
        return source_info

    def fetch_node(self, line, col, db_context, module_name) -> str:
        cursor = db_context.cursor()
        SQL_QUERY_LINE_MAP = """
            SELECT func_name FROM '{}' WHERE line={} AND col={};
        """
        # TODO Have this be inside the new DB class later
        fetch_query = SQL_QUERY_LINE_MAP.format(
            module_name + "_line_map", line, col)
        cursor.execute(fetch_query)
        function_info = cursor.fetchall()
        # Could be more than once match
        func_name = function_info[0][0]
        SQL_QUERY_FUNC_ENTRY = """
        SELECT entry_type, data FROM '{}' WHERE line={} and col={};
    """
        fetch_entry_query = SQL_QUERY_FUNC_ENTRY.format(func_name, line, col)
        cursor.execute(fetch_entry_query)
        entry_info = cursor.fetchall()
        # If there is multiple matches, select first one
        # The DB stored the array as a string
        # Convert back into an array
        arr_string = entry_info[0][1]
        source_list = arr_string[1:len(arr_string) - 1].split(",")
        # Todo have a parser for these types of things
        return source_list[2]


# Call patcher new pattern, then have the patcher add it to the list.
class FixPattern:
    # Take a *argv and just pass it to make a statement list :)
    def __init__(self, *args):
        self.statement_list = StatementList(args)

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
