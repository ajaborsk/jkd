import asyncio
import time
import datetime
import math

from .node import Node

class SqlDatasource(Node):
    tagname = "sql_datasource"
    def __init__(self, elt = None, database=None, username=None, password=None, **kwargs):
        import pyodbc
        self.pyodbc = pyodbc
        super().__init__(**kwargs)

