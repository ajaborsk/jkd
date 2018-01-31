import logging

from .environment import *

class Data:
    pass

class DatabaseManager(Node):
    pass

class DataTable(Data):
    pass

class DataBase(Data):
    pass

class Cache(Node):
    pass

class Processor(Node):
    def __init__(self):
        pass
    async def process(self):
        pass
    async def get_results(self):
        pass

# HTML report


def serve():
    print("serving...")
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/{name}', handle)
    web.run_app(app)
