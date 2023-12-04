import os
from threading import Thread

import numpy as np
import time
import datetime

from matplotlib import pyplot as plt

from anritsu_conn_utils import connect_to_device, get_message, send_command, get_error, find_device

import constants as c
from client.server_conn_utils import send_files_to_server


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


def main():

    # Crea un socket
    conn = connect_to_device()

    # Assuming you've defined a function like send_command and read_response to communicate with obj1.

    # Send an ID query command
    print(get_message(conn,'*IDN?\n'))

    error = get_error(conn)

    if c.print_debug == 1:
        print(error if error is not None else "")

    ### PARTE GPS, DA VEDERE
    location_name = "Roma Tor Vergata"

    gps_raw = get_message(conn, ':FETCh:GPS?\n')  # Fetching the GPS
    gps_array_split = gps_raw.split(',')

    if gps_array_split[0] == 'GOOD FIX':
        curr_latitude = float(gps_array_split[2])
        curr_longitude = float(gps_array_split[3])
        curr_timestamp = gps_array_split[1]

    # Configure instrument settings

    # print(get_message(conn,":FSTRength:ANTenna:LIST:USER?\n")) TODO: Vedere se recuperare dinaicamente nome dell'antenna factor

    send_command(conn,':MODE SPEC\n')
    send_command(conn,':CONFigure:CHPower\n')
    send_command(conn,':FSTRength:STATe 1\n')
    send_command(conn,':FSTRength:ANTenna "{}"\n'.format(c.antenna_file))
    send_command(conn,':UNIT:POW V/M\n')  # Unit in terms of field strength (volt meter). IMPORTANT: DOUBLE CHECK THAT THE ANTENNA FILE ON THE SA IS CORRECT!
    send_command(conn,':POW:RF:ATT:AUTO OFF\n')  # Automatic input attenuation coupling
    send_command(conn,':POW:RF:ATT 0 DB\n')  # Set attenuation to 0 dB
    send_command(conn,':POW:RF:GAIN:STAT OFF\n')  # Turn off pre-amplifier for initial setting

    # Monitoring of all DL frequencies
    while True:  # You might want to replace 'True' with a condition to stop the loop
        measured_emf_matrix_base_station = np.zeros((c.num_frequencies, c.number_samples_chp))
        time_array = np.empty((c.num_frequencies, c.number_samples_chp), dtype=object)

        if not os.path.exists(c.logs_dir):
            # Create a new directory
            os.makedirs(c.logs_dir)

        # Create and open a TXT file to record data
        logFileName = os.path.join(c.logs_dir,c.log_file+'.txt')
        logFile = open(logFileName, 'a')

        # Create and open a CSV file to record data
        csvFileName = os.path.join(c.logs_dir,c.log_file+'.csv')
        csvFile = open(csvFileName, 'a')

        currentTimestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')

        logFile.write('Timestamp di esecuzione: {}\n'.format(currentTimestamp))

        for f in range(c.num_frequencies):
            selected_frequency_start = c.frequency_start[f]
            selected_frequency_stop = c.frequency_stop[f]
            currentTimestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            print("Current Frequency: {}, Starting time: {}".format(c.frequency_center[f], currentTimestamp))

            c.transmission_freq_used = False
            if c.frequency_center[f] in c.transmission_freq:     # Controllo di frequenza di invio
                c.transmission_freq_used = True


            if c.iq_mode == 1:
                if c.transmission_freq_used == True and c.sending == True:
                    print("Invio dati in IQ_MODE nella frequenza attuale. Passo alla frequenza successiva.")
                    continue

            frequenc_range_str = ':SENS:FREQ:STAR {} MHZ;:SENS:FREQ:STOP {} MHZ\n'.format(selected_frequency_start,
                                                                                        selected_frequency_stop)
            send_command(conn,frequenc_range_str)  # Frequency range

            send_command(conn,':ABOR\n')  # Restart the trigger system

            initial_reference_level_str = ':DISP:WIND:TRAC:Y:SCAL:RLEV {}\n'.format(c.initial_reference_level)
            send_command(conn,initial_reference_level_str)  # Automatic reference level above 10 dB

            rbw_str = ':BAND:RES:AUTO ON\n'  # Resolution BW
            send_command(conn,rbw_str)

            send_command(conn,':CONF:CHP\n')  # Configuring channel power (RMS + integration BW equal to SPAN)

            send_command(conn,':INIT:CONT ON\n')  # Continuous sweeping

            send_command(conn,':TRAC:DET RMS\n')  # RMS DETECTOR

            samples_for_averages_str = ':SENS:AVER:COUN {}\n'.format(c.samples_for_averages)
            send_command(conn,samples_for_averages_str)  # Rolling average number of samples

            send_command(conn,':TRAC:TYPE RAV\n',c.command_rolling_average_time)  # Rolling average DETECTOR

            for index_samples in range(c.number_samples_chp):
                emf_measured_chp = get_message(conn,':FETCH:CHP:CHP?\n')  # Fetch current value of channel power
                measured_emf_matrix_base_station[f, index_samples] = float(emf_measured_chp)
                time_array[f, index_samples] = datetime.datetime.now()

                if c.print_debug > 0:
                    logFile.write('Timestamp: {} - Frequency: {} - Channel power: {}\n'.format(
                        datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                        measured_emf_matrix_base_station[f, index_samples]))
                else:
                    logFile.write('{} {} {}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                                                      measured_emf_matrix_base_station[f, index_samples]))

                csvData = '{},{},{}\n'.format(datetime.datetime.now().strftime('%H:%M:%S'), c.frequency_center[f],
                                              measured_emf_matrix_base_station[f, index_samples])
                csvFile.write(csvData)
                time.sleep(c.inter_sample_time)

            t = datetime.datetime.now()
            y, M, d, h, m, s = t.year, t.month, t.day, t.hour, t.minute, round(t.second)
            plt.plot(measured_emf_matrix_base_station[f, :], "b-", linewidth=2)
            plt.xlabel("Sample Number [unit]", fontsize=14)
            plt.ylabel("Channel Power [V/m]", fontsize=14)
            plt.title("Frequency {} MHz Timestamp: {}/{}/{}, {}:{}:{}".format(c.frequency_center[f], y, M, d, h, m, s), fontsize=16)

            # Save the figure with a unique file name based on date and time
            if not os.path.exists(c.grafici_dir):
                # Create a new directory because it does not exist
                os.makedirs(c.grafici_dir)

            plot_file = 'freq_{}.jpg'.format(c.frequency_center[f])
            plt.savefig(os.path.join(c.grafici_dir, plot_file))
            plt.clf()

            location_name_mat = '{}.mat'.format(location_name)
            np.save(location_name_mat, measured_emf_matrix_base_station)
            c.transmission_freq_used = False

        # Close the log files
        logFile.close()
        csvFile.close()
        # Add code to stop the loop or exit gracefully if needed


if __name__ == '__main__':
    #t = Thread(target=send_files_to_server)
    #t.start()

    #find_device()
    #main()
    iq_capture()

