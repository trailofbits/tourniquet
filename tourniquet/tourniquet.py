from typing import Dict, List
import os
import extractor
import sqlite3
from sqlite3 import Error
import logging


class Tourniquet:
    SQL_CREATE_MODULES_TABLE = """ 
        CREATE TABLE IF NOT EXISTS {} (
            func_id int NOT NULL AUTO_INCREMENT,
            function_name nvarchar NOT NULL,
            function_table_id int NOT NULL 
        PRIMARY KEY (func_id)
        ); 
    """
    SQL_CREATE_FUNCTION_TABLE = """
        CREATE TABLE IF NOT EXISTS {} (
            function_table_id int NOT NULL AUTO_INCREMENT,
            function_name nvarchar NOT NULL, 
            var_table int, 
            stmt_table int,
            global_vars_table int,
        PRIMARY KEY(function_table_id) 
        );
    """
    SQL_CREATE_VAR_TABLE = """
        CREATE TABLE IF NOT EXISTS {} (
            id int NOT NULL AUTO_INCREMENT, 
            name nvarchar NOT NULL, 
            var_type int NOT NULL, 
            is_array int NOT NULL, 
            var_size int NOT NULL,
        PRIMARY_KEY(id) 
        );
    """
    SQL_CREATE_STMT_TABLE = """
        CREATE TABLE IF NOT EXISTS {} (
            id int NOT NULL AUTO_INCREMENT, 
            stmt_type int NOT NULL, 
            json_blob json NOT NULL,
        PRIMARY_KEY(id)
        );
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

    def create_var_table(self, table_name: str, table_entries: List[str]) -> None:
        cursor = self.db_conn.cursor()
        # Create new table
        cursor.execute(self.SQL_CREATE_VAR_TABLE.format(table_name))

    def store_ast(self, ast_info: Dict[str, List[List[str]]]) -> None:
        # Table for each function (maybe some symbol issues)
        for func_key in ast_info:
            if func_key == "global":


        # Inside each function table there are all the variables
        # and references to stmt tables
        return
