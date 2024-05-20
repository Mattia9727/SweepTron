import datetime
import os, json
import threading
import time

import pika

from my_utils.log_utils import print_in_log
from my_utils.sensing_utils import measure_ultraportable, measure_rack, interp_af, iq_measure_rack
from my_utils.mq_utils import callbackTransferData, startTransferData, pingToWatchdog, stopToWatchdog
from my_utils.anritsu_conn_utils import general_setup_connection_to_device

import constants as c


def sensing(ch):
    # Crea un socket
    # find_device()
    conn,location_name = general_setup_connection_to_device()
    c.antenna_factor = interp_af(c.frequency_center)
    today = -1
    # Monitoring of all DL frequencies
    while True:
        pingToWatchdog(ch)

        condition = (4 <= datetime.datetime.now().hour < 7)
        if condition or c.debug_transfer:
            if c.transferedToday == 0 or c.debug_transfer:
                startTransferData(ch)
            c.transferedToday = 1
            today = datetime.datetime.today().day
        else:
            if today != datetime.datetime.today().day:
                c.transferedToday = 0
        c.update_all()
        if c.device_type == "MS2760A":
            measure_ultraportable(ch, conn, location_name)
        elif c.device_type == "MS2090A":

            if c.iq_mode == 0:
                measure_rack(ch, conn, location_name)
            else:
                iq_measure_rack(ch, conn, location_name)


def consume_thread():
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params, heartbeat=10))
    channel = connection.channel()

    channel.queue_declare(queue='T-S')

    channel.basic_consume(queue='T-S',
                          auto_ack=True,
                          on_message_callback=callbackTransferData)

    print_in_log("Inizio consume")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print_in_log(' [x] Consumatore interrotto.')


def start_consuming_thread():
    # Crea un thread e avvia la funzione consume()
    thread = threading.Thread(target=consume_thread)
    thread.daemon = True
    thread.start()


def sensing_init():
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))

    channel = connection.channel()

    channel.queue_declare(queue='S-P')

    channel.queue_declare(queue='S-T')
    channel.queue_declare(queue='S-W')
    try:
        print_in_log("Sensing microservice ON")

        start_consuming_thread()
        sensing(channel)
    except InterruptedError:
        stopToWatchdog(channel)

if __name__ == "__main__":
    sensing_init()