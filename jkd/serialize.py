
import json

def jkd_serialize(data):
    return json.dumps(data).encode('utf8')

def jkd_deserialize(bytestring):
    return json.loads(bytestring)

