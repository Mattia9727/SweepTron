import os
import numpy as np
import json

#data_folder = "C:\\Users\\matti" + "\\" + 'Desktop' + "\\" + 'SweeptronData'
data_folder = "C:\\Users\\user" + "\\" + 'Desktop' + "\\" + 'SweeptronData'

print_debug = iq_mode = grafici_dir = logs_dir = measures_dir = iq_measures_dir = settings_path = sensing_activity = \
    processing_activity = transfer_activity = pika_params = service_log_file = disable_restart = \
    processed_iq_measures_dir = error_log_file = log_file = log_iq_file = compressed_log_file = \
    compressed_iq_log_file = transmission_freq = transmission_freq_used = transferedToday = \
    isTransfering = device_type = debug_transfer = server_ip = url = error_url = location = None


def update_all():
    global print_debug, iq_mode, grafici_dir, logs_dir, measures_dir, iq_measures_dir, settings_path, sensing_activity,\
        processing_activity, transfer_activity, pika_params, service_log_file, disable_restart,  \
        processed_iq_measures_dir, error_log_file, log_file, log_iq_file, compressed_log_file,  \
        compressed_iq_log_file, transmission_freq, transmission_freq_used,  transferedToday,  \
        isTransfering, device_type, debug_transfer, server_ip, url, error_url, location

    settings_path =  data_folder + "\\" + 'config.json'


    # Carica le costanti dal file JSON
    with open(settings_path) as f:
        constants = json.load(f)

    # Estrai le costanti
    print_debug = constants["print_debug"]
    iq_mode = constants["iq_mode"]
    grafici_dir = data_folder + "\\" + constants["grafici_dir"]
    logs_dir = data_folder + "\\" + constants["logs_dir"]
    measures_dir = data_folder + "\\" + constants["measures_dir"]
    iq_measures_dir = data_folder + "\\" + constants["iq_measures_dir"]
    processed_iq_measures_dir =  data_folder + "\\" + constants["processed_iq_measures_dir"]

    error_log_file =  data_folder + "\\" + constants["error_log_file"]
    service_log_file = data_folder + "\\" + constants["transfer_log_file"]
    log_file =  measures_dir + "\\" + constants["log_file"]
    log_iq_file =  iq_measures_dir + "\\" + constants["log_iq_file"]
    compressed_log_file =  data_folder + "\\" + constants["compressed_log_file"]
    compressed_iq_log_file =  data_folder + "\\" + constants["compressed_iq_log_file"]

    pika_params = constants["pika_params"]

    transmission_freq = constants["transmission_freq"]
    transmission_freq_used = constants["transmission_freq_used"]

    transferedToday = constants["transferedToday"]
    isTransfering = constants["isTransfering"]

    device_type = constants["device_type"]
    debug_transfer = constants["debug_transfer"]

    server_ip = constants["server_ip"]
    url = constants["url"]
    error_url = constants["error_url"]

    location = constants["location"]

update_all()