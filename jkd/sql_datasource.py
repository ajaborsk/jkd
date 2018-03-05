import asyncio
import time
import datetime
import math
from functools import partial

from .node import Node

class SqlDatasource(Node):
    tagname = "sql_datasource"
    def __init__(self, elt = None, database=None, username=None, password=None, **kwargs):
        import pyodbc
        self.pyodbc = pyodbc
        super().__init__(**kwargs)
        
        self.cnx = pyodbc.connect("DSN={};UID={};PWD={}".format(database, username, password))
        
        for el in elt:
            if el.tag == 'query':
                name = el.attrib['name']
                query = el.text
                self.port_add(name)
                self.task_add(name, partial(self.sql_query, query = query), returns = ['test0'])
        
    async def sql_query(self, query = None):
        cols = []
        resp = []
        cur = self.cnx.cursor()
        try:
            cur.execute(query)
            self.debug(str(cur))
            self.debug(str(cur.description))
            for desc in cur.description:
                cols.append({'title':desc[0]})
            for row in cur.fetchall():
                resp.append(list(row))
            self.debug('response length: ' + str(len(resp)))
        except:
            pass
        return {'cols':cols, 'data':resp, 'query':query}

