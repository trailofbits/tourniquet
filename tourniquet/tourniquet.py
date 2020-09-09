import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from . import extractor, models
from .error import PatchSituationError, TemplateNameError
from .location import Location, SourceCoordinate
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

        return extractor.extract_ast(source_path, is_cxx)

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
                        module=module,
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
        """
        Collect information about the given source file and add it to the backing database.
        """
        ast_info = self._extract_ast(source_path, is_cxx=self._path_looks_like_cxx(source_path))
        self._store_ast(ast_info)

    def register_template(self, name: str, template: PatchTemplate):
        """
        Register a patching template with the given name.
        """
        if name in self.patch_templates:
            raise TemplateNameError(f"a template has already been registered as {name}")
        self.patch_templates[name] = template

    # TODO Should take  target
    # TODO(ww): Consider rehoming this?
    def view_template(self, template_name, location: Location) -> Optional[str]:
        """
        Pretty-print the given template, partially concretized to the given
        module and source location.
        """
        template = self.patch_templates.get(template_name)
        if template is None:
            return None

        print("=" * 10, template_name, "=" * 10)
        view_str = template.view(self.db, location)
        print(view_str)
        print("=" * 10, "END", "=" * 10)
        return view_str

    # TODO Should take a target
    def concretize_template(self, template_name: str, location: Location) -> Iterator[str]:
        """
        Concretize the given registered template to the given
        module and source location, yielding each candidate patch.

        Args:
            template_name: The name of the template to concretize. This name
                must have been previously registered with `register_template`.
            location: The `Location` to concretize the template at.

        Returns:
            A generator of strings, each one representing a concrete patch suitable
            for placement at the supplied location.

        Raises:
            TemplateNameError: If the supplied template name isn't registered.
        """
        template = self.patch_templates.get(template_name)
        if template is None:
            raise TemplateNameError(f"no template registed with name {template_name}")

        yield from template.concretize(self.db, location)

    # TODO Should take a target
    # TODO(ww): This should take a span instead of a location, so that it doesn't have
    # to depend on the patch location being a statement.
    @contextmanager
    def patch(self, replacement: str, location: Location) -> Iterator[bool]:
        """
        Applies the given replacement to the given location.

        Rolls back the replacement after context closure.

        Args:
            replacement: The patch to insert.
            location: The `Location` to insert at, including the source file.

        Returns:
            A generator whose single yield is the status of the replacement operation.

        Raises:
            PatchSituationError: If the supplied location can't be used for a patch.
        """
        try:
            temp_file = tempfile.NamedTemporaryFile()
            shutil.copyfile(location.filename, temp_file.name)

            statement = self.db.statement_at(location)
            if statement is None:
                raise PatchSituationError(f"no statement at ({location.line}, {location.column})")

            yield self.transform(
                location.filename,
                replacement,
                statement.start_coordinate,
                statement.end_coordinate,
            )
        finally:
            shutil.copyfile(temp_file.name, location.filename)
            temp_file.close()

    # TODO Should take a target
    def auto_patch(self, template_name, tests, location: Location) -> Optional[str]:
        # TODO(ww): This should be a NamedTempFile, at the absolute minimum.
        EXEC_FILE = Path("/tmp/target")

        # Collect replacements
        replacements = self.concretize_template(template_name, location)

        # Patch
        for replacement in replacements:
            with self.patch(replacement, location):
                # Just compile with clang for now
                ret = subprocess.call(["clang", "-g", "-o", EXEC_FILE, location.filename])
                if ret != 0:
                    print("Error, build failed?")
                    continue

                # Run the test suite
                failed_test = False
                for test_case in tests:
                    (input_, output) = test_case
                    ret = subprocess.call([EXEC_FILE, input_])
                    if output != ret:
                        failed_test = True
                        break
                if not failed_test:
                    # This means that its fixed :)
                    return replacement

        return None

    def transform(
        self, filename: Path, replacement: str, start: SourceCoordinate, end: SourceCoordinate
    ):
        res = extractor.transform(
            filename,
            self._path_looks_like_cxx(filename),
            replacement,
            start.line,
            start.column,
            end.line,
            end.column,
        )
        return res
