import datetime
import os
from math import sqrt

import numpy as np
import servicemanager
from matplotlib import pyplot as plt

from data import constants as c
from .anritsu_conn_utils import connect_to_device, get_message, send_command, get_error, \
    setup_for_single_freq, general_setup_connection_to_device

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

    for i in range(time_search_max):
        time.sleep(1)
        send_command(conn,':CALC:MARKer1:MAXimum\n')  # put marker on maximum
        output_string = get_message(conn,':CALC:MARKer1:Y?\n')  # query marker
        curr_max_marker = float(output_string)

        if curr_max_marker > max_marker:
            max_marker = curr_max_marker

    min_marker = -80   # TODO: capire come trovarlo dinamicamente  (val = valoredinamico - 20 (Db))

    reference_level = int(max_marker) + curr_margin


    str_level = ':DISP:WIND:TRAC:Y:SCAL:RLEV {}\n'.format(reference_level)
    send_command(conn,str_level)  # setting reference level

    scale_div = abs(reference_level - min_marker) / y_ticks
    if c.print_debug == 1:
        print(str(scale_div))
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

def iq_measureMS2090A(conn, location_name):
    print(get_message(conn, "*IDN?"))
    # Set Frequency
    for f in range(c.iq_num_frequencies):
        send_command(conn, ":SENS:FREQ:START {} MHz;",c.iq_frequency_start[f])
        send_command(conn, ":SENS:FREQ:STOP {} MHz;",c.iq_frequency_stop[f])
        bandwidth = c.iq_frequency_stop[f] - c.iq_frequency_start[f]

        print(get_message(conn, ":SYST:ERR?"))

        # Set sweep mode
        send_command(conn, "SWEEP:MODE FFT;")

        # Set RBW
        send_command(conn, ":SENS:BWID:RES {} MHz;", bandwidth)

        # Set Reference Level to -30 dBm
        send_command(conn, ":DISP:WIND:TRAC:Y:SCAL:RLEV -70;")

        # Set to single sweep
        send_command(conn, ":INIT:CONT ON;")

        # Set number of display points to calculate frequency array
        # write("DISP:POIN 601;")

        # Get number of display points to calculate frequency array
        # print(spa.query(":DISP:POIN?;"))

        send_command(conn, ":SENS:AVER:TYPE NORM")

        # Prepare per IQ Capture
        send_command(conn, "IQ:SAMP SB19")
        send_command(conn, ":IQ:LENG 1 s")
        send_command(conn, ":IQ:BITS 16")
        send_command(conn, ":IQ:MODE SING")
        send_command(conn, ":IQ:TIME OFF")
        # send_command(conn, (":TRACe:IQ:DATA:FORM PACK")
        send_command(conn, ":TRACe:IQ:DATA:FORM ASC")
        send_command(conn, ":INIT:CONT ON;")
        print("Start Capture....\n")
        send_command(conn, "MEAS:IQ:CAPT")
        data = get_message(conn, ":STAT:OPER?")
        print("Sweep Status:  " + data)

        dati = get_message(conn, "TRAC:IQ:DATA?")
        print(dati)
        log_file = open(c.log_iq_file, 'a')
        log_file.write('{} {} {}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                                           dati))


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
        servicemanager.LogInfoMsg("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))

        c.transmission_freq_used = False
        if c.frequency_center[f] in c.transmission_freq:  # Controllo di frequenza di invio
            c.transmission_freq_used = True

        if c.iq_mode == 1:
            if c.transmission_freq_used == True and c.isTransfering == True:
                print("Invio dati in IQ_MODE nella frequenza attuale. Passo alla frequenza successiva.")
                continue

        setup_for_single_freq(conn, f)

        for i in range(c.time_search_for_adjust_ref_level_scale):
            adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], c.time_search_for_adjust_ref_level_scale, c.y_ticks)

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


    # # Create and open a CSV file to record data
    # csv_file = open(os.path.join(c.log_file + '.csv'), 'a')

    curr_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    if c.print_debug > 0:
        log_file = open(c.log_file, 'a')
        log_file.write('Timestamp di esecuzione: {}\n'.format(curr_timestamp))
        log_file.close()

    for f in range(c.num_frequencies):
        log_file = open(c.log_file, 'a')

        curr_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        print("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))

        c.transmission_freq_used = False
        if c.frequency_center[f] in c.transmission_freq:  # Controllo di frequenza di invio
            c.transmission_freq_used = True

        if c.iq_mode == 1 and c.transmission_freq_used == True and c.isTransfering == True:
            print("Invio dati in IQ_MODE nella frequenza attuale. Passo alla frequenza successiva.")
            continue

        setup_for_single_freq(conn, f)

        for i in range(c.time_search_for_adjust_ref_level_scale):
            adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], c.time_search_for_adjust_ref_level_scale, c.y_ticks)


        for i in range(c.number_samples_chp):

            emf_measured_chp = get_message(conn, ':FETCH:CHP:CHP?\n')  # Fetch current value of channel power
            if emf_measured_chp == "" or len(emf_measured_chp.split("\n"))>2:
                print("Problema valore CHP, reset connessione e riprovo misurazione...")
                conn.close()
                conn, _ = general_setup_connection_to_device()
                i-=1
                continue
            emf_measured_vm = calculate_vm_from_dbm(emf_measured_chp.split("\n",1)[0],c.antenna_factor[f])
            measured_emf_matrix_base_station[f, i] = float(emf_measured_vm)
            time_array[f, i] = datetime.datetime.now()

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
        log_file.close()

    # Close the log files

    # csv_file.close()
    # Add code to stop the loop or exit gracefully if needed

