import datetime
import math
import os


from math import sqrt

import numpy as np
from matplotlib import pyplot as plt

import constants as c

from .anritsu_conn_utils import connect_to_device, get_message, send_command, get_error, \
    setup_for_single_freq, general_setup_connection_to_device, update_error_log
import time

from .log_utils import print_in_log
from .mq_utils import pingToWatchdog


import sys
import logging

# Imposta il file di log
LOG_FILE = "C:\\Users\\pc\\Desktop\\SweepTron_Sensing_sens_utils.log"
class Logger(object):
    def __init__(self, log_file):
        self.log = open(log_file, "a")

    def write(self, message):
        self.log.write(message)
        self.log.flush()  

    def flush(self):
        pass  # Necessario per compatibilità con stdout

sys.stdout = Logger(LOG_FILE)

print(" SweepTron_Sensing: Il servizio è stato avviato!")
sys.stdout.flush() 


def interp_ac(freqs):
    ac_anritsu = np.genfromtxt(c.ac_anritsu, delimiter=';', skip_header=1) #legge dal fil .csv
    freq_mhz = ac_anritsu[:, 0] #sono in MHz
    ac_values = ac_anritsu[:, 1]
    ac_sel_frequencies=np.interp(freqs,freq_mhz,ac_values)
    return ac_sel_frequencies #ritorna il vettore con i valori selezionati per ogni frequenza centrale data in input

def interp_af(freqs):

    # Carica i dati dal file di testo
    af_keysight = np.genfromtxt(c.af_keysight, delimiter=';', skip_header=1)


    # Estrai le frequenze in MHz dalla prima colonna
    freq_mhz = af_keysight[:, 0]  # Converti da MHz a kHz
    af_values = af_keysight[:, 1] 

    # Trova il valore minimo e massimo delle frequenze
   #min_freq = np.min(freq_mhz)
    #max_freq = np.max(freq_mhz)

    # Crea un vettore di frequenze interpolate
    #step = 0.5  # Passo dell'interpolazione
    #freq_interp = np.arange(min_freq, max_freq + step, step) # creare un array di valori equispaziati a partire da min_freq fino a max_freq, con un passo di interpolazione pari a step (0.5 in questo caso)

    # Esegui l'interpolazione lineare
    #af_interp = np.interp(freq_interp, freq_mhz, af_keysight[:, 1])

    # Inizializza un array per le ampiezze selezionate
    #af_sel_frequencies = np.zeros(len(freqs))

    #vettore contenente gli AF relativi alle frequenze dei canali da scannerizzare
    af_sel_frequencies=np.interp(freqs,freq_mhz,af_values)

    # Seleziona le ampiezze corrispondenti alle frequenze numeriche
    #for i, freq in enumerate(freqs):
    #    index = np.where(freq_interp == freq)[0]
    #    if len(index) > 0:
    #        af_sel_frequencies[i] = af_interp[index[0]]

    # af_sel_frequencies contiene le ampiezze selezionate
    return af_sel_frequencies #ritorna il vettore con i valori selezionati per ogni frequenza centrale data in input


def calculate_vm_from_dbm(dbm,af,ac):
    #return (1/sqrt(20))*10**((float(dbm)+float(af))/20)
    return 10**((float(dbm)+float(ac)+float(af)-13.01)/20)

def adjust_ref_level_scale_div(conn, curr_margin, time_search_max, y_ticks, min_marker, freq_start):
    max_marker = -200
    calc_min_marker = 200
    if_gain_margin = 15
    if_gain_threshold = -35

    no_error = False
    while (not no_error):
        try:
            for i in range(3):
                time.sleep(1)
                m1message = get_message(conn, 'CALCulate:MARKer1:STATe?\n')
                m2message = get_message(conn, 'CALCulate:MARKer2:STATe?\n')
        
            m1status = int(m1message)
            m2status = int(m2message)
            if m1status != 1:
                send_command(conn, 'CALCulate:MARKer1:STATe 1\n')
            if m2status != 1:
                send_command(conn, 'CALCulate:MARKer2:STATe 1\n')

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
            no_error = True
        except ValueError:
            no_error = False
    reference_level = int(max_marker) + curr_margin

    calc_min_marker = int(calc_min_marker) - curr_margin

    #print_in_log("Actual min margin {} Should be like {}".format(calc_min_marker, min_marker))

    str_level = ':DISP:WIND:TRAC:Y:SCAL:RLEV {}\n'.format(reference_level)
    send_command(conn,str_level)  # setting reference level

    #scale_div = abs(reference_level - min_marker) / y_ticks
    scale_div = abs(reference_level - calc_min_marker) / y_ticks
    if scale_div>15: scale_div=15
    if scale_div<1: scale_div=1
    str_scale_div = ':DISP:WIND:TRAC:Y:PDIVISION {}\n'.format(int(scale_div))
    send_command(conn,str_scale_div)  # automatic scale div setting

    if c.device_type == "MS2760A" or c.device_type == "ultraportable":
        if (int(max_marker) + if_gain_margin < if_gain_threshold) or c.force_if_gain:
            send_command(conn,":POW:IF:GAIN:STAT ON\n")
        else:
            send_command(conn, ":POW:IF:GAIN:STAT OFF\n")

    return reference_level, scale_div


# def plot_measure(measured_emf_matrix_base_station,f):
#     t = datetime.datetime.now()
#     y, M, d, h, m, s = t.year, t.month, t.day, t.hour, t.minute, round(t.second)
#     plt.plot(measured_emf_matrix_base_station[f, :], "b-", linewidth=2)
#     plt.xlabel("Sample Number [unit]", fontsize=14)
#     plt.ylabel("Channel Power [V/m]", fontsize=14)
#     plt.title("Frequency {} MHz Timestamp: {}/{}/{}, {}:{}:{}".format(c.frequency_center[f], y, M, d, h, m, s),
#               fontsize=16)
#
#     # Save the figure with a unique file name based on date and time
#     if not os.path.exists(c.grafici_dir):
#         # Create a new directory because it does not exist
#         os.makedirs(c.grafici_dir)
#
#     plot_file = 'freq_{}.jpg'.format(c.frequency_center[f])
#     plt.savefig(os.path.join(c.grafici_dir, plot_file))
#     plt.clf()

def iq_measure_rack(ch, conn, location_name):

    import pyvisa as visa
    rm = visa.ResourceManager()
    spa = rm.open_resource('TCPIP::10.0.0.2::9001::SOCKET')
    spa.timeout = 10000      # Set Timeout to a value ighter than Capture time
    spa.read_termination = '\n'
    spa.write_termination = '\n'
    spa.chunk_size = 2048

    for f in range(c.iq_num_frequencies):
        pingToWatchdog(ch)
        print_in_log("inizio cattura iq per freq "+str(c.iq_frequency_center[f]))

        spa.write(":MMEMory:STORe:CAPTure:MODE MANual")

        spa.write(":SENS:FREQ:START {} MHz".format(c.iq_frequency_start[f]))
        spa.write(":SENS:FREQ:STOP {} MHz".format(c.iq_frequency_stop[f]))
        bandwidth = c.iq_frequency_stop[f] - c.iq_frequency_start[f]

        # Set sweep mode
        # spa.write(":SWEep:MODE FFT")  # NON SUPPORTATO IN MS27201A

        # Set RBW
        #spa.write(":SENS:BWID:RES {} MHz".format(bandwidth))

        # Set Reference Level to -30 dBm
        spa.write(":DISP:WIND:TRAC:Y:SCAL:RLEV -70")

        # Set to single sweep
        spa.write(":INIT:CONT ON")

        # Set number of display points to calculate frequency array
        # write("DISP:POIN 601;")

        # Get number of display points to calculate frequency array
        # print(spa.query(":DISP:POIN?;"))

        spa.write(":SENS:AVER:TYPE NORM")

        if (bandwidth == 10): sb = "SB12"
        elif (bandwidth == 20): sb = "SB9"
        elif (bandwidth == 40): sb = "SB6"
        elif (bandwidth == 80): sb = "SB3"
        else: sb = "SB19"

        # Prepare per IQ Capture
        spa.write("IQ:SAMP {}".format(sb))
        spa.write(":IQ:LENG {} {}".format(c.iq_length_value, c.iq_length_unit))
        spa.write(":IQ:BITS {}".format(c.iq_bits))
        spa.write(":IQ:MODE SING")
        spa.write(":IQ:TIME OFF")
        spa.write(":TRAC:IQ:DATA:FORM PACK")
        # spa.write(":TRAC:IQ:DATA:FORM ASC")
        spa.write(":INIT:CONT ON")

        print_in_log("Start IQ Capture\n")

        spa.write("MEAS:IQ:CAPT")
        time.sleep(1)

        spa.write("TRAC:IQ:DATA?")
        try:
            iq_data_header = spa.read_raw().decode()
            print(len(iq_data_header))

            if iq_data_header[0] == '#':
                spa.read_termination = ''
                nlength = int(iq_data_header[1])
                length = int(iq_data_header[2:2 + nlength])

                iq_data = spa.read_bytes(length - (len(iq_data_header)-2-nlength))
                spa.write(":IQ:DISCard")
                timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H%M%SZ')
                dgz_filename = c.iq_measures_dir+timestamp+".dgz"
                with open(dgz_filename, "wb") as file:
                    file.write(iq_data)

                spa.read_termination = '\0'
                spa.write(":IQ:METadata?")
                iq_metadata_header = spa.read_bytes(6).decode()
                if (iq_metadata_header[0] == "#"):
                    nlength = int(iq_metadata_header[1])
                    length = int(iq_metadata_header[2:2 + nlength])
                    iq_metadata = spa.read_bytes(length).decode().replace("Unknown",dgz_filename)
                    if iq_metadata.endswith("\n"):
                        iq_metadata = iq_metadata[:-1]
                    with open(dgz_filename+"m", "w") as file:
                        file.write(iq_metadata) 
        except Exception as e:
            print_in_log("Errore Cattura IQ: "+str(e))
            update_error_log("Errore Cattura IQ: "+str(e))
            if os.path.exists(dgz_filename):
                os.remove(dgz_filename)
            if os.path.exists(dgz_filename+"m"):
                os.remove(dgz_filename+"m")
        if c.iq_mode==1:
                exit(0)
    return


def dbmm2_to_vm(value):
    value_in_dbmuvm = value + 115.8
    value_in_vm = 10**((value_in_dbmuvm-120)/20)
    return value_in_vm

def vm_to_dbmm2(value_in_vm):
    value_in_dbmuvm = 20 * math.log10(value_in_vm) + 120
    value_in_dbmm2 = value_in_dbmuvm - 115.8
    return value_in_dbmm2

def measure_rack(ch, conn, location_name):
    measured_emf_matrix_base_station = np.zeros((c.num_frequencies, c.number_samples_chp))
    time_array = np.empty((c.num_frequencies, c.number_samples_chp), dtype=object)

    if not os.path.exists(c.logs_dir):
        # Create a new directory
        os.makedirs(c.logs_dir)

    # Create and open a TXT file to record data


    # # Create and open a CSV file to record data
    # csv_file = open(os.path.join(c.log_file + '.csv'), 'a')

    curr_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    #log_file.write('Timestamp di esecuzione: {}\n'.format(curr_timestamp))

    for f in range(c.num_frequencies):
        pingToWatchdog(ch)

        curr_timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        print_in_log("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))
        #servicemanager.LogInfoMsg("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))

        c.transmission_freq_used = False
        if c.frequency_center[f] in c.transmission_freq:  # Controllo di frequenza di invio
            c.transmission_freq_used = True

        if c.iq_mode == 1:
            if c.transmission_freq_used == True and c.isTransfering == True:
                print_in_log("Invio dati in IQ_MODE nella frequenza attuale di trasferimento. Passo alla frequenza successiva.")
                continue

        setup_for_single_freq(conn, f)

        for i in range(c.time_search_for_adjust_ref_level_scale):
            adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], c.time_search_for_adjust_ref_level_scale, c.y_ticks, c.minimum_level_no_pre_amp[f], c.frequency_start[f])

        for i in range(c.number_samples_chp):
            emf_measured_chp = get_message(conn, ':FETCH:CHP:CHP?\n')  # Fetch current value of channel power
            measured_emf_matrix_base_station[f, i] = float(emf_measured_chp)
            time_array[f, i] = datetime.datetime.now()
            emf_in_vm = dbmm2_to_vm(measured_emf_matrix_base_station[f, i])
            while c.lock_file == True:
                time.sleep(0.01)
            c.lock_file = True
            log_file = open(c.log_file, 'a')
            # if c.print_debug > 0:
            #     log_file.write('Timestamp: {} - Frequency: {} - Channel power in DBm/m2: {} - Channel power in V/m: {}\n'.format(
            #         datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],
            #         measured_emf_matrix_base_station[f, i], emf_in_vm))
            # else:
            log_file.write('{} {} {} {}\n'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],
                                                   round(measured_emf_matrix_base_station[f, i],3), round(emf_in_vm,3)))

            log_file.close()
            c.lock_file = False
            # csv_file.write('{},{},{}\n'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],
            #                                    measured_emf_matrix_base_station[f, i]))
            time.sleep(c.inter_sample_time)


        #OLD
        #plot_measure(measured_emf_matrix_base_station, f)
        #location_name_mat = '{}.mat'.format(location_name)
        #np.save(location_name_mat, measured_emf_matrix_base_station)

        c.transmission_freq_used = False

    # Close the log files
    # csv_file.close()
    # Add code to stop the loop or exit gracefully if needed


#function made for acquisition of measurements for ARPA (MS2710A)
def measure_monitoring_unit(ch, conn, location_name):
    measured_emf_matrix_base_station = np.zeros((c.num_frequencies, c.number_samples_chp)) #alloca la matrice che conterrà i valori per ogni banda e num di sample definito
    time_array = np.empty((c.num_frequencies, c.number_samples_chp), dtype=object)

    if not os.path.exists(c.logs_dir):
        # Create a new directory
        os.makedirs(c.logs_dir)

    # Create and open a TXT file to record data


    # # Create and open a CSV file to record data
    # csv_file = open(os.path.join(c.log_file + '.csv'), 'a')

    # if c.print_debug > 0:
    #     log_file = open(c.log_file, 'a')
    #     log_file.write('Timestamp di esecuzione: {}\n'.format(curr_timestamp))
    #     log_file.close()


    #faccio il preset dello strumento
    send_command(conn, 'syst:pres\n')

    print("ho fatto il preset dello strumento")
    sys.stdout.flush() 

    for f in range(c.num_frequencies):
        pingToWatchdog(ch)

        curr_timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        print_in_log("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))

        c.transmission_freq_used = False
        if c.frequency_center[f] in c.transmission_freq:  # Controllo di frequenza di invio
            c.transmission_freq_used = True

        if c.iq_mode == 1 and c.transmission_freq_used == True and c.isTransfering == True: #TODO: VERIFICARE CON IL PROFESSORE SE FARE CONTROLLO SOLO CON CATTURA IQ O SEMPRE
            print_in_log("Invio dati in IQ_MODE nella frequenza attuale di trasferimento. Passo alla frequenza successiva.")
            continue


        setup_for_single_freq(conn, f)  #Faccio il setup iniziale dello strumento da fare per ogni banda analizzata


       # for i in range(c.time_search_for_adjust_ref_level_scale):
       #     adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], c.time_search_for_adjust_ref_level_scale, c.y_ticks, c.minimum_level_no_pre_amp[f], c.frequency_start[f])


        for i in range(c.number_samples_chp): #ciclo per il numero di volte (campioni) che decido io nel file di conf
            
            print("sono nel for di number_samples_chp")
            sys.stdout.flush() 
            #passo in mode normal 
            send_command(conn,'trac1:type NORM\n')
            print("trac1:NORM")
            sys.stdout.flush() 
            send_command(conn,':CONFigure:CHPower\n') #configuro il channel power
            print("configurato ch power")
            sys.stdout.flush() 
            send_command(conn,'init:imm\n')
            print("mandato primo init")
            sys.stdout.flush() 
            #imposta la traccia al massimo 
            send_command(conn,'trac1:type max\n')
            print("trac1:type max")
            sys.stdout.flush() 
            #aggiunge un marker nel punto di massimo
            send_command(conn,'calc:mark1:max\n')
            print("calc mark1 max")
            sys.stdout.flush() 
            #restituisce il valore dell asse y (potenza segnale) in corrispondenza del marker
            max_marker=get_message(conn,'calc:mark1:y?\n')
            print("max_marker", max_marker,type(max_marker))
            sys.stdout.flush() 
            max_marker=float(max_marker)
            #aggiungiamo 20db rispetto al valore di massimo 
            new_ref_lev='disp:wind:trac:y:scal:rlev {}\n'.format(max_marker+20)
            send_command(conn,new_ref_lev)
            print("impostata reference lev",new_ref_lev)
            sys.stdout.flush() 
            #passiamo in modalità average
            send_command(conn,'trac1:type aver\n')
            print("trac1:type aver")
            sys.stdout.flush() 
            send_command(conn,':TRAC:DET RMS\n') #imposta il detector in modalità rms (regola la singola acquisione delle mille tracce che vengono mediate)
            print("DET RMS")
            sys.stdout.flush() 
            samples_for_averages_str = ':SENS:AVER:COUN {}\n'.format(int(c.samples_for_averages)) #imposta il numero di medie 
            send_command(conn, samples_for_averages_str)
            print("eseguito sens:aver:count")
            sys.stdout.flush() 
            send_command(conn, ':init:imm:all\n')
            #attendo di fare il fetch fino a che il comando precedente non ha terminato
            #send_command(conn, '*wai\n')
            print("sto per eseguire il comando OPC")
            sys.stdout.flush() 
            # Imposta OPC quando la misura è completata
            send_command(conn,'*OPC\n')
            # Loop di polling per controllare ESR finché OPC non è impostato

            print("sto entrando nel ciclo di polling")
            sys.stdout.flush() 

            time.sleep(3) #attende un tempo di base di 3 sec
            while True:
                esr_value = int(get_message(conn,'*ESR?\n'))  # Interroga il registro ESR
                print("valore flag", esr_value)
                sys.stdout.flush()
                if esr_value & 1:  # Controlla se il bit OPC è impostato (bit 0)
                    break  # Esce dal loop quando ESR=1
                time.sleep(0.5)  # Attendi 100ms prima di controllare di nuovo
            
            print("sono uscito dal ciclo di polling, valore flag è", esr_value)
            sys.stdout.flush() 
            #fetch del valore
            emf_measured_chp = get_message(conn, ':FETCH:CHP:CHP?\n') 

            print("ho fatto il fetch") 
            sys.stdout.flush() 

            if emf_measured_chp == "" or len(emf_measured_chp.split("\n"))>2:
                print_in_log("Problema valore CHP, reset connessione e riprovo misurazione...")
                conn.close()
                conn = None
                conn, _ = general_setup_connection_to_device()
                i-=1
                continue

            print("sto facendo il calcolo emf to vm")
            sys.stdout.flush() 
            emf_measured_vm = calculate_vm_from_dbm(emf_measured_chp.split("\n",1)[0],c.af_factor[f],c.ac_factor[f])
            emf_measured_dbmm2 = vm_to_dbmm2(emf_measured_vm)
            measured_emf_matrix_base_station[f, i] = float(emf_measured_vm)
            time_array[f, i] = datetime.datetime.now()

            if c.print_debug > 0:
                print_in_log('{} - {} - {} - {}'.format(
                            datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],emf_measured_dbmm2,
                            measured_emf_matrix_base_station[f, i]))
            while c.lock_file == True:
                time.sleep(0.01)
            c.lock_file = True
            log_file = open(c.log_file, 'a')
            # if c.print_debug > 0:
            #     log_file.write('Timestamp: {} - Frequency: {} - Channel power: {}\n'.format(
            #         datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],
            #         measured_emf_matrix_base_station[f, i]))
            # else:
            log_file.write('{} {} {} {}\n'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f], round(emf_measured_dbmm2,3),
                                               round(measured_emf_matrix_base_station[f, i],3)))

            # csv_file.write('{},{},{}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
            #                                    measured_emf_matrix_base_station[f, i]))
            log_file.close()
            c.lock_file = False
            time.sleep(c.inter_sample_time)


#funzione di acquisizione per ultraportable anritsu MS2760A 
def measure_ultraportable(ch, conn, location_name):
    measured_emf_matrix_base_station = np.zeros((c.num_frequencies, c.number_samples_chp))
    time_array = np.empty((c.num_frequencies, c.number_samples_chp), dtype=object)

    if not os.path.exists(c.logs_dir):
        # Create a new directory
        os.makedirs(c.logs_dir)

    # Create and open a TXT file to record data


    # # Create and open a CSV file to record data
    # csv_file = open(os.path.join(c.log_file + '.csv'), 'a')

    # if c.print_debug > 0:
    #     log_file = open(c.log_file, 'a')
    #     log_file.write('Timestamp di esecuzione: {}\n'.format(curr_timestamp))
    #     log_file.close()

    for f in range(c.num_frequencies):
        pingToWatchdog(ch)


        curr_timestamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        print_in_log("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], curr_timestamp))

        c.transmission_freq_used = False
        if c.frequency_center[f] in c.transmission_freq:  # Controllo di frequenza di invio
            c.transmission_freq_used = True

        if c.iq_mode == 1 and c.transmission_freq_used == True and c.isTransfering == True: #TODO: VERIFICARE CON IL PROFESSORE SE FARE CONTROLLO SOLO CON CATTURA IQ O SEMPRE
            print_in_log("Invio dati in IQ_MODE nella frequenza attuale di trasferimento. Passo alla frequenza successiva.")
            continue


        setup_for_single_freq(conn, f)

        for i in range(c.time_search_for_adjust_ref_level_scale):
            adjust_ref_level_scale_div(conn, c.initial_guard_amplitude[f], c.time_search_for_adjust_ref_level_scale, c.y_ticks, c.minimum_level_no_pre_amp[f], c.frequency_start[f])


        for i in range(c.number_samples_chp):

            emf_measured_chp = get_message(conn, ':FETCH:CHP:CHP?\n')  # Fetch current value of channel power
            if emf_measured_chp == "" or len(emf_measured_chp.split("\n"))>2:
                print_in_log("Problema valore CHP, reset connessione e riprovo misurazione...")
                conn.close()
                conn = None
                conn, _ = general_setup_connection_to_device()
                i-=1
                continue
            emf_measured_vm = calculate_vm_from_dbm(emf_measured_chp.split("\n",1)[0],c.antenna_factor[f])
            emf_measured_dbmm2 = vm_to_dbmm2(emf_measured_vm)
            measured_emf_matrix_base_station[f, i] = float(emf_measured_vm)
            time_array[f, i] = datetime.datetime.now()

            if c.print_debug > 0:
                print_in_log('{} - {} - {} - {}'.format(
                            datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],emf_measured_dbmm2,
                            measured_emf_matrix_base_station[f, i]))
            while c.lock_file == True:
                time.sleep(0.01)
            c.lock_file = True
            log_file = open(c.log_file, 'a')
            # if c.print_debug > 0:
            #     log_file.write('Timestamp: {} - Frequency: {} - Channel power: {}\n'.format(
            #         datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f],
            #         measured_emf_matrix_base_station[f, i]))
            # else:
            log_file.write('{} {} {} {}\n'.format(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'), c.frequency_center[f], round(emf_measured_dbmm2,3),
                                               round(measured_emf_matrix_base_station[f, i],3)))

            # csv_file.write('{},{},{}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
            #                                    measured_emf_matrix_base_station[f, i]))
            log_file.close()
            c.lock_file = False
            time.sleep(c.inter_sample_time)

        #OLD
        # plot_measure(measured_emf_matrix_base_station, f)
        # location_name_mat = '{}.mat'.format(location_name)
        # np.save(location_name_mat, measured_emf_matrix_base_station)
        # c.transmission_freq_used = False


    # Close the log files

    # csv_file.close()
    # Add code to stop the loop or exit gracefully if needed

