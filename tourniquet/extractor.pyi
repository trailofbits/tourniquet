from os import PathLike
from typing import Any, Dict

def extract_ast(filename: PathLike, is_cxx: bool) -> Dict[str, Any]: ...
def transform(
    filename: PathLike,
    is_cxx: bool,
    replacement: str,
    start_line: int,
    start_col: int,
    end_line: int,
    end_col: int,
): ...
