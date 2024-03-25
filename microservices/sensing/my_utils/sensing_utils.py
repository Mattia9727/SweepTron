import datetime
import os

from math import sqrt

import numpy as np
from matplotlib import pyplot as plt

import constants as c

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

def adjust_ref_level_scale_div(conn, curr_margin, time_search_max, y_ticks, min_marker,freq_start):
    max_marker = -200
    calc_min_marker = 200

    for i in range(time_search_max):
        time.sleep(1)
        send_command(conn,':CALC:MARKer1:MAXimum\n')  # put marker on maximum
        output_string = get_message(conn,':CALC:MARKer1:Y?\n')  # query marker
        curr_max_marker = float(output_string)


        send_command(conn,':CALC:MARKer2:X {} MHZ\n'.format(freq_start))  # put marker on start (high probability that it's minimum)
        output_string = get_message(conn,':CALC:MARKer2:Y?\n')  # query marker
        curr_min_marker = float(output_string)

        if curr_max_marker > max_marker:
            max_marker = curr_max_marker

        if curr_min_marker < calc_min_marker:
            calc_min_marker = curr_min_marker

    #min_marker = -85   # TODO: capire come trovarlo dinamicamente  (val = valoredinamico - 20 (Db))

    reference_level = int(max_marker) + curr_margin

    calc_min_marker = int(calc_min_marker) - curr_margin

    #print("Actual min margin {} Should be like {}".format(calc_min_marker, min_marker))

    str_level = ':DISP:WIND:TRAC:Y:SCAL:RLEV {}\n'.format(reference_level)
    send_command(conn,str_level)  # setting reference level

    #scale_div = abs(reference_level - min_marker) / y_ticks
    scale_div = abs(reference_level - calc_min_marker) / y_ticks
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

def iq_measureMS2090A(ch, conn, location_name):
    #print(get_message(conn, "*IDN?\n"))
    # Set Frequency
    wait_secs = 20
    for f in range(c.iq_num_frequencies):
        ch.pingToWatchdog()
        print("inizio cattura iq per freq "+str(c.iq_frequency_center[f]))
        send_command(conn, ":SENS:FREQ:START {} MHz;\n".format(c.iq_frequency_start[f]),wait_secs)
        send_command(conn, ":SENS:FREQ:STOP {} MHz;\n".format(c.iq_frequency_stop[f]),wait_secs)
        bandwidth = c.iq_frequency_stop[f] - c.iq_frequency_start[f]

        #print(get_message(conn, ":SYST:ERR?\n"))

        # Set sweep mode
        send_command(conn, "SWEEP:MODE FFT;\n",wait_secs)

        # Set RBW
        send_command(conn, ":SENS:BWID:RES {} MHz;\n".format(bandwidth),wait_secs)

        # Set Reference Level to -30 dBm
        send_command(conn, ":DISP:WIND:TRAC:Y:SCAL:RLEV -70;\n",wait_secs)

        # Set to single sweep
        send_command(conn, ":INIT:CONT ON;\n",wait_secs)

        # Set number of display points to calculate frequency array
        # write("DISP:POIN 601;")

        # Get number of display points to calculate frequency array
        # print(spa.query(":DISP:POIN?;"))

        send_command(conn, ":SENS:AVER:TYPE NORM\n",wait_secs)

        sb = ""
        #if (bandwidth == 10): sb = "SB12"
        #elif (bandwidth == 20): sb = "SB9"
        #elif (bandwidth == 40): sb = "SB6"
        #elif (bandwidth == 80): sb = "SB3"
        #else: sb = "SB19"
        sb = "SB19"
        # Prepare per IQ Capture
        send_command(conn, "IQ:SAMP {}\n".format(sb),wait_secs)
        send_command(conn, ":IQ:LENG {} {}\n".format(c.iq_length_value, c.iq_length_unit),wait_secs)
        send_command(conn, ":IQ:BITS {}\n".format("c.iq_bits"),wait_secs)
        send_command(conn, ":IQ:MODE SING\n",wait_secs)
        send_command(conn, ":IQ:TIME OFF\n",wait_secs)
        send_command(conn, ":TRACe:IQ:DATA:FORM PACK",wait_secs)
        # send_command(conn, ":TRACe:IQ:DATA:FORM ASC\n",wait_secs)
        send_command(conn, ":INIT:CONT ON;\n",wait_secs)
        print("Start Capture....\n")
        send_command(conn, "MEAS:IQ:CAPT\n",wait_secs)
        status = get_message(conn, ":STAT:OPER?\n",wait_secs)
        print("Sweep Status:  " + status)

        first_iq_data = get_message(conn, "TRAC:IQ:DATA?\n",wait_secs)
        print(len(first_iq_data))
        total_iq_data = ""
        if (first_iq_data[0]=="#"):
            nbytes_to_look = int(first_iq_data[1])
            print("nbytestolook="+str(nbytes_to_look))
            nbytes = int(first_iq_data[2:2+nbytes_to_look])
            print("nbytesfirstcall="+str(nbytes))
            countbytes = nbytes
            while (len(total_iq_data)<nbytes):
                time.sleep(2)
                iq_data = get_message(conn, "TRAC:IQ:DATA?\n",wait_secs)
                iq_data = iq_data[2:-1]
                if countbytes<len(iq_data): iq_data = iq_data[:countbytes]
                total_iq_data += iq_data
                countbytes -= len(iq_data)
                print(countbytes)
        send_command(conn, ":IQ:DISCard\n",wait_secs)
        timestamp = datetime.datetime.now()
        timestamp_string = timestamp.strftime("%Y%m%d%H%M%S")
        #print(dati)
        splitpathfile = c.log_iq_file.rsplit(".",1)
        pathfile = splitpathfile[0]+"_"+timestamp_string+"."+splitpathfile[1]
        log_file = open(pathfile, 'w')
        log_file.write('{}\n'.format(total_iq_data))
        log_file.close()
        time.sleep(1)
    exit(0)

def dbmm2_to_vm(value):
    value_in_dbmuvm = value + 115.8
    value_in_vm = 10**((value_in_dbmuvm-120)/20)
    return value_in_vm


def measureMS2090A(ch, conn, location_name):
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

    #log_file.write('Timestamp di esecuzione: {}\n'.format(curr_timestamp))

    for f in range(c.num_frequencies):
        ch.pingToWatchdog()

        curr_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        print("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))
        #servicemanager.LogInfoMsg("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))

        c.transmission_freq_used = False
        if c.frequency_center[f] in c.transmission_freq:  # Controllo di frequenza di invio
            c.transmission_freq_used = True

        if c.iq_mode == 1:
            if c.transmission_freq_used == True and c.isTransfering == True:
                print("Invio dati in IQ_MODE nella frequenza attuale. Passo alla frequenza successiva.")
                continue

        setup_for_single_freq(conn, f)

        for i in range(c.time_search_for_adjust_ref_level_scale):
            adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], c.time_search_for_adjust_ref_level_scale, c.y_ticks, c.minimum_level_no_pre_amp[f])

        for i in range(c.number_samples_chp):
            emf_measured_chp = get_message(conn, ':FETCH:CHP:CHP?\n')  # Fetch current value of channel power
            measured_emf_matrix_base_station[f, i] = float(emf_measured_chp)
            time_array[f, i] = datetime.datetime.now()
            emf_in_vm = dbmm2_to_vm(measured_emf_matrix_base_station[f, i])

            if c.print_debug > 0:
                log_file.write('Timestamp: {} - Frequency: {} - Channel power in DBm/m2: {} - Channel power in V/m: {}\n'.format(
                    datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],
                    measured_emf_matrix_base_station[f, i], emf_in_vm))
            else:
                log_file.write('{} {} {} {}\n'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],
                                                   measured_emf_matrix_base_station[f, i], emf_in_vm))

            # csv_file.write('{},{},{}\n'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],
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

def measureMS2760A(ch, conn, location_name):
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
        ch.pingToWatchdog()
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

