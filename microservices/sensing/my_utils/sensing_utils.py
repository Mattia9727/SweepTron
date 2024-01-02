import datetime
import os
import time

import numpy as np
from matplotlib import pyplot as plt

from . import constants as c
from .anritsu_conn_utils import connect_to_device, get_message, send_command, get_error, \
    setup_for_single_freq


def plot_measure(measured_emf_matrix_base_station,f):
    t = datetime.datetime.now()
    y, M, d, h, m, s = t.year, t.month, t.day, t.hour, t.minute, round(t.second)
    plt.plot(measured_emf_matrix_base_station[f, :], "b-", linewidth=2)
    plt.xlabel("Sample Number [unit]", fontsize=14)
    plt.ylabel("Channel Power [V/m]", fontsize=14)
    plt.title("Frequency {} MHz Timestamp: {}/{}/{}, {}:{}:{}".format(c.frequency_center[f], y, M, d, h, m, s),
              fontsize=16)

    # Save the figure with a unique file name based on date and time
    if not os.path.exists(c.grafici_dir):
        # Create a new directory because it does not exist
        os.makedirs(c.grafici_dir)

    plot_file = 'freq_{}.jpg'.format(c.frequency_center[f])
    plt.savefig(os.path.join(c.grafici_dir, plot_file))
    plt.clf()

def iq_capture():
    # Crea un socket
    conn = connect_to_device()
    print(get_message(conn, '*IDN?\n'))
    send_command(conn, ':IQ:SAMPle SB2\n')
    print(get_error(conn))
    send_command(conn, ':IQ:BITS I16\n')
    print(get_error(conn))
    send_command(conn, ':IQ:MODE SINGLE\n')
    print(get_error(conn))
    send_command(conn, ':SENS:IQ:TIME 1\n')
    print(get_error(conn))
    send_command(conn, ':IQ:LENGTH 5 ms\n')
    print(get_error(conn))
    send_command(conn, ':MEAS:IQ:CAPT\n')
    print(get_error(conn))
    print(get_message(conn,
                      ':STATus:OPERation?\n'))  # TODO: :MMEMory:STORe:CAPTure, :MMEMory:DATA <string>,<string>,<block data>
    conn.close()


def measure(conn, location_name):
    measured_emf_matrix_base_station = np.zeros((c.num_frequencies, c.number_samples_chp))
    time_array = np.empty((c.num_frequencies, c.number_samples_chp), dtype=object)

    if not os.path.exists(c.logs_dir):
        # Create a new directory
        os.makedirs(c.logs_dir)

    # Create and open a TXT file to record data
    log_file = open(os.path.join(c.logs_dir, c.log_file + '.txt'), 'a')

    # Create and open a CSV file to record data
    csv_file = open(os.path.join(c.logs_dir, c.log_file + '.csv'), 'a')

    curr_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    log_file.write('Timestamp di esecuzione: {}\n'.format(curr_timestamp))

    for f in range(c.num_frequencies):

        curr_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        print("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))

        c.transmission_freq_used = False
        if c.frequency_center[f] in c.transmission_freq:  # Controllo di frequenza di invio
            c.transmission_freq_used = True

        if c.iq_mode == 1:
            if c.transmission_freq_used == True and c.isTransfering == True:
                print("Invio dati in IQ_MODE nella frequenza attuale. Passo alla frequenza successiva.")
                continue

        setup_for_single_freq(conn, f)

        for index_samples in range(c.number_samples_chp):
            emf_measured_chp = get_message(conn, ':FETCH:CHP:CHP?\n')  # Fetch current value of channel power
            measured_emf_matrix_base_station[f, index_samples] = float(emf_measured_chp)
            time_array[f, index_samples] = datetime.datetime.now()

            if c.print_debug > 0:
                log_file.write('Timestamp: {} - Frequency: {} - Channel power: {}\n'.format(
                    datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                    measured_emf_matrix_base_station[f, index_samples]))
            else:
                log_file.write('{} {} {}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                                                   measured_emf_matrix_base_station[f, index_samples]))

            csv_file.write('{},{},{}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                                               measured_emf_matrix_base_station[f, index_samples]))
            time.sleep(c.inter_sample_time)

        plot_measure(measured_emf_matrix_base_station, f)

        location_name_mat = '{}.mat'.format(location_name)
        np.save(location_name_mat, measured_emf_matrix_base_station)
        c.transmission_freq_used = False

    # Close the log files
    log_file.close()
    csv_file.close()
    # Add code to stop the loop or exit gracefully if needed


def get_loc_name_by_geo_info(curr_latitude, curr_longitude, curr_timestamp):
    #TODO: Capire con il prof se va fatto qualcosa qui (uso API per trovare nome da info lat-long, oppure nome statico)
    return "Roma Tor Vergata"


def get_gps_info(conn):

    # PARTE GPS, DA VEDERE
    location_name = "Roma Tor Vergata"

    gps_raw = get_message(conn, ':FETCh:GPS?\n')  # Fetching the GPS
    gps_array_split = gps_raw.split(',')

    curr_latitude = 0
    curr_longitude = 0
    curr_timestamp = 0

    if gps_array_split[0] == 'GOOD FIX':
        curr_latitude = float(gps_array_split[2])
        curr_longitude = float(gps_array_split[3])
        curr_timestamp = gps_array_split[1]

        location_name = get_loc_name_by_geo_info(curr_latitude, curr_longitude, curr_timestamp)

    return location_name