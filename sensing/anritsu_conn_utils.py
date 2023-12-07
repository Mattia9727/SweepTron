import datetime
import os
import socket

import constants as c

# TCP_IP = '160.80.83.142'
# TCP_IP = '192.168.0.2'
TCP_IP = '192.168.214.70'
TCP_PORT = 9001
BUFFER_SIZE = 8192
TIMEOUT = 1  # amount of time in s between one command and the following time


def find_device():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(TIMEOUT)
    try:
        # Connessione al dispositivo
        client_socket.connect((TCP_IP, TCP_PORT))

    except Exception as e:
        print("Can't find any device in IP {}, port {} with error:".format(TCP_IP, TCP_PORT), str(e))
        exit(0)

    print("Device found in IP {}, port {}".format(TCP_IP, TCP_PORT))
    client_socket.close()


def connect_to_device():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(TIMEOUT)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUFFER_SIZE)
    try:
        # Connessione al dispositivo
        client_socket.connect((TCP_IP, TCP_PORT))

    except Exception as e:
        print("Errore durante la comunicazione con il dispositivo:", str(e))

    return client_socket


def send_command(conn, message, wait=-1):
    if wait != -1:
        conn.settimeout(wait)
    try:
        conn.send(message.encode())

    except Exception as e:
        print("Errore durante l'invio dei dati:", str(e))

    if wait != -1:
        conn.settimeout(TIMEOUT)


def get_message(conn, message, wait=-1):
    if wait != -1:
        conn.settimeout(wait)

    # Invia dati al dispositivo
    try:
        conn.send(message.encode())

        # Ricevi dati dal dispositivo
        recv_message = conn.recv(BUFFER_SIZE)

    except Exception as e:
        print("Errore durante la ricezione dei dati:", str(e))
        recv_message = get_error(conn)  # Todo: da capire bene cosa fare qui

    if wait != -1:
        conn.settimeout(TIMEOUT)

    if type(recv_message) == str:
        return recv_message
    return recv_message.decode()


def update_error_log(message):
    errorLogFileName = os.path.join(c.logs_dir, c.error_log_file)
    errorLogFile = open(errorLogFileName, 'a')
    currentTimestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    errorLogFile.write(str(format(currentTimestamp)) + " " + message + "\n")
    return


def get_error(conn):
    while True:
        error = get_message(conn, ':SYSTem:ERRor?\n')
        if error[0] != "0":
            err_split = error.split(",")
            print(err_split)
            update_error_log(error)

            # TODO: Gestione errori Anritsu

            if any(err_split[0] == i for i in range(-100, -200)):  # Command error (invalid character, syntax error, ...)
                pass
            elif any(err_split[0] == i for i in range(-200, -300)):  # Execution error (data out of range, Illegal parameter value, ...)
                pass
            elif any(err_split[0] == i for i in range(-300, -400)):  # Device-specific error (Calibration Failed, Queue overflow, Input buffer overrun)
                pass
            elif err_split[0] == -400:  # Query error
                pass
        else:
            break


