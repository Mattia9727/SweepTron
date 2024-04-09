import datetime

import constants as c

def print_in_log(message):
    if c.print_debug == 1:
        print(message)
    with(open(c.service_log_file, "a") as f):
        f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message+"\n")