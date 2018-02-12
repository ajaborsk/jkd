from .node import *

class HtmlPage(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    async def msg_handle(self, msg):
        if 'query' in msg and msg['query'] == 'get':
            html_page = '<html><body>HtmlPage default reply.</body></html>'
            self.debug("handling"+str(msg))
            self.debug("Reply to " + str(msg['src']) + "/ qid=" + str(msg['qid']))
            rep= {'qid':msg['qid'], 'reply':html_page}
            self.debug("Reply = " + str(rep))
            self.debug("Queue = " + str(msg['src'].input))
            await msg['src'].input.put(rep)
            self.debug("Replied")
        else:
            await super().msg_handle(msg)

