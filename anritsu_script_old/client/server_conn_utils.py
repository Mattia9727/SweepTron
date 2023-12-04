import os
import socket
import time
import constants as c

TCP_IP = socket.gethostbyname(socket.gethostname())
TCP_PORT = 4455
FORMAT = "utf-8"
BUFFER_SIZE = 10240
TIMEOUT = 1  # amount of time in s between one command and the following time

def create_content_and_clear_log(filename):
    # Voglio inviare le prime n righe ogni volta in modo da fare stream processing, rimuovendole poi in locale
    dim = 0
    with open(filename, 'r') as fp:
        # read and store all lines into list
        lines = fp.readlines()
        i = -1
        while dim < BUFFER_SIZE and i < len(lines) - 1:   #TODO: Risolvere problema ultima iterazione
            i += 1
            dim += len(lines[i])
            #print("DIM=" + str(dim))

    content_text = ""
    for j in range(i):
        content_text = content_text + lines[j]

    with open(filename, 'w') as fp:
        # iterate each line
        for number, line in enumerate(lines):
            # delete line 5 and 8. or pass any Nth line you want to remove
            # note list index starts from 0
            if number not in range(i):
                fp.write(line)

    return content_text

def send_file(filename):
    content_text = "start"
    while content_text != "":
        try:
            content_text = create_content_and_clear_log(filename)
        except FileNotFoundError:
            return

        if c.iq_mode == 0:
            while c.transmission_freq_used:
                print("Misurando alla frequenza di trasmissione, non in IQ_mode. In attesa che la misurazione termini...")
                time.sleep(30)

        if content_text != "":

            """ Staring a TCP socket. """
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            """ Connecting to the server. """
            conn.connect((TCP_IP, TCP_PORT))

            """ Sending the filename to the server. """
            conn.send(filename.encode(FORMAT))
            msg = conn.recv(BUFFER_SIZE).decode(FORMAT)
            print(f"[SERVER]: {msg}")
            time.sleep(0.5)

            """ Sending the file data to the server. """
            conn.send(content_text.encode(FORMAT))
            msg = conn.recv(BUFFER_SIZE).decode(FORMAT)
            print(f"[SERVER]: {msg}")
            time.sleep(0.5)

            """ Closing the connection from the server. """
            conn.close()
    return

def send_files_to_server():
    while True:
        c.sending = True
        #send_file(os.path.join(c.logs_dir,c.log_file+".txt"))
        send_file(os.path.join(c.logs_dir,c.log_file+".csv"))
        send_file(os.path.join(c.logs_dir,c.error_log_file))
        c.sending = False
        time.sleep(10)




