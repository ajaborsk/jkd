import sys

import jkd

a = jkd.Data()

#print("jkd launched", a)
#print(sys.argv)
#jkd.serve()

if len(sys.argv) <= 1:
    environment = jkd.Environment()
    environment.http_serve()
elif sys.argv[1] == 'http':
    environment = jkd.Environment()
    environment.http_serve()
elif sys.argv[1] == 'slave':
    if len(sys.argv) == 3:
        app_name = sys.argv[2]
        #TODO
        print("(sub)application result : blabla...")
    else:
        print("Slave : No (sub)application name provided")
else:
    print("Unknown command")


