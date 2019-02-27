from socket import *
import sys, time, threading

def hash_func(num):
    return num%256

class Peer():
    def __init__(self, me, suc1, suc2):
        self.me = me
        self.suc1 = suc1
        self.suc2 = suc2
        self.pred1 = 0
        self.pred2 = 0

    def setsuc1(self,suc1):
        self.suc1 = suc1

    def setsuc2(self,suc2):
        self.suc2 = suc2

    def setpred1(self,pred1):
        self.pred1 = pred1

    def setpred2(self,pred2):
        self.pred2 = pred2

    def getsuc1(self):
        return self.suc1

    def getsuc2(self):
        return self.suc2

    def getpred1(self):
        return self.pred1

    def getpred2(self):
        return self.pred2

    def setUDP(self, UDP):
        self.UDP = UDP

    def setTCP(self, TCP):
        self.TCP = TCP

    def callUDP(self):
        self.UDP.pinging()

    def commandTCP(self, command):
        self.TCP.commanding(command)

    def closeUDP(self):
        self.UDP.Uclose()

class UDP(threading.Thread):
    def __init__(self, entity, Usocket, dest):
        super(UDP, self).__init__()
        self.entity = entity
        self.Usocket = Usocket
        self.dest = dest

    def run(self):
        Usocket = self.Usocket
        dest = self.dest
        me = self.entity
        if dest == 1:
            target = me.suc1
        elif dest == 2:
            target = me.suc2
        message = "Ping " + str(me.me) + " " + str(self.dest)
        Usocket.sendto(message.encode(),('', target+50000))

class UDPThread(threading.Thread):
    def __init__(self, entity):
        super(UDPThread, self).__init__()
        self.entity = entity
        self.ping = False
        self.running = True

    def pinging(self):
        self.ping = True

    def Uclose(self):
        self.running = False
        
    def run(self):
        portName = self.entity.me + 50000
        UDPsocket = socket(AF_INET, SOCK_DGRAM)
        UDPsocket.bind(('', portName))
        UDPsocket.settimeout(1)
        now = time.time()
        wait1, wait2 = False, False
        interval = 5
        max_interval = 20
        suc1_count, suc2_count = 0, 0
        while self.running:
            message = ["NULL"]
            try:
                receive, addr = UDPsocket.recvfrom(1024)
                receive = receive.decode()
                message = receive.split(" ")
            except:
                pass
            if time.time() - now > interval or self.ping:
                self.ping = False
                NewPingThread1 = UDP(self.entity, UDPsocket, 1)
                NewPingThread2 = UDP(self.entity, UDPsocket, 2)
                NewPingThread1.start()
                NewPingThread2.start()
                wait1, wait2 = True, True
                now = time.time()
            if time.time() - now > 1 and wait1: #suc1 dead
                if suc1_count == 3:
                    wait1 = False
                    suc1_count = 0
                    print("Peer " + str(self.entity.suc1) + " is no longer alive.")
                    self.entity.commandTCP("Nsuc1")
                    interval = 5
                else:
                    suc1_count += 1
                    PingThread1 = UDP(self.entity, UDPsocket, 1)
                    PingThread1.start()
                    now = time.time()
            if time.time() - now > 1 and wait2: #suc2 dead
                if suc2_count == 3:
                    wait2 = False
                    suc2_count = 0
                    print("Peer " + str(self.entity.suc2) + " is no longer alive.")
                    self.entity.commandTCP("Nsuc2")
                    interval = 5
                else:
                    suc2_count += 1
                    PingThread2 = UDP(self.entity, UDPsocket, 2)
                    PingThread2.start()
                    now = time.time()
            if message[0] == "Ping":
                print("A ping request message was received from Peer " + str(message[1]) + ".")
                if message[2] == "1" and self.entity.pred1!= addr[1] - 50000:
                    self.entity.setpred1(addr[1] - 50000)
                elif message[2] == "2" and self.entity.pred2 != addr[1] - 50000:
                    self.entity.setpred2(addr[1] - 50000)
                response = "Alive" + " " + message[2]
                UDPsocket.sendto(response.encode(),addr)
            elif message[0] == "Alive":
                if wait1 and message[1] == "1":
                    wait1 = False
                    if interval < max_interval:
                        interval += interval//2.4
                    print("Peer " + str(self.entity.suc1) + " is still alive.")
                if wait2 and message[1] == "2":
                    wait2 = False
                    if interval < 360:
                        interval += interval//2.4
                    print("Peer " + str(self.entity.suc2) + " is still alive.")
        UDPsocket.close()
                
class TCP(threading.Thread):
    def __init__(self, entity, msg, dest, target):
        super(TCP, self).__init__()
        self.entity = entity
        self.dest = dest
        self.msg = msg
        self.target = target

    def run(self):
##        clientPort = self.entity.me + 40000
        Tsocket = socket(AF_INET, SOCK_STREAM)
##        Tsocket.bind(('',clientPort))
        dest = self.dest
        if self.target == -1:
            target = 50000
            if dest == 1:
                target += self.entity.suc1
            elif dest == 2:
                target += self.entity.suc2
            elif dest == -1:
                target += self.entity.pred1
            elif dest == -2:
                target += self.entity.pred2
        else:
            target = self.target + 50000
        Tsocket.connect(('',target))
        Tsocket.send((self.msg).encode())
        Tsocket.close()

class TCPThread(threading.Thread):
    def __init__(self, entity):
        super(TCPThread,self).__init__()
        self.entity = entity
        self.command = "NULL"
        self.file = 0

    def commanding(self, command):
        cmd = command.split(" ")
        self.command = cmd[0]
        if len(cmd) == 2:
            self.request(int(cmd[1]))
        if self.command == "request":
            msg = "request" + " " + str(self.file) + " " + str(self.entity.me) +" "+ str(self.entity.me)
            NewRequestThread = TCP(self.entity,msg,1,-1)
            NewRequestThread.start()
            self.command = "NULL"
        elif self.command == "Nsuc1" or self.command == "Nsuc2":
            if self.command == "Nsuc1":
                self.entity.setsuc1(self.entity.suc2)
            msg = "Need " + str(self.entity.suc1) +" " + str(self.entity.me)
            askThread = TCP(self.entity,msg,1,-1)
            askThread.start()
            self.command = "NULL"
        elif self.command == "quit":
            print("Peer "+str(self.entity.me)+" will depart from the network.")
            msg = "Departure " + str(self.entity.me) + " " + str(self.entity.suc1)+ " " + str(self.entity.suc2)
            noteThread1 = TCP(self.entity,msg,-1,-1)
            noteThread2 = TCP(self.entity,msg,-2,-1)
            noteThread1.start()
            noteThread2.start()
            self.command = "NULL"

    def request(self,file):
        self.file = hash_func(file)
        self.command = "request"
    
    def run(self):
        serverPort = self.entity.me + 50000
        TCPsocket = socket(AF_INET, SOCK_STREAM)
        TCPsocket.bind(('', serverPort))
        TCPsocket.listen(12)
        known1, known2 = False, False
        while True:
            message = ["NULL"]
            connectionSocket, addr = TCPsocket.accept()
            request = connectionSocket.recv(1024)
            connectionSocket.close()
            request = request.decode()
            message = request.split(" ")
            if message[0] == "request":
                if ((int(message[3]) > (self.entity.me)) and (int(message[1]) > int(message[3]))) or ((int(message[1]) <= self.entity.me) and (int(message[1])>int(message[3]))):
                    msg = "Received a response message from peer "+str(self.entity.me)+", which has the file "+message[1]+"."
                    receiveThread = TCP(self.entity,msg,0,int(message[2]))#message[2] contains peer name of who want to this file
                    receiveThread.start()
                    print("File "+ message[1] +" is here.")
                    print("A response message, destined for peer "+message[2]+", has been sent.")
                else:
                    msg = message[0] + " "+ message[1] +" "+ message[2] + " "+str(self.entity.me)
                    passThread = TCP(self.entity,request,1,-1)
                    passThread.start()
                    print("File "+ message[1] +" is not stored here.")
                    print("File request message has been forwarded to my successor.")
            elif message[0] == "Received":
                print(request)
            elif message[0] == "Need":
                self.entity.setpred1(int(message[1]))
                msg = "New " + str(self.entity.suc1)
                responseThread = TCP(self.entity,msg,-1,int(message[2]))
                responseThread.start()
            elif message[0] == "Departure":
                if int(message[1]) == self.entity.suc1:
                    resThread = TCP(self.entity,"1ok",1,self.entity.suc1)
                    resThread.start()
                    self.entity.setsuc1(self.entity.suc2)
                    self.entity.setsuc2(int(message[3]))
                else:
                    resThread = TCP(self.entity,"2ok",2,self.entity.suc2)
                    resThread.start()
                    self.entity.setsuc2(int(message[2]))
                print("My first successor is now peer "+ str(self.entity.suc1) +".")
                print("My second successor is now peer "+ str(self.entity.suc2) +".")
            elif message[0] == "New":
                if message[1] == str(self.entity.suc2):
                    self.commanding("Nsuc2")
                else:
                    self.entity.setsuc2(int(message[1]))
                    self.entity.callUDP()
                    print("My first successor is now peer "+ str(self.entity.suc1) +".")
                    print("My second successor is now peer "+ str(self.entity.suc2) +".")
            elif message[0] == "1ok":
                known1 = True
            elif message[0] == "2ok":
                known2 = True           
            if known1 == True and known2 == True:
                TCPsocket.close()
                self.entity.closeUDP()
                exit()
                       
def main():
    me = int(sys.argv[1])
    suc1 = int(sys.argv[2])
    suc2 = int(sys.argv[3])
    ThisPeer = Peer(me, suc1, suc2)
    UThread = UDPThread(ThisPeer)
    TThread = TCPThread(ThisPeer)
    ThisPeer.setUDP(UThread)
    ThisPeer.setTCP(TThread)
    UThread.start()
    TThread.start()
    while True:
        command = input()
        TThread.commanding(command)

if __name__ == "__main__":
    main()


