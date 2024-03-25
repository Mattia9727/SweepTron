import datetime
import threading
import time

import socket

import win32serviceutil

import pika

from restarter import start_restarter_thread

import constants as c


def callback_sensing(ch, method, properties, body):
    if (body.decode("utf-8") == "stop"):
        c.sensing_activity = False
        print("[Watchdog] Sensing -> Stop")
    elif (body.decode("utf-8") == "ping"):
        if (c.sensing_activity==False): print("[Watchdog] Sensing -> Start")
        c.sensing_activity = datetime.datetime.now()
        print("[Watchdog] Sensing -> Ping")
    else: print("[Watchdog] Messaggio inaspettato da Sensing")

def callback_processing(ch, method, properties, body):
    if (body.decode("utf-8") == "stop"):
        c.processing_activity = False
        print("[Watchdog] Processing -> Stop")
    elif (body.decode("utf-8") == "ping"):
        if (c.processing_activity==False): print("[Watchdog] Processing -> Start")
        c.processing_activity = datetime.datetime.now()
        print("[Watchdog] Processing -> Ping")
    else:
        print("[Watchdog] Messaggio inaspettato da Processing")

def callback_transfer(ch, method, properties, body):
    if (body.decode("utf-8") == "stop"):
        c.transfer_activity = False
        print("[Watchdog] Transfer -> Stop")
    elif (body.decode("utf-8") == "ping"):
        if (c.transfer_activity==False): print("[Watchdog] Transfer -> Start")
        c.transfer_activity = datetime.datetime.now()
        print("[Watchdog] Transfer -> Ping")
    else:
        print("[Watchdog] Messaggio inaspettato da Transfer")

def main():
    print("[Watchdog] Start service")
    start_restarter_thread()
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))
    channel = connection.channel()

    channel.queue_declare(queue='S-W')
    channel.queue_declare(queue='P-W')
    channel.queue_declare(queue='T-W')

    channel.basic_consume(queue='S-W',
                          auto_ack=True,
                          on_message_callback=callback_sensing)
    channel.basic_consume(queue='P-W',
                          auto_ack=True,
                          on_message_callback=callback_processing)
    channel.basic_consume(queue='T-W',
                          auto_ack=True,
                          on_message_callback=callback_transfer)

    while(True):
        print("Wait for messages")
        channel.start_consuming()
        print("Wait done")

if __name__ == "__main__":
    main()
