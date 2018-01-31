import jkd

a = jkd.Data()

print("jkd launched", a)
#jkd.serve()

environment = jkd.Environment()
environment.http_serve()


