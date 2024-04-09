import json

data_folder = "C:\\Users\\matti" + "\\" + 'Desktop' + "\\" + 'SweeptronData'
# data_folder = "C:\\Users\\user" + "\\" + 'Desktop' + "\\" + 'SweeptronData'
settings_path = data_folder+"\\"+'config.json'

# Carica le costanti dal file JSON
with open(settings_path) as f:
    constants = json.load(f)

# Estrai le costanti
print_debug = constants["print_debug"]
iq_mode = constants["iq_mode"]
grafici_dir = data_folder+"\\"+ constants["grafici_dir"]
logs_dir = data_folder+"\\"+ constants["logs_dir"]
measures_dir = data_folder+"\\"+ constants["measures_dir"]
iq_measures_dir = data_folder+"\\"+ constants["iq_measures_dir"]
settings_path = data_folder + "\\config.json"

sensing_activity = False
processing_activity = False
transfer_activity = False
pika_params = constants["pika_params"]
service_log_file = data_folder+"\\"+ constants["watchdog_log_file"]

