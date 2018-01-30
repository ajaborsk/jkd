
class Node:
    pass

class Data(Node):
    pass


class Database(Data):
    pass


class DataTable(Data):
    pass


class DataProcessor(Node):
    def __init__(self):
        pass
    async def process(self):
        pass
    async def get_results(self):
        pass



class HtmlReport(Node):
    async def get(self):
        return "<html><head></head><body><p>Full one !</p></body></html>"

# The Web server part (to be put in a separate module)

application = HtmlReport()

from aiohttp import web

async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    
    text = await application.get()
    
    #text = "Hello, " + name
    return web.Response(body=text)

def serve():
    print("serving...")
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/{name}', handle)
    web.run_app(app)
