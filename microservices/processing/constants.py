import os
import numpy as np
import json

data_folder = "C:\\Users\\matti" + "\\" + 'Desktop' + "\\" + 'SweeptronData'
settings_path = os.path.join(data_folder, 'config.json')

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
processed_iq_measures_dir = os.path.join(data_folder, constants["processed_iq_measures_dir"])

error_log_file = os.path.join(data_folder, constants["error_log_file"])
service_log_file = measures_dir + "\\" + constants["processing_log_file"]
log_file = os.path.join(measures_dir, constants["log_file"])
log_iq_file = os.path.join(iq_measures_dir, constants["log_iq_file"])
compressed_log_file = os.path.join(data_folder, constants["compressed_log_file"])
compressed_iq_log_file = os.path.join(data_folder, constants["compressed_iq_log_file"])

pika_params = constants["pika_params"]

transferedToday = constants["transferedToday"]
isTransfering = constants["isTransfering"]
