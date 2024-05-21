import datetime
import os
import socket
import threading
import time
import traceback

import pika
import requests
import sys

from my_utils.log_utils import print_in_log
from my_utils.mq_utils import pingToWatchdog, stopToWatchdog

import constants as c


def check_server_reachability():
    ip_port = c.server_ip.split(":")
    try:
        socket.create_connection((ip_port[0], ip_port[1]), timeout=5)
        print_in_log(f"Server {ip_port[0],}:{ip_port[1]} is reachable.")
        return True
    except socket.error as e:
        print_in_log(f"Server {ip_port[0],}:{ip_port[1]} is not reachable. Error: {e}")
        return False


def send_data(file_path):
    with open(file_path, "rb") as file:
        files = {'file': (file_path, file)}
        try:
            response = requests.post(c.url, files=files)
            return response.status_code
        except requests.exceptions.ConnectionError:
            print_in_log("Server non trovato. Verificare che il server sia acceso per il trasferimento.")
            return "errore"


def send_data_to_server(timestamp, freq, dbmm2value, vmvalue):
    json_data = {
        "location": c.location,  # Sostituisci con il tuo luogo
        "timestamp": timestamp,
        "freq": freq,
        "dbmm2value": dbmm2value,
        "vmvalue": vmvalue
    }

    # Invia la richiesta POST al server Flask
    response = requests.post(c.url, json=json_data)

    # Verifica lo stato della risposta

    return str(response.status_code)




def callback_transfer_iq_data(ch, method, properties, body):
    print_in_log("Callback transfer iq attivato")

    if (check_server_reachability == False):
        print_in_log("Server irraggiungibile... provare più tardi")
        return
    
    msg = send_data(body.decode())
    ch.basic_publish(exchange='',
                     routing_key='T-S',
                     body=("IQ_"+msg).encode("utf-8"))
    if msg == "OK":
        os.remove(body)

def init_send_simple_data(logfile):
    print_in_log("Inizio trasferimento file "+logfile)
    logfile_strings = logfile.rsplit(".", 1)

    with open(logfile, 'r') as file:
        lines = file.readlines()
    emptyfile = True
    with open(logfile_strings[0] + "temp." + logfile_strings[1], 'w') as file:
        for line in lines:
            # Dividi la riga in timestamp, freq, dbmm2, vmvalue
            parts = line.split()
            if len(parts) == 4:
                timestamp, freq, dbmm2value, vmvalue = parts

                # Invia i dati al server Flask
                ok = False
                for i in range(5):
                    response = send_data_to_server(timestamp, float(freq), float(dbmm2value), float(vmvalue))
                    if (response == "200"):
                        ok = True
                        break
                    else:
                        print_in_log(response)
                    time.sleep(1)
                if (not ok):
                    file.write(line)
                    emptyfile = False
    #os.remove(logfile)
    if emptyfile:
        #os.remove(logfile_strings[0] + "temp." + logfile_strings[1])
        print_in_log("Trasferimento completato correttamente.")
    else:
        #os.rename(logfile_strings[0] + "temp." + logfile_strings[1], logfile)
        print_in_log("Trasferimento completato, ma qualche entry non è stata inviata.")


def callback_transfer_normal_data(ch, method, properties, body):
    print_in_log("Callback transfer normal attivato")
    if (check_server_reachability == False):
        print_in_log("Server irraggiungibile... provare più tardi")
        return
    filename = body.decode("utf-8")

    c.isTransfering = True
    try:
        init_send_simple_data(filename)
        send_data(c.error_log_file)
    except Exception:
        print_in_log("Errore in fase di trasmissione, vedere log di transfer.")
        with open(c.service_log_file.rsplit(".",1)[0] + ".log", "a") as logfile:
            traceback.print_exc(file=logfile)
    finally:
        c.isTransfering = False

    # directory = c.data_folder+"\\measures"
    # for file in os.listdir(directory):
    #     if file.endswith('.txt'):
    #         try:
    #             init_send_simple_data(directory+"\\"+file)
    #         except FileNotFoundError:
    #             pass


    try:
        ch.basic_publish(exchange='',
                     routing_key='T-S',
                     body=("normal_OK").encode("utf-8"))
    except pika.exceptions.StreamLostError:
        ch.basic_publish(exchange='',
                     routing_key='T-S',
                     body=("normal_OK").encode("utf-8"))


def consume_thread():
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))
    channel = connection.channel()

    channel.queue_declare(queue='T-S')
    channel.queue_declare(queue='T-W')
    channel.queue_declare(queue='S-T')
    channel.queue_declare(queue='P-T')

    pingToWatchdog(channel)
    try:
        channel.basic_consume(queue='P-T', on_message_callback=callback_transfer_iq_data, auto_ack=True)
        channel.basic_consume(queue='S-T', on_message_callback=callback_transfer_normal_data, auto_ack=True)
        channel.start_consuming()
    except KeyboardInterrupt:
        stopToWatchdog(channel)


def start_consuming_thread():
    # Crea un thread e avvia la funzione consume()
    thread = threading.Thread(target=consume_thread)
    thread.daemon = True
    thread.start()

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params, heartbeat=600,
                                                                   blocked_connection_timeout=300))
    channel = connection.channel()
    if (not (4 <= datetime.datetime.now().hour < 7) and not c.debug_transfer):
        stopToWatchdog(channel)
        connection.close()
        print_in_log("Orario di inizio errato (" + str(datetime.datetime.now().hour)+")")
        return
    print_in_log("Transfer microservice ON (" + str(datetime.datetime.now().hour)+")")
    start_consuming_thread()

    #TODO: Provvisorio, capire come gestire bene watchdog
    now = datetime.datetime.now()
    delta = datetime.timedelta(hours=3)
    while (now+delta > datetime.datetime.now() or c.isTransfering):
        time.sleep(30)
        pingToWatchdog(channel)
    stopToWatchdog(channel)
    connection.close()
    return

if __name__ == "__main__":
    main()
