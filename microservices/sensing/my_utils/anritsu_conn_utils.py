import datetime
import os
import socket

from . import constants as c

# TCP_IP = '160.80.83.142'
# TCP_IP = '192.168.0.2'
# TCP_IP = '192.168.214.70'
TCP_IP = 'localhost'
# TCP_PORT = 9001
TCP_PORT = 59001
BUFFER_SIZE = 8192
TIMEOUT = 3  # amount of time in s between one command and the following time


def find_device():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(TIMEOUT)
    try:
        # Connessione al dispositivo
        client_socket.connect((TCP_IP, TCP_PORT))
        print(get_message(client_socket, '*IDN?\n'))
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
    if isinstance(recv_message, bytes):
        return recv_message.decode()
    return recv_message


def update_error_log(message):
    error_log_file_name = os.path.join(c.error_log_file)
    error_log_file = open(error_log_file_name, 'a')
    current_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    error_log_file.write(str(format(current_timestamp)) + " " + message + "\n")


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

def setup_anritsu_device_MS2090A(conn):
    send_command(conn,':MODE SPEC\n')
    send_command(conn,':CONFigure:CHPower\n')
    send_command(conn,':FSTRength:STATe 1\n')
    send_command(conn,':FSTRength:ANTenna "{}"\n'.format(c.antenna_file))
    send_command(conn,':UNIT:POW V/M\n')  # Unit in terms of field strength (volt meter). IMPORTANT: DOUBLE CHECK THAT THE ANTENNA FILE ON THE SA IS CORRECT!
    send_command(conn,':POW:RF:ATT:AUTO OFF\n')  # Automatic input attenuation coupling
    send_command(conn,':POW:RF:ATT 0 DB\n')  # Set attenuation to 0 dB
    send_command(conn,':POW:RF:GAIN:STAT OFF\n')  # Turn off pre-amplifier for initial setting

def setup_anritsu_device_MS2760A(conn):
    send_command(conn,':CONFigure:CHPower\n')

def setup_for_single_freq(conn,f):
    selected_frequency_start = c.frequency_start[f]
    selected_frequency_stop = c.frequency_stop[f]

    frequenc_range_str = ':SENS:FREQ:STAR {} MHZ;:SENS:FREQ:STOP {} MHZ\n'.format(selected_frequency_start,
                                                                                  selected_frequency_stop)
    send_command(conn, frequenc_range_str)  # Frequency range
    send_command(conn, ':ABOR\n')  # Restart the trigger system
    initial_reference_level_str = ':DISP:WIND:TRAC:Y:SCAL:RLEV {}\n'.format(c.initial_reference_level)
    send_command(conn, initial_reference_level_str)  # Automatic reference level above 10 dB
    rbw_str = ':BAND:RES:AUTO ON\n'  # Resolution BW
    send_command(conn, rbw_str)
    send_command(conn, ':CONF:CHP\n')  # Configuring channel power (RMS + integration BW equal to SPAN)
    send_command(conn, ':INIT:CONT ON\n')  # Continuous sweeping
    send_command(conn, ':TRAC:DET RMS\n')  # RMS DETECTOR
    samples_for_averages_str = ':SENS:AVER:COUN {}\n'.format(c.samples_for_averages)
    send_command(conn, samples_for_averages_str)  # Rolling average number of samples
    send_command(conn, ':TRAC:TYPE RAV\n', c.command_rolling_average_time)  # Rolling average DETECTOR
