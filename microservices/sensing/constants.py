import json

#data_folder = "C:\\Users\\matti" + "\\" + 'Desktop' + "\\" + 'SweeptronData'
data_folder = "C:\\Users\\user" + "\\" + 'Desktop' + "\\" + 'SweeptronData'

print_debug = iq_mode = grafici_dir = logs_dir = measures_dir = iq_measures_dir = settings_path = sensing_activity = \
    processing_activity = transfer_activity = pika_params = service_log_file = disable_restart = \
    processed_iq_measures_dir = error_log_file = log_file = log_iq_file = compressed_log_file = \
    compressed_iq_log_file = transmission_freq = transmission_freq_used = transferedToday = \
    isTransfering = device_type = debug_transfer = server_ip = url = error_url = location = lock_file = \
    spectrum_analyzer_ip = spectrum_analyzer_port = antenna_file = af_keysight = initial_reference_level = \
    y_ticks = command_rolling_average_time = inter_sample_time = number_samples_chp = samples_for_averages = \
    frequency_start = frequency_stop = iq_frequency_start = iq_frequency_stop = \
    num_frequencies = iq_num_frequencies = frequency_center = iq_frequency_center = minimum_level_no_pre_amp = \
    initial_guard_amplitude = time_search_for_adjust_ref_level_scale = iq_length_value = iq_length_unit = \
    iq_bits = None


def update_all():
    global print_debug, iq_mode, grafici_dir, logs_dir, measures_dir, iq_measures_dir, settings_path, sensing_activity,\
        processing_activity, transfer_activity, pika_params, service_log_file, disable_restart,  \
        processed_iq_measures_dir, error_log_file, log_file, log_iq_file, compressed_log_file,  \
        compressed_iq_log_file, transmission_freq, transmission_freq_used,  transferedToday,  \
        isTransfering, device_type, debug_transfer, server_ip, url, error_url, location, lock_file, \
        spectrum_analyzer_ip, spectrum_analyzer_port, antenna_file, af_keysight, initial_reference_level, y_ticks, \
        command_rolling_average_time, inter_sample_time, number_samples_chp, samples_for_averages, iq_num_frequencies, \
        frequency_start, frequency_stop, iq_frequency_start, iq_frequency_stop, \
        num_frequencies, frequency_center, iq_frequency_center, minimum_level_no_pre_amp, initial_guard_amplitude, \
        time_search_for_adjust_ref_level_scale, iq_length_value, iq_length_unit, iq_bits

    settings_path = data_folder+"\\"+'config.json'

    # Carica le costanti dal file JSON
    with open(settings_path) as f:
        constants = json.load(f)

    # Estrai le costanti
    print_debug = constants["print_debug"]
    iq_mode = constants["iq_mode"]
    lock_file = False
    grafici_dir = data_folder+"\\"+ constants["grafici_dir"]
    logs_dir = data_folder+"\\"+ constants["logs_dir"]
    measures_dir = data_folder+"\\"+ constants["measures_dir"]
    iq_measures_dir = data_folder+"\\"+ constants["iq_measures_dir"]

    spectrum_analyzer_ip = constants["spectrum_analyzer_ip"]
    spectrum_analyzer_port = int(constants["spectrum_analyzer_port"])

    error_log_file = data_folder+"\\"+ constants["error_log_file"]
    service_log_file = data_folder+"\\"+ constants["sensing_log_file"]
    log_file = measures_dir+"\\"+ constants["log_file"]
    log_iq_file = iq_measures_dir+"\\"+ constants["log_iq_file"]
    compressed_log_file = data_folder+"\\"+ constants["compressed_log_file"]
    compressed_iq_log_file = data_folder+"\\"+ constants["compressed_iq_log_file"]

    pika_params = constants["pika_params"]
    antenna_file = constants["antenna_file"]
    af_keysight = data_folder+"\\"+ constants["af_keysight"]

    initial_reference_level = constants["initial_reference_level"]
    y_ticks = constants["y_ticks"]
    command_rolling_average_time = constants["command_rolling_average_time"]
    inter_sample_time = constants["inter_sample_time"]
    number_samples_chp = constants["number_samples_chp"]

    samples_for_averages = constants["samples_for_averages"]
    frequency_start = constants["frequency_start"]
    frequency_stop = constants["frequency_stop"]
    iq_frequency_start = constants["iq_frequency_start"]
    iq_frequency_stop = constants["iq_frequency_stop"]

    num_frequencies = len(frequency_start)
    iq_num_frequencies = constants["iq_num_frequencies"]

    frequency_center = [(stop - start) / 2 + start for start, stop in zip(frequency_start, frequency_stop)]
    iq_frequency_center = [(stop - start) / 2 + start for start, stop in zip(iq_frequency_start, iq_frequency_stop)]

    transmission_freq = constants["transmission_freq"]
    transmission_freq_used = constants["transmission_freq_used"]

    transferedToday = constants["transferedToday"]
    isTransfering = constants["isTransfering"]

    device_type = constants["device_type"]
    debug_transfer = constants["debug_transfer"]

    minimum_level_no_pre_amp = constants["minimum_level_no_pre_amp"] * num_frequencies
    initial_guard_amplitude = constants["initial_guard_amplitude"] * num_frequencies
    time_search_for_adjust_ref_level_scale = constants["time_search_for_adjust_ref_level_scale"]

    server_ip = constants["server_ip"]
    url = constants["url"]

    iq_length_value = constants["iq_length_value"]
    iq_length_unit = constants["iq_length_unit"]
    iq_bits = constants["iq_bits"]

    location = constants["location"]

update_all()
