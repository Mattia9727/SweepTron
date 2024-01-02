import os
from threading import Thread

import numpy as np
import time
import datetime

from matplotlib import pyplot as plt

from anritsu_conn_utils import connect_to_device, get_message, send_command, get_error, find_device, measuring

import constants as c
#from server_conn_utils import send_files_to_server


def iq_capture():
    # Crea un socket
    conn = connect_to_device()
    print(get_message(conn, '*IDN?\n'))
    send_command(conn,':IQ:SAMPle SB2\n')
    print(get_error(conn))
    send_command(conn,':IQ:BITS I16\n')
    print(get_error(conn))
    send_command(conn,':IQ:MODE SINGLE\n')
    print(get_error(conn))
    send_command(conn,':SENS:IQ:TIME 1\n')
    print(get_error(conn))
    send_command(conn,':IQ:LENGTH 5 ms\n')
    print(get_error(conn))
    send_command(conn,':MEAS:IQ:CAPT\n')
    print(get_error(conn))
    print(get_message(conn,':STATus:OPERation?\n'))
    conn.close()


if __name__ == '__main__':
    #t = Thread(target=send_files_to_server)
    #t.start()

    find_device()
    measuring()
    #iq_capture()

