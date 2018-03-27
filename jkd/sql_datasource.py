import asyncio
import time
import datetime
import math
import string
import pandas as pd
import decimal

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
                query = "".join(el.itertext())
                col_ops = []
                for subel in el:
                    if subel.tag == 'column':
                        col_ops.append(dict(subel.attrib))
                self.port_add(name)
                self.task_add(name, partial(self.sql_query, query = query, col_ops = col_ops), returns = [el.attrib['name']])

    async def sql_query(self, query = None, col_ops = [], args={}):
        self.debug("Query: "+str(query))
        cols = []
        resp = []
        cur = self.cnx.cursor()
        try:
            cur.execute(query)
            #self.debug(str(cur))
            #self.debug(str(cur.description))
            for desc in cur.description:
                cols.append({'title':desc[0]})
            for row in cur.fetchall():
                #self.debug(repr(row))
                #self.debug(str(list(row)))
                resp.append(list(row))
            self.debug('response length: ' + str(len(resp)))
        except:
            pass

        df = pd.DataFrame(resp, columns=[c['title'] for c in cols])
        
#        for col in range(len(df.columns)):
#            self.debug(str(cur.description[col]))
#            if cur.description[col][1] == decimal.Decimal:
#                df[df.columns[col]] = pd.to_numeric(df[df.columns[col]])/100. 
        
        for col_op in col_ops:
            #test_code
            #if col_op['name'] == 'Appel':
            #    df['Appel'] = pd.to_datetime(df['DA_AP']+' '+df['HE_AP'].str[0:2]+":"+df['HE_AP'].str[2:4])        
            args = {}
            for fmt in string.Formatter().parse(col_op['value']):
                if fmt[1] is not None:
                    args[fmt[1]] = 'df["{}"]'.format(fmt[1])
            self.debug(str(args))
            value = eval(col_op['value'].format(**args), None, {'df':df})
            if col_op.get('type', 'int') == 'datetime':
                df[col_op['name']] = pd.to_datetime(value)
            elif col_op.get('type', 'int') == 'float':
                df[col_op['name']] = pd.to_numeric(value)
            else:
                self.warning("Unknown type for column operation: "+str(col_op.get('type')))
            for to_del in col_op.get('remove',"").split(','):
                to_del = to_del.strip().upper()
                if to_del != '':
                    if to_del in df:
                        del df[to_del]
                    else:
                        self.warning('Trying to remove unknown column: '+str(to_del))
                
        return df       
#        return {'cols':cols, 'data':resp, 'query':query, 'df':df}

