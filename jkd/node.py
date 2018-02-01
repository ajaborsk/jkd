import xml.etree.ElementTree as ET

class Node:
    def __init__(self, env = None):
        #print("setting env to", env)
        self.env = env

    def get_etnode(self):
        return ET.Element()

    async def aget(self):
        """Return a ElementTree that represent the Node full state (if possible)
        """
        warn("")

    def serialize(self):
        """
        """
        pass

