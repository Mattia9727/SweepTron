import datetime
import os
import socket
import threading
import time
import pika
import requests
import sys

from my_utils.mq_utils import pingToWatchdog, stopToWatchdog

import constants as c


def check_server_reachability():
    ip_port = c.server_ip.split(":")
    try:
        socket.create_connection((ip_port[0], ip_port[1]), timeout=5)
        print(f"Server {ip_port[0],}:{ip_port[1]} is reachable.")
        return True
    except socket.error as e:
        print(f"Server {ip_port[0],}:{ip_port[1]} is not reachable. Error: {e}")
        return False


def send_data(file_path):
    with open(file_path, "rb") as file:
        files = {'file': (file_path, file)}
        try:
            response = requests.post(c.url, files=files)
            return("OK")
        except requests.exceptions.ConnectionError:
            print("Server non trovato. Verificare che il server sia acceso per il trasferimento.")
            return("errore")


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

    # # Verifica lo stato della risposta
    # if response.status_code == 200:
    #     print("Dati inviati correttamente al server.")
    # else:
    #     print("Errore durante l'invio dei dati al server.")
    return str(response.status_code)




def callback_transfer_iq_data(ch, method, properties, body):
    print("Callback transfer iq attivato")

    if (check_server_reachability == False):
        print("Server irraggiungibile... provare più tardi")
        return
    
    msg = send_data(body.decode())
    ch.basic_publish(exchange='',
                     routing_key='T-S',
                     body=("IQ_"+msg).encode("utf-8"))
    if msg == "OK":
        os.remove(body)


def callback_transfer_normal_data(ch, method, properties, body):
    print("Callback transfer normal attivato")

    if (check_server_reachability == False):
        print("Server irraggiungibile... provare più tardi")
        return

    body_strings = body.decode("utf-8").rsplit(".",1)

    with open(body, 'r') as file:
        lines = file.readlines()
    emptyfile = True
    with open(body_strings[0]+"temp."+body_strings[1], 'w') as file:
        for line in lines:
            # Dividi la riga in timestamp, freq, dbmm2, vmvalue
            parts = line.split()
            if len(parts) == 4:
                timestamp, freq, dbmm2, vmvalue = parts

                # Invia i dati al server Flask
                ok = False
                for i in range(5):
                    if(send_data_to_server(timestamp, float(freq), float(dbmm2), float(vmvalue)) == "200"):
                        ok=True
                        break
                if(not ok):
                    file.write(line)
                    emptyfile = False
    os.remove(body)
    if emptyfile:
        os.remove(body_strings[0]+"temp."+body_strings[1])
    else:
        os.rename(body_strings[0]+"temp."+body_strings[1],body)


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
    print("Transfer microservice ON")
    if (4 < datetime.datetime.now().hour < 7): exit(0)
    with(open("C:\\Users\\matti\\Desktop\\debugservizio.txt", "a") as f):
        f.write("Sensing microservice ON")
    start_consuming_thread()
    time.sleep(10800)
    exit(0)

if __name__ == "__main__":
    main()
