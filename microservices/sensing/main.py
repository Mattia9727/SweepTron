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
    transfer_day = -1
    iq_hour = datetime.datetime.now().hour
    # Monitoring of all DL frequencies
    while True:
        pingToWatchdog(ch)

        condition = (4 <= datetime.datetime.now().hour < 7)
        if condition or c.debug_transfer:                               #Condizione di trasferimento, modificabile
            if c.transferedToday == 0 or c.debug_transfer:              #Se oggi il trasferimento non è avvenuto
                startTransferData(ch)                                   #Avvia trasferimento
            c.transferedToday = 1                                       #Flag che segna l'avvenuto trasferimento di oggi
            transfer_day = datetime.datetime.today().day                       #Aggiorno numero del giorno in cui è avvenuto il trasferimento
        else:
            if transfer_day != datetime.datetime.today().day:                  #Se è cambiato il giorno
                c.transferedToday = 0                                   #Si può di nuovo avviare il trasferimento
        c.update_all()                                                  #Ricarica configurazione da json


        if c.device_type == "MS2760A":                                  #In base al tipo di analizzatore e al tipo di
            measure_ultraportable(ch, conn, location_name)              #cattura lancia la funzione corrispondente
        elif c.device_type == "MS2090A":
            condition = (iq_hour != datetime.datetime.now().hour)
            if c.iq_mode == 1 or condition:
                iq_measure_rack(ch, conn, location_name)
                iq_hour = datetime.datetime.now().hour
            else:
                measure_rack(ch, conn, location_name)


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