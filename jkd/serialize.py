
import json

def default(obj):
    return obj

def jkd_serialize(data):
    return json.dumps(data, default = default).encode('utf8')

def jkd_deserialize(bytestring):
    return json.loads(bytestring)

