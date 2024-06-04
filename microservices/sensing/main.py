import datetime
import os, json
import threading
import time

import pika

from my_utils.log_utils import print_in_log
from my_utils.sensing_utils import measure_ultraportable, measure_rack, interp_af, iq_measure_rack
from my_utils.mq_utils import callback_transfer_data, startTransferData, pingToWatchdog, stopToWatchdog, send_error_log
from my_utils.anritsu_conn_utils import general_setup_connection_to_device, get_error

import constants as c


def sensing(ch):
    # Crea un socket
    # find_device()
    conn,location_name = general_setup_connection_to_device()
    c.antenna_factor = interp_af(c.frequency_center)            #Recupera antenna factor (per ultraportable)
    transfer_day = -1
    iq_hour = datetime.datetime.now().hour
    # Monitoring of all DL frequencies
    while True:
        get_error(conn)

        #Blocco di codice che controlla se ci sono log di errore da inviare, e se si li invia a fini di allarme
        try:
            with open(c.error_log_file,"r") as f:
                error_lines = f.readlines()
                if error_lines != "":
                    send_error_log(ch)
        except Exception as e:
            print("An exception occurred:", e)

        pingToWatchdog(ch)                                              #Ping di notifica attività al watchdog

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
                          on_message_callback=callback_transfer_data)

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