import numpy as np

print_debug=1
iq_mode = 0

antenna_file = "AARONIA_6080"

initial_reference_level = 6  # initial reference level in V/m
y_ticks = 10  # number of y ticks on the screen of the spectrum analyzer
minimum_reference_level = 0  # in V/m
command_rolling_average_time = 2.0  # amount of time in s to compute the rolling average of the trace
inter_sample_time = 0.5  # inter sample time between one chp measurement sample and the following one
number_samples_chp = 40  # number of sampled channel power measurements

samples_for_averages = 100  # number of measurement samples for averages (to compute the channel power)
buffer_size = 6000  # size to take measured trace data from the SA (CHECK)
buffer_timeout = 0.2  # buffer timeout in seconds for the fscanf

# frequency_start=[758,768,778,791,801,811,925,930,940,950,1452,1472,1810,1830,1840,1860,2110,2130,2145,2155,2630,2640,2655,2670,2570,3437,3458,3479,3537,3558,3620,3640,3720]
# frequency_stop=[768,778,788,801,811,821,930,940,950,960,1472,1492,1830,1840,1860,1880,2130,2145,2155,2170,2640,2655,2670,2690,2600,3458,3479,3500,3558,3620,3640,3720,3800]

frequency_start = [768, 713, 801, 842, 930, 885, 1452, 1810, 1715, 2130, 1940, 2655, 2535, 3720, 26900]
frequency_stop = [778, 723, 811, 852, 940, 895, 1472, 1830, 1735, 2145, 1955, 2670, 2550, 3800, 27100]

id_frequencies = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
# id_frequencies=[1]

num_frequencies = len(frequency_start)

emf_array = np.zeros(num_frequencies)
emf_array_traffic = np.zeros(num_frequencies)

frequency_center = np.zeros(num_frequencies)

for f in range(num_frequencies):
    frequency_center[f] = (frequency_stop[f] - frequency_start[f]) / 2 + frequency_start[f]

grafici_dir = "grafici/"
logs_dir = "./logs/"

error_log_file = 'log_errors.txt'
log_file = 'log_data'

transmission_freq = [718.0, 890.0]
transmission_freq_used = False

sending = False
