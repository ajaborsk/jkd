
class Data:
    pass


class Database(Data):
    pass


class DataTable(Data):
    pass


class DataProcessor:
    def __init__(self):
        pass
    def process(self):
        pass
    def get_results(self):
        pass

# The Web server part (to be put in a separate module)

from aiohttp import web

async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

def serve():
    print("serving...")
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/{name}', handle)
    web.run_app(app)
