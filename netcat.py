
import sys
import getopt
import socket
import threading
import thread
import subprocess
import os

def usage():
    print "----------------------------------------------------"
    print "                  *NETC*                            "
    print "----------------------------------------------------"
    print "usage : netc.py -t target -p port"
    print "-l --listen      : to listen for incoming connections"
    print "-s --shell       : to initiate a command shell"
    print "-u --upload path : to upload a file to specific path or destination"
    print "\nExamples:"
    print "netc.py -t 127.0.0.1 -p 8080 -l -s"
    print "netc.py -t 127.0.0.1 -p 8080 -l -u \"c:\\Desktop\\r.txt\""
    print "echo \"something\" |netc.py -t 192.1.1.14 -p 80 "
    sys.exit(0)

#defining some global variables
target=''
port =0
listen=False
shell=False
upload=""

if not len(sys.argv[1:]):
    usage()

try:
    options,arguments=getopt.getopt(sys.argv[1:],'t:p:lsu:',["target=","port=","listen","shell","upload="])
except getopt.GetoptError as err :
    print str(err)
    usage()
for o,a in options:
    if o in ("-t","--target"):
        target =a
    elif o in ("-p","--port"):
        port = int(a)
    elif o in ("-l","--listen"):
        listen= True
    elif o in ("-s","--shell"):
        shell = True
    elif o in ("-u","--upload"):
        upload = a
    else:
        print "Unhandled operation\n"
        usage()


def client():
    global target
    global port
    try:
        host=socket.gethostbyname(target)
    except socket.gaierror:
        print "Error in resolving hostname"
        sys.exit(0)
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    print "Connecting to server................."
    try :
        s.connect((host,port))
    except socket.error as err:    
        print "Error in connecting socket"
        print str(err)
        sys.exit(0)
    s.setblocking(0)
    while True:
        response=""
        try:
            while 1:
                data=s.recv(4096)
                response=response + data
                if len(data) < 4096:
                    break
        except:
            pass         
        sys.stdout.write(response)
        buff=raw_input()
        if len(buff):
            s.send(buff)
        
def server():
    global target
    global port
    global shell
    global upload
    
    if not len(target):
        target=''
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print 'Socket Created '
    print 'Binding Socket '
    try:
        s.bind((target,port))
    except:
        print 'Error in binding socket'
        sys.exit(0)
    s.listen(5)
    print 'Listening for connections .........'
    while True :
        conn,addr=s.accept()
        print 'Connected to ' + str(addr[0]) + 'at port: ' + str(addr[1])
        thread.start_new_thread(client_handler,(conn,))
        #t1.daemon=True
        #t1.start()

def client_handler(conn):
    global shell
    global upload 
    if len(upload) :
        try :
            buff= ''
            while True:
                data=conn.recv(4096)        
                buff=buff+data
                if len(data) < 4096:
                    break
            fd=open(upload,"wb")
            fd.write(buff)
            fd.close()
            print 'Successfully uploaded the file to %s' %(upload)
        except:
            print 'Failed to upload file to specified destination'
    elif shell :
        buff='enter the command or quit to exit\n'
        buff= buff + str(os.getcwd()) + '>'
        conn.send(buff)
        while True :
            command=conn.recv(1024)
            if command[0:4]=='quit' or command[0:1]=='q': 
                break
            #command.rstrip()
            if command[0:2]=='cd' :
                os.chdir(command[3:])
            if len(command) > 0 :
                try:
                    cmd=subprocess.Popen(command[:],shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE)
                    output=str(cmd.stdout.read() + cmd.stderr.read())
                    output= output +str(os.getcwd()) + '>'
                    conn.sendall(output)
                except:
                    print ' Cannot execute command .... Try again '
                    pass
    else :
         utility()
                    

if not listen and len(target) and port > 0:
    #buff= raw_input()
    client()

if listen:
    server()  
