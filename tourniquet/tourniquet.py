import os
import subprocess
from typing import Any, Dict, Iterator, List, Optional

import extractor

from . import models
from .patch_lang import PatchTemplate


# TODO Make DB class to pass around instead of connection.
class Tourniquet:
    SQL_CREATE_MODULES_TABLE = """
        CREATE TABLE IF NOT EXISTS '{}' (
            id INTEGER PRIMARY KEY,
            function_name nvarchar NOT NULL
        );
    """
    SQL_INSERT_MOD_TABLE = """
        INSERT INTO '{}' (function_name) VALUES ('{}')
    """

    SQL_CREATE_FUNC_TABLE = """
            CREATE TABLE IF NOT EXISTS '{}' (
            id INTEGER PRIMARY KEY,
            entry_type nvarchar NOT NULL,
            data json NOT NULL,
            line int NOT NULL,
            col int NOT NULL,
            end_line int NOT NULL,
            end_col int NOT NULL
        );
    """
    # This table is to easily map line,col --> func_table
    SQL_CREATE_LINE_MAP_TABLE = """
        CREATE TABLE IF NOT EXISTS '{}' (
        id INTEGER PRIMARY KEY,
        line int NOT NULL,
        col int NOT NULL,
        func_name nvarchar NOT NULL
        );
    """
    SQL_INSERT_LINE_MAP_TABLE = """
        INSERT INTO '{}' (line, col, func_name) VALUES ('{}', '{}', '{}');
    """
    SQL_QUERY_LINE_MAP = """
        SELECT func_name FROM '{}' WHERE line={} AND col={};
    """
    SQL_QUERY_FUNC_ENTRY = """
        SELECT (entry_type, data) FROM '{}' WHERE line={} and col={};
    """
    SQL_INSERT_FUNC_ENTRY = """
        INSERT INTO '{}' (entry_type, data, line, col, end_line, end_col)
        VALUES ( '{}', '{}', '{}', '{}', '{}', '{}')
    """

    def __init__(self, database_name):
        self.db_name = database_name
        self.db = models.DB.create(database_name)
        self.patch_templates: List[PatchTemplate] = []

    def _extract_ast(self, filepath: str) -> Dict[str, Any]:
        # Assert file path exists
        if not os.path.exists(filepath):
            raise FileNotFoundError("Error! File not found!")
        if not os.path.isfile(filepath):
            raise FileNotFoundError("Error! This is a directory and not a file")

        return extractor.extract_ast(filepath)

    # def _create_module_table(self, table_name: str) -> int:
    #     cursor = self.db_conn.cursor()
    #     cursor.execute(self.SQL_CREATE_MODULES_TABLE.format(table_name))
    #     self.db_conn.commit()
    #     return cursor.lastrowid

    # # The way to relate to this table is via a string
    # def _create_global_table(self, module_name) -> str:
    #     cursor = self.db_conn.cursor()
    #     global_query = self.SQL_CREATE_FUNC_TABLE.format(module_name + "_globals")
    #     cursor.execute(global_query)
    #     self.db_conn.commit()
    #     return module_name + "_globals"

    # def _create_line_map_table(self, module_name) -> str:
    #     cursor = self.db_conn.cursor()
    #     map_query = self.SQL_CREATE_LINE_MAP_TABLE.format(module_name + "_line_map")
    #     cursor.execute(map_query)
    #     self.db_conn.commit()
    #     return module_name + "_line_map"

    # def _create_function_table(self, table_name: str, table_entries) -> None:
    #     cursor = self.db_conn.cursor()
    #     table_create_query = self.SQL_CREATE_FUNC_TABLE.format(table_name)
    #     cursor.execute(table_create_query)
    #     for entry in table_entries:
    #         entry_type = entry[len(entry) - 1]
    #         start_line = entry[0]
    #         start_col = entry[1]
    #         end_line = entry[2]
    #         end_col = entry[3]
    #         query = self.SQL_INSERT_FUNC_ENTRY.format(
    #             table_name, entry_type, json.dumps(entry), start_line, start_col, end_line, end_col
    #         )
    #         cursor.execute(query)
    #     self.db_conn.commit()

    # # Create module table
    # # TODO take module name from extractor
    # def _store_ast(self, ast_info: Dict[str, Any]) -> None:
    #     module_name: str = ast_info["module_name"]
    #     self._create_module_table(module_name)
    #     # create global table
    #     self._create_global_table(module_name)
    #     line_map_table = self._create_line_map_table(module_name)
    #     # Table for each function (maybe some symbol issues)
    #     cursor = self.db_conn.cursor()
    #     for func_key in ast_info:
    #         if func_key == "global" or func_key == "module_name":
    #             continue
    #         self._create_function_table(func_key, ast_info[func_key])
    #         mod_insert_query = self.SQL_INSERT_MOD_TABLE.format(module_name, func_key)
    #         # print(mod_insert_query)
    #         cursor.execute(mod_insert_query)
    #         entry_info = ast_info[func_key]
    #         for entry in entry_info:
    #             start_line = entry[0]
    #             start_col = entry[1]
    #             line_map_query = self.SQL_INSERT_LINE_MAP_TABLE.format(
    #                 line_map_table, start_line, start_col, func_key
    #             )
    #             cursor.execute(line_map_query)
    #         self.db_conn.commit()

    def _store_ast(self, ast_info: Dict[str, Any]):
        module = models.Module(name=ast_info["module_name"])
        for global_ in ast_info["globals"]:
            assert global_[0] == "var_type", f"{global_[0]} != var_type"
            global_ = models.Global(
                module=module,
                name=global_[5],
                type_=global_[6],
                start_line=global_[1],
                start_column=global_[2],
                end_line=global_[3],
                end_column=global_[4],
                is_array=bool(global_[7]),
                size=global_[8],
            )
            self.db.session.add(global_)

        # Every subsequent member
        for func_name, exprs in ast_info["functions"].items():
            # NOTE(ww): We expected the first member of each function's list to be
            # a "func_decl" list, containing information about the function declaration
            # itself. We use this to construct the initial Function model.
            func_decl = next(exprs)
            assert func_decl[0] == "func_decl", f"{func_decl[0]} != func_decl"

            function = models.Function(
                module=module,
                start_line=func_decl[1],
                start_column=func_decl[2],
                end_line=func_decl[3],
                end_column=func_decl[4],
            )
            self.db.session.add(function)

            for expr in exprs:
                # From here, the exprs we know are "var_type" (models.VarDecl),
                # "call_type" (models.Call), and "stmt_type" (models.Statement).
                # "call_type" lists contain, in turn, a list of arguments,
                # which we promote to models.Argument objects.
                if expr[0] == "var_type":
                    var_decl = models.VarDecl(
                        function=function,
                        name=expr[5],
                        type_=expr[6],
                        start_line=expr[1],
                        start_column=expr[2],
                        end_line=expr[3],
                        end_column=expr[4],
                        is_array=bool(expr[7]),
                        size=expr[8],
                    )
                    self.db.session.add(var_decl)
                elif expr[0] == "call_type":
                    call = models.Call(
                        function=function,
                        expr=expr[5],
                        name=expr[6],
                        start_line=expr[1],
                        start_column=expr[2],
                        end_line=expr[3],
                        end_column=expr[4],
                    )
                    self.db.session.add(call)
                    # TODO(ww): Argument mdoels.
                elif expr[0] == "stmt_type":
                    pass
                else:
                    assert False, expr[0]

        self.db.session.commit()

    # TODO Should take a target
    def collect_info(self, filepath: str):
        ast_info = self._extract_ast(filepath)
        self._store_ast(ast_info)

    def add_new_template(self, template: PatchTemplate):
        self.patch_templates.append(template)

    def print_template_names(self):
        for template in self.patch_templates:
            print(template.template_name)

    # TODO Should take  target
    def view_template(self, module_name, template_name, line: int, col: int) -> Optional[str]:
        for template in self.patch_templates:
            if template.template_name == template_name:
                print("=" * 10, template_name, "=" * 10)
                view_str = template.view(line, col, self.db, module_name)
                print(view_str)
                print("=" * 10, "END", "=" * 10)
                return view_str
        return None

    # TODO Should take a target
    def concretize_template(self, module_name, template_name, line, col) -> Iterator[str]:
        for template in self.patch_templates:
            if template.template_name == template_name:
                yield from template.concretize(line, col, self.db, module_name)
        yield from ()

    # TODO Should take a target
    def patch(self, file_path, replacement: str, line: int, col: int) -> bool:
        # Query for end_line/end_col
        cursor = self.db_conn.cursor()
        SQL_QUERY_LINE_MAP = """
                        SELECT func_name FROM '{}' WHERE line={} AND col={};
                    """
        # TODO Have this be inside the new DB class later
        fetch_query = SQL_QUERY_LINE_MAP.format(file_path + "_line_map", line, col)
        cursor.execute(fetch_query)
        function_info = cursor.fetchall()
        # Could be more than once match
        func_name = function_info[0][0]
        SQL_QUERY_FUNC_ENTRY = """
            SELECT end_line, end_col FROM '{}' WHERE line={} and col={};
        """
        fetch_entry_query = SQL_QUERY_FUNC_ENTRY.format(func_name, line, col)
        cursor.execute(fetch_entry_query)
        line_info = cursor.fetchall()
        # TODO have a better way of resolving this
        end_line, end_col = line_info[0]
        return self.transform(file_path, replacement, line, col, end_line, end_col)

    # TODO Should take a target
    def auto_patch(self, file_path, tests, template_name, line, col) -> bool:
        # Save the current file to tmp
        TEMP_FILE = "/tmp/save_file"
        EXEC_FILE = "/tmp/target"
        ret = subprocess.call(["cp", file_path, TEMP_FILE])
        if ret != 0:
            print("Failed to save copy of original file")
            return False

        # Collect replacements
        replacements = self.concretize_template(file_path, template_name, line, col)

        # Patch
        for replacement in replacements:
            # Copy file back over to reset
            ret = subprocess.call(["cp", TEMP_FILE, file_path])
            if ret != 0:
                print("Failed to copy saved file back to original location")
                return False

            self.patch(file_path, replacement, line, col)

            # Just compile with clang for now
            ret = subprocess.call(["clang-9", "-g", "-o", EXEC_FILE, file_path])
            if ret != 0:
                print("Error, build failed?")
                continue
            # Run the test suite
            failed_test = False
            for test_case in tests:
                input = test_case[0]
                output = test_case[1]
                ret = subprocess.call([EXEC_FILE, input])
                if output != ret:
                    failed_test = True
                    break
            if not failed_test:
                # This means that its fixed :)
                return True

        ret = subprocess.call(["cp", TEMP_FILE, file_path])
        if ret != 0:
            print("Failed to copy saved file back to original location")
            return False
        return False

    def transform(self, filename, replacement, start_line, start_col, end_line, end_col):
        res = extractor.transform(filename, replacement, start_line, start_col, end_line, end_col)
        return res

    # TODO Autopatch
    # TODO Integrate with CPG
    # def create_new_template(self, matcher_func, statement_list: StatementList):
    #    new_fix_pattern = FixPattern(statement_list)
    #    patch_t = PatchTemplate(matcher_func, new_fix_pattern)
    #    self.patch_templates.append((template_name, patch_t))
