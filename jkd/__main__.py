import sys

import jkd

a = jkd.Data()

#print("jkd launched", a)
#print(sys.argv)
#jkd.serve()

if len(sys.argv) == 1:
    environment = jkd.Environment()
    environment.http_serve()
else:
    print("Slave : Done !!")


