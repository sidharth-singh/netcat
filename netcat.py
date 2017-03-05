import sys
import getopt
import socket
import threading
import subprocess

# Declaring global variables
listen = False
upload = False
command_line = False
target = ""
port = 0
execute = ""
upload_destination = ""

def usage():
    print("NetCat - swiss knife of networking\n")
    print("Usage: netcat.py -t [target-address] -p [target-port]")
    print("-l --listen                  -listen on [host]:[port] for incoming connections")
    print("-c --command                 -initialize a command shell")
    print("-e --execute                 -execute a file upon receiving a connection")
    print("-u --upload=destination      -upload a receiving a connection upload a file and write to [destination]")
    print()

def client_sender(buffer):
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        # connect to our target host
        client.connect((target,port))

        if len(buffer):
            client.send(str.encode(buffer))

        while True:
            recieve_length = 1
            response = ""

            while recieve_length:
                recieved_data = client.recv(4096)
                recieve_length = len(recieved_data)
                response += str(recieved_data, "utf-8")

                if recieve_length < 4096:
                    break

            print(response)

            # waiting for more input
            buffer = input()
            buffer+="\n"

            # send the new input
            client_sender(str.encode(buffer))

    except:
        print("Exception encountered! Exiting now...")
        # close the connection of client socket
        client.close()

def run_command(command):
    # trim the new line
    command = command.rstrip()

    # run the command and get the output
    try:
        output = str(subprocess.check_output(command,stderr=subprocess.STDOUT,shell=True),"utf-8")
    except:
        output = "Failed to execute command. \r\n"

    # send the output to the client

    return output



def client_handler(client_socket):
    # check for upload
    if len(upload_destination):
        # read all the bytes and write to destination
        file_buffer = ""

        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        # now write these bytes to upload destination
        try:
            file_pointer = open(upload_destination,"wb")
            file_pointer.write(file_buffer)
            file_pointer.close()
            msg="Successfully written file to: " + str(upload_destination)
            client_socket.send(str.encode(msg))
        except:
            msg = "Failed to save file: " + str(upload_destination)
            client_socket.send(str.encode(msg))

    # checking for command execution
    if len(execute):
        # run the command
        output = run_command(execute)

        # send the response to client
        client_socket.send(str.encode(output))

    # check whether a command shell was requested
    if command_line:
        while True:
            # show the prompt
            print("<netcat#> ")

            # now recieve the command until linefeed (new line) is found
            command_buffer = ""

            while "\n" not in command_buffer:
                cmd = client_socket.recv(1024)
                command_buffer += str(cmd,"utf-8")

            response = run_command(command_buffer)

            # sending the response back
            client_socket.send(str.encode(response))
            

def server_loop():
    global target

    # if no target is defined then listening on all the interfaces
    if not len(target):
        target = "0.0.0.0"

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # binding to given target on given port
        server_socket.bind((target,port))
        server_socket.listen(5)

        while True:
            conn, addr = server_socket.accept()
            print("Connection established to: " + str(addr[0]) + " : " + str(addr[1]))
            client_thread = threading.Thread( target = client_handler, args=(conn,))
            client_thread.start()


def main():
    global target
    global listen
    global port
    global execute
    global command_line
    global upload_destination

    if not len(sys.argv[1:]):
        usage()

    # get the command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hle:u:ct:p:",["help","listen","execute=","upload=","command","target=","port="])
    except getopt.GetoptError as msg:
        print(str(msg))
        usage()

    for o, a in opts:
        if o in ("-h","--help"):
            usage()
            sys.exit(1)
        elif o in ("-l","--listen"):
            listen = True
        elif o in ("-e","--execute"):
            execute = a
        elif o in ("-u","--upload"):
            upload_destination = a
        elif o in ("-c","--command"):
            command_line = true
        elif o in ("-t","--target"):
            target = a
        elif o in ("-p","--port"):
            port = int(a)
        else:
            assert False,"Unhandled option"

        # if listening
        if listen:
            server_loop()

        # if not listening and just sending the data from standard input
        if not listen and len(target) and port > 0:
            buffer = sys.stdin.read()
            client_sender(buffer)


main()