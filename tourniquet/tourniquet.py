from typing import Dict, List
import os
import extractor
import sqlite3
from sqlite3 import Error
import logging
import json


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
            data json NOT NULL
        );
    """
    SQL_INSERT_FUNC_ENTRY = """
        INSERT INTO '{}' (entry_type, data) VALUES ( '{}', '{}' )
    """

    def __init__(self, database_name: str):
        self.db_name = database_name
        self.db_conn = None
        self.logger = logging.getLogger("tourniquet")
        self.create_db(self.db_name)

    def create_db(self, db_name: str) -> None:
        # Connect to DB
        try:
            self.db_conn = sqlite3.connect(db_name)
        # Raise exception if can't get the DB
        except Error:
            self.logger.error(self, f"Error! Could not connect to database: {db_name}")
            raise

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

    def create_module_table(self, table_name: str) -> int:
        cursor = self.db_conn.cursor()
        cursor.execute(self.SQL_CREATE_MODULES_TABLE.format(table_name))
        self.db_conn.commit()
        return cursor.lastrowid

    # The way to relate to this table is via a string
    def create_global_table(self, module_name) -> str:
        cursor = self.db_conn.cursor()
        cursor.execute(self.SQL_CREATE_FUNC_TABLE.format(module_name + "_globals"))
        self.db_conn.commit()
        return module_name + "_globals"

    def create_function_table(self, table_name: str, table_entries) -> None:
        cursor = self.db_conn.cursor()
        table_create_query = self.SQL_CREATE_FUNC_TABLE.format(table_name)
        print(table_create_query)
        cursor.execute(table_create_query)
        for entry in table_entries:
            print("ENTRY IS ", entry)
            print("TABLE ENTRY IS", table_entries)
            entry_type = entry[len(entry) - 1]
            print(entry_type)
            query = self.SQL_INSERT_FUNC_ENTRY.format(table_name, entry_type, json.dumps(entry))
            print(query)
            cursor.execute(query)
        self.db_conn.commit()

    def store_ast(self, ast_info: Dict[str, List[List[str]]]) -> None:
        # Create module table
        module_name = "test_name"
        self.create_module_table(module_name)
        # create global table
        global_table = self.create_global_table(module_name)
        # Table for each function (maybe some symbol issues)
        cursor = self.db_conn.cursor()
        for func_key in ast_info:
            if func_key == "global":
                continue
            self.create_function_table(func_key, ast_info[func_key])
            mod_insert_query = self.SQL_INSERT_MOD_TABLE.format(module_name, func_key)
            print(mod_insert_query)
            cursor.execute(mod_insert_query)
            self.db_conn.commit()
        return
