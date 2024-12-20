import datetime
import socket

import constants as c

from .log_utils import print_in_log

# TCP_IP = '160.80.83.142'
# TCP_IP = '192.168.0.2'
# TCP_IP = '10.0.0.2'
# TCP_IP = '192.168.214.70'
TCP_IP = 'localhost'          #Per ultraportable
# TCP_PORT = 9001
TCP_PORT = 59001              #Per ultraportable
BUFFER_SIZE = 8192
TIMEOUT = 10  # amount of time in s between one command and the following time


def find_device():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(TIMEOUT)
    try:
        # Connessione al dispositivo
        client_socket.connect((c.spectrum_analyzer_ip, c.spectrum_analyzer_port))
        print_in_log(get_message(client_socket, '*IDN?\n'))
    except Exception as e:
        print_in_log("Can't find any device in IP {}, port {} with error:".format(c.spectrum_analyzer_ip, c.spectrum_analyzer_port) + str(e))
        return -1

    print_in_log("Device found in IP {}, port {}".format(c.spectrum_analyzer_ip, c.spectrum_analyzer_port))
    client_socket.close()
    return 0


def connect_to_device():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(TIMEOUT)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUFFER_SIZE)
    try:
        # Connessione al dispositivo
        client_socket.connect((c.spectrum_analyzer_ip, c.spectrum_analyzer_port))

    except Exception as e:
        print_in_log("Errore durante la comunicazione con il dispositivo:" + str(e))

    return client_socket


def send_command(conn, message, wait=-1):
    if wait != -1:
        conn.settimeout(wait)
    try:
        conn.send(message.encode())

    except Exception as e:
        print_in_log("Errore durante l'invio dei dati:", str(e))

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
        print_in_log("Errore durante la ricezione dei dati:" + str(e))
        recv_message = get_error(conn)  # TODO: da capire bene cosa fare qui

    if isinstance(recv_message, bytes):
        try:
            return recv_message.decode("utf-8")
        except UnicodeDecodeError:
            return str(recv_message)
    if wait != -1:
        conn.settimeout(TIMEOUT)
    return recv_message


def update_error_log(message):
    print_in_log(message)
    error_log_file_name = c.error_log_file
    error_log_file = open(error_log_file_name, 'a')
    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    error_log_file.write(str(format(current_timestamp)) + " " + message)


def get_error(conn):
    while True:
        error = get_message(conn, ':SYSTem:ERRor?\n')
        if error == None: return
        if error[0] != "0":
            err_split = error.split(",")
            update_error_log(error)

            # TODO: Gestione errori Anritsu se necessario

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

def setup_anritsu_device_rack(conn):
    send_command(conn,':MODE SPEC\n')
    send_command(conn,':CONFigure:CHPower\n')
    send_command(conn,':FSTRength:STATe 1\n')
    send_command(conn,':FSTRength:ANTenna "{}"\n'.format(c.antenna_file))
    send_command(conn,':UNIT:POW DBM/M2\n')  # Unit in terms of field strength. IMPORTANT: DOUBLE CHECK THAT THE ANTENNA FILE ON THE SA IS CORRECT!
    send_command(conn,':POW:RF:ATT:AUTO OFF\n')  # Automatic input attenuation coupling
    send_command(conn,':POW:RF:ATT 0 DB\n')  # Set attenuation to 0 dB
    send_command(conn,':POW:RF:GAIN:STAT OFF\n')  # Turn off pre-amplifier for initial setting

def setup_anritsu_device_ultraportable(conn):
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
    import time
    time.sleep(10)


def get_loc_name_by_geo_info(curr_latitude, curr_longitude, curr_timestamp):
    #TODO: Capire con il prof se va fatto qualcosa qui (uso API per trovare nome da info lat-long, oppure nome statico)
    return "Roma Tor Vergata"


def get_gps_info(conn):

    # PARTE GPS, DA VEDERE
    location_name = "_"

    gps_raw = get_message(conn, ':FETCh:GPS?\n')  # Fetching the GPS TODO: Ultraportable non ha GPS! Come fare?
    if gps_raw != None:
        gps_array_split = gps_raw.split(',')

        if gps_array_split[0] == 'GOOD FIX':
            curr_latitude = float(gps_array_split[2])
            curr_longitude = float(gps_array_split[3])
            curr_timestamp = gps_array_split[1]

            location_name = get_loc_name_by_geo_info(curr_latitude, curr_longitude, curr_timestamp)

    return location_name

def general_setup_connection_to_device():
    import time
    for i in range(10):
        ret = find_device()
        time.sleep(60)
        if ret==0:
            break
    if ret==-1:
        exit(0)
    conn = connect_to_device()
    location_name = ""
    if c.device_type == "MS2090A" or c.device_type == "rack":
        location_name = get_gps_info(conn)
        setup_anritsu_device_rack(conn)
    elif c.device_type == "MS2760A" or c.device_type == "ultraportable":
        setup_anritsu_device_ultraportable(conn)

    return conn, location_name