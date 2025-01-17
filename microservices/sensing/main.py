import datetime
import os, json
import threading
import time

import pika

from my_utils.log_utils import print_in_log
from my_utils.sensing_utils import measure_ultraportable, measure_rack, interp_af, interp_ac, iq_measure_rack,measure_monitoring_unit
from my_utils.mq_utils import callback_transfer_data, startTransferData, pingToWatchdog, stopToWatchdog, send_error_log
from my_utils.anritsu_conn_utils import general_setup_connection_to_device, get_error

import constants as c


def sensing(ch):
    # Crea un socket
    # find_device()
    conn,location_name = general_setup_connection_to_device() #fa il setup generale. INCLUDE ALCUNI COMANDI SCPI!!!
    c.antenna_factor = interp_af(c.frequency_center)  
    c.cable_att=interp_ac(c.frequency_center)          #Recupera antenna factor (per ultraportable)
    iq_hour = datetime.datetime.now().hour       
    if (iq_hour<7): transfer_day = 0
    else: transfer_day = 1
    
    # Monitoring of all DL frequencies
    while True:
        get_error(conn)

        #Blocco di codice che controlla se ci sono log di errore da inviare, e se si li invia a fini di allarme
        try:
            with open(c.error_log_file,"r") as f:
                error_lines = f.readlines()
            if len(error_lines) != 0:
                send_error_log(ch)
        except FileNotFoundError:
            open(c.error_log_file,"w")
        except Exception as e:
            print("An exception occurred:", e)
            

        pingToWatchdog(ch)                                              #Ping di notifica attività al watchdog

        condition = (4 <= datetime.datetime.now().hour < 7)             #dice che il trasferimento deve avvenire tra le 4 e le 7
        if condition or c.debug_transfer:                               #Condizione di trasferimento, modificabile (se il trasferimento è tra le 4 o le 7 o se ci sta il debug transfer=!)
            if c.transferedToday == 0 or c.debug_transfer:              #Se oggi il trasferimento non è avvenuto
                startTransferData(ch)                                   #Avvia trasferimento
            c.transferedToday = 1                                       #Flag che segna l'avvenuto trasferimento di oggi
            transfer_day = datetime.datetime.today().day                #Aggiorno numero del giorno in cui è avvenuto il trasferimento
        else:
            if transfer_day != datetime.datetime.today().day:           #Se è cambiato il giorno
                c.transferedToday = 0                                   #Si può di nuovo avviare il trasferimento
        c.update_all()                                                  #Ricarica configurazione da json


        if c.device_type == "MS2760A" or c.device_type == "ultraportable": #In base al tipo di analizzatore e al tipo di
            measure_ultraportable(ch, conn, location_name)                 #cattura lancia la funzione corrispondente
        elif c.device_type == "MS2090A" or c.device_type == "rack":
            condition = (iq_hour != datetime.datetime.now().hour)
            if c.iq_mode == 1 or condition:
                iq_measure_rack(ch, conn, location_name)
                iq_hour = datetime.datetime.now().hour
            else:
                measure_rack(ch, conn, location_name)
        elif c.device_type == "MS2090A" or c.device_type == "rack":
            measure_rack(ch, conn, location_name)
        elif c.device_type == "MS27102A" :
            measure_monitoring_unit(ch, conn, location_name)



def consume_thread():
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params, heartbeat=10))
    channel = connection.channel()
#Viene dichiarata una coda chiamata 'T-S' utilizzata per trasferire dati da transfer a sensing
    channel.queue_declare(queue='T-S')

#I messaggi che arrivano sulla coda vengono processati dalla funzione callback_transfer_data
    channel.basic_consume(queue='T-S',
                          auto_ack=True,
                          on_message_callback=callback_transfer_data)

    print_in_log("Inizio consume")
    try:
        #inizia il ciclo infinito di consuming su quella coda
        channel.start_consuming()
        #: Se  si interrompe il processo da tastiera ( usando Ctrl + C), viene catturata l'eccezione KeyboardInterrupt e viene registrato l'evento nel log.
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

 #inizializza le code  tra sensing-processing sensing-transfer sensing-watchdog
    channel.queue_declare(queue='S-P')

    channel.queue_declare(queue='S-T')
    channel.queue_declare(queue='S-W')
    pingToWatchdog(channel)
    try:
        print_in_log("Sensing microservice ON")
        
        start_consuming_thread()
        sensing(channel)
    except InterruptedError:
        stopToWatchdog(channel)

if __name__ == "__main__":
    sensing_init()