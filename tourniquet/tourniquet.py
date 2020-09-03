import subprocess
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import extractor

from . import models
from .patch_lang import PatchTemplate


class Tourniquet:
    def __init__(self, database_name):
        self.db_name = database_name
        self.db = models.DB.create(database_name)
        self.patch_templates: Dict[str, PatchTemplate] = {}

    def _path_looks_like_cxx(self, source_path: Path):
        return source_path.suffix in [".cpp", ".cc", ".cxx"]

    def _extract_ast(self, source_path: Path, is_cxx: bool = True) -> Dict[str, Any]:
        if not source_path.is_file():
            raise FileNotFoundError(f"{source_path} is not a file")

        return extractor.extract_ast(str(source_path), is_cxx)

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
            # If a list doesn't begin with "func_decl," then it was external and we
            # skip it.
            # TODO(ww): Think more about the above.
            exprs = iter(exprs)
            func_decl = next(exprs)
            if func_decl[0] != "func_decl":
                continue

            function = models.Function(
                module=module,
                name=func_name,
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

                    for name, type_ in expr[7:]:
                        argument = models.Argument(call=call, name=name, type_=type_)
                        self.db.session.add(argument)
                elif expr[0] == "stmt_type":
                    stmt = models.Statement(
                        module=module,
                        function=function,
                        expr=expr[5],
                        start_line=expr[1],
                        start_column=expr[2],
                        end_line=expr[3],
                        end_column=expr[4],
                    )
                    self.db.session.add(stmt)
                else:
                    assert False, expr[0]

        self.db.session.commit()

    # TODO Should take a target
    def collect_info(self, source_path: Path):
        ast_info = self._extract_ast(source_path, is_cxx=self._path_looks_like_cxx(source_path))
        self._store_ast(ast_info)

    def register_template(self, name: str, template: PatchTemplate):
        if name in self.patch_templates:
            raise ValueError(f"a template has already been registered as {name}")
        self.patch_templates[name] = template

    # TODO Should take  target
    # TODO(ww): Consider rehoming this?
    def view_template(self, module_name, template_name, line: int, col: int) -> Optional[str]:
        template = self.patch_templates.get(template_name)
        if template is None:
            return None

        print("=" * 10, template_name, "=" * 10)
        view_str = template.view(line, col, self.db, module_name)
        print(view_str)
        print("=" * 10, "END", "=" * 10)
        return view_str

    # TODO Should take a target
    def concretize_template(self, module_name, template_name, line, col) -> Iterator[str]:
        template = self.patch_templates.get(template_name)
        if template is None:
            # TODO(ww): Custom error.
            raise ValueError(f"no template registed with name {template_name}")

        yield from template.concretize(line, col, self.db, module_name)

    # TODO Should take a target
    def patch(self, file_path, replacement: str, line: int, col: int) -> bool:
        function = (
            self.db.query(models.Function)
            .filter_by(start_line=line, start_column=col)
            .one_or_none()
        )

        if function is None:
            # TODO(ww): Come up with an appropriate exception here.
            raise ValueError(f"no function at ({line}, {col})")

        return self.transform(
            file_path,
            replacement,
            function.start_line,
            function.start_column,
            function.end_line,
            function.end_column,
        )

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
