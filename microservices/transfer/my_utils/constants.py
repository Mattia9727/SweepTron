import numpy as np

print_debug=1
iq_mode = 0

grafici_dir = "grafici/"
logs_dir = "./logs/"

error_log_file = '../data/log_errors.txt'
log_file = '../data/log_file.txt'
log_iq_file = '../data/iq_log_file.dgz'
compressed_log_file = '../data/iq_compressed_log_file.txt'

server_ip = "127.0.0.1:5000"
url = "http://{}/upload".format(server_ip)

pika_params = "localhost"
