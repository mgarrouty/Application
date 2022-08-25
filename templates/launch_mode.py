var="dev"

def urls(var) :
    if var == "dep" :
        return "http://host.docker.internal:8086"
    elif var == "dev" :
        return "http://localhost:8086"
def hosts(var) :
    if var == "dev" :
        return "127.0.0.1"
    elif var == "dep" :
        return "0.0.0.0"

url=urls(var)
host=hosts(var)