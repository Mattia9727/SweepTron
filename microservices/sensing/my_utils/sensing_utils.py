import datetime
import os
import time
from math import sqrt

import numpy as np
from matplotlib import pyplot as plt

from . import constants as c
from .anritsu_conn_utils import connect_to_device, get_message, send_command, get_error, \
    setup_for_single_freq

import time

def interp_af(freqs):

    # Carica i dati dal file di testo
    af_keysight = np.loadtxt(c.af_keysight)

    # Estrai le frequenze in kHz dalla prima colonna
    freq_mhz = af_keysight[:, 0] * 1000

    # Trova il valore minimo e massimo delle frequenze
    min_freq = np.min(freq_mhz)
    max_freq = np.max(freq_mhz)

    # Crea un vettore di frequenze interpolate
    step = 0.5  # Passo dell'interpolazione
    freq_interp = np.arange(min_freq, max_freq + step, step)

    # Esegui l'interpolazione lineare
    af_interp = np.interp(freq_interp, freq_mhz, af_keysight[:, 1])

    # Inizializza un array per le ampiezze selezionate
    af_sel_frequencies = np.zeros(len(freqs))

    # Seleziona le ampiezze corrispondenti alle frequenze numeriche
    for i, freq in enumerate(freqs):
        index = np.where(freq_interp == freq)[0]
        if len(index) > 0:
            af_sel_frequencies[i] = af_interp[index[0]]

    # af_sel_frequencies contiene le ampiezze selezionate
    return af_sel_frequencies


def calculate_vm_from_dbm(dbm,af):
    return (1/sqrt(20))*10**((float(dbm)+float(af))/20)

def adjust_ref_level_scale_div(conn, curr_margin, time_search_max, y_ticks):
    max_marker = -200
    min_marker = 200
    for i in range(time_search_max):
        time.sleep(1)
        send_command(conn,':CALC:MARKer1:MAXimum\n')  # put marker on maximum
        output_string = get_message(conn,':CALC:MARKer1:Y?\n')  # query marker
        curr_max_marker = float(output_string)

        if curr_max_marker > max_marker:
            max_marker = curr_max_marker

    for i in range(time_search_max):
        time.sleep(1)
        send_command(conn,':CALC:MARKer1:MINimum\n')  # put marker on minimum #TODO: NON ESISTE! DEVO VEDERE COME FARE
        output_string = get_message(conn,':CALC:MARKer1:Y?\n')  # query marker
        curr_min_marker = float(output_string)

        if curr_min_marker < min_marker:
            min_marker = curr_min_marker

    reference_level = int(max_marker) + curr_margin

    str_level = ':DISP:WIND:TRAC:Y:SCAL:RLEV {}\n'.format(reference_level)
    send_command(conn,str_level)  # setting reference level
    time.sleep(1)

    scale_div = abs(reference_level - min_marker) / y_ticks
    str_scale_div = ':DISP:WIND:TRAC:Y:PDIVISION {}\n'.format(scale_div)
    send_command(conn,str_scale_div)  # automatic scale div setting

    return reference_level, scale_div


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
    print(get_message(conn,':STATus:OPERation?\n'))
    conn.close()


def measureMS2090A(conn, location_name):
    measured_emf_matrix_base_station = np.zeros((c.num_frequencies, c.number_samples_chp))
    time_array = np.empty((c.num_frequencies, c.number_samples_chp), dtype=object)

    if not os.path.exists(c.logs_dir):
        # Create a new directory
        os.makedirs(c.logs_dir)

    # Create and open a TXT file to record data
    log_file = open(c.log_file, 'a')

    # # Create and open a CSV file to record data
    # csv_file = open(os.path.join(c.log_file + '.csv'), 'a')

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

        for i in range(c.number_samples_chp):
            emf_measured_chp = get_message(conn, ':FETCH:CHP:CHP?\n')  # Fetch current value of channel power
            measured_emf_matrix_base_station[f, i] = float(emf_measured_chp)
            time_array[f, i] = datetime.datetime.now()

            if c.print_debug > 0:
                log_file.write('Timestamp: {} - Frequency: {} - Channel power: {}\n'.format(
                    datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                    measured_emf_matrix_base_station[f, i]))
            else:
                log_file.write('{} {} {}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                                                   measured_emf_matrix_base_station[f, i]))

            # csv_file.write('{},{},{}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
            #                                    measured_emf_matrix_base_station[f, i]))
            time.sleep(c.inter_sample_time)

        plot_measure(measured_emf_matrix_base_station, f)

        location_name_mat = '{}.mat'.format(location_name)
        np.save(location_name_mat, measured_emf_matrix_base_station)
        c.transmission_freq_used = False

    # Close the log files
    log_file.close()
    # csv_file.close()
    # Add code to stop the loop or exit gracefully if needed

def measureMS2760A(conn, location_name):
    measured_emf_matrix_base_station = np.zeros((c.num_frequencies, c.number_samples_chp))
    time_array = np.empty((c.num_frequencies, c.number_samples_chp), dtype=object)

    if not os.path.exists(c.logs_dir):
        # Create a new directory
        os.makedirs(c.logs_dir)

    # Create and open a TXT file to record data
    log_file = open(c.log_file, 'a')

    # # Create and open a CSV file to record data
    # csv_file = open(os.path.join(c.log_file + '.csv'), 'a')

    curr_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    if c.print_debug > 0:
        log_file.write('Timestamp di esecuzione: {}\n'.format(curr_timestamp))

    for f in range(c.num_frequencies):

        adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], 3, c.y_ticks)
        adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], 3, c.y_ticks)
        adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], 3, c.y_ticks)

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

        for i in range(c.number_samples_chp):
            emf_measured_chp = get_message(conn, ':FETCH:CHP:CHP?\n')  # Fetch current value of channel power
            if emf_measured_chp == "" :
                print("Problema valore nullo")
                continue
            emf_measured_vm = calculate_vm_from_dbm(emf_measured_chp.split("\n",1)[0],c.antenna_factor[f])
            measured_emf_matrix_base_station[f, i] = float(emf_measured_vm)
            time_array[f, i] = datetime.datetime.now()
            if (len(emf_measured_chp.split("\n"))>2):
                print("C'è un problema con il valore restituito nella misurazione")

            if c.print_debug > 0:
                print('{} - {} - {}'.format(
                            datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), c.frequency_center[f],
                            measured_emf_matrix_base_station[f, i]))

            # if c.print_debug > 0:
            #     log_file.write('Timestamp: {} - Frequency: {} - Channel power: {}\n'.format(
            #         datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), c.frequency_center[f],
            #         measured_emf_matrix_base_station[f, i]))
            # else:
            log_file.write('{} {} {}\n'.format(datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S'), c.frequency_center[f],
                                               measured_emf_matrix_base_station[f, i]))

            # csv_file.write('{},{},{}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
            #                                    measured_emf_matrix_base_station[f, i]))
            time.sleep(c.inter_sample_time)

        plot_measure(measured_emf_matrix_base_station, f)

        location_name_mat = '{}.mat'.format(location_name)
        np.save(location_name_mat, measured_emf_matrix_base_station)
        c.transmission_freq_used = False

    # Close the log files
    log_file.close()
    # csv_file.close()
    # Add code to stop the loop or exit gracefully if needed

def get_loc_name_by_geo_info(curr_latitude, curr_longitude, curr_timestamp):
    #TODO: Capire con il prof se va fatto qualcosa qui (uso API per trovare nome da info lat-long, oppure nome statico)
    return "Roma Tor Vergata"


def get_gps_info(conn):

    # PARTE GPS, DA VEDERE
    location_name = "Roma Tor Vergata"

    gps_raw = get_message(conn, ':FETCh:GPS?\n')  # Fetching the GPS TODO: Ultraportable non ha GPS! Come fare?
    if gps_raw != None:
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