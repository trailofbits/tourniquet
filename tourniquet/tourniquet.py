from typing import Dict, List
import os
import extractor
import sqlite3


class Tourniquet:
    """

    """

    def __init__(self, database_name: str):
        self.db_name = database_name

    def extract_ast(self, filepath: str) -> Dict[str, List[List[str]]]:
        # Assert file path exists
        if not os.path.exists(filepath):
            raise FileNotFoundError("Error! File not found!")
        if not os.path.isfile(filepath):
            raise FileNotFoundError("Error! This is a directory and not a file")

        result: Dict = extractor.extract_ast(filepath)
        clean_result: Dict[str, List[List[str]]] = {}
        for key in result:
            entries = result[key]
            decoded_key = key.decode("utf-8")
            clean_result[decoded_key] = []
            for entry in entries:
                clean_result[decoded_key].append(list(map(lambda x: x.decode("utf-8"), entry)))
        return clean_result
