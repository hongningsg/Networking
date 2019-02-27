from socket import *
import re, sys
def main(argv):
    serverPort = int(argv[0])
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen(1)
    print("Server ready to receive GET request!")
    while True:
        connectionSocket, addr = serverSocket.accept()
        request = connectionSocket.recv(1024)
        print("Connection from ", addr)
        print(request)
        #create http response here
        GetCheck = re.match('GET \/(index.html)? HTTP\/1',request)
        pngneed = re.match('GET \/yoda.png HTTP\/1',request)
        icon = re.match('GET \/favicon.ico HTTP\/1',request)
        if GetCheck:
            httpResponse = "HTTP/1.1 200 OK\n\n"
            f=open("index.html", 'r')
            httpResponse += f.read()
            f.close()
        elif pngneed:
            httpResponse = "HTTP/1.1 200 OK\n\n"
            f=open('yoda.png','r')
            httpResponse += f.read()
            f.close()
        elif icon:
            pass
        else:
            print("404 Not Found!")
            httpResponse = "HTTP/1.1 404 Not Found\n\
Content-Type: text/html\n\n\
<html><head><title>404 Not Found</title></head><body>\
            <h1>404 Not Found</h1></body></html>"
        connectionSocket.send(httpResponse)
        connectionSocket.close()


if __name__ == "__main__":
    main(sys.argv[1:])
