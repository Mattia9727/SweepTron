import os
import socket
import time
import pika
import requests
from my_utils import constants as c


def check_server_reachability():
    try:
        ip_port = c.server_ip.split(":")
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

    last_transfer_data=""
    msg = "errore"
    if body!="old":
        last_transfer_data = body
    if last_transfer_data !="":
        msg = send_data(last_transfer_data)
    ch.basic_publish(exchange='',
                     routing_key='T-S',
                     body=("normal_"+msg).encode("utf-8"))
    if msg == "OK":
        os.remove(last_transfer_data)


if __name__ == "__main__":
    print("Transfer microservice ON")
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))
    channel = connection.channel()

    channel.queue_declare(queue='T-S')
    channel.queue_declare(queue='S-T')
    channel.queue_declare(queue='P-T')

    channel.basic_consume(queue='P-T', on_message_callback=callback_transfer_iq_data, auto_ack=True)
    channel.basic_consume(queue='S-T', on_message_callback=callback_transfer_normal_data, auto_ack=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(' [x] Consumatore interrotto.')
