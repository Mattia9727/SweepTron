import time

import docker
import socket

import pika


def main():
    print("I will have some watchdog functionalities")
    while True:
        time.sleep(1)

def callback(ch, method, properties, body):
    print(f" [x] Received {body}")

if __name__ == "__main__":

    connection = pika.BlockingConnection(pika.ConnectionParameters("amqp://guest:guest@rabbitmq/"))
    channel = connection.channel()

    channel.queue_declare(queue='W-P')
    channel.queue_declare(queue='T-W')

    channel.basic_publish(exchange='',
                          routing_key='W-P',
                          body=b'Hello Processing!')
    time.sleep(1)
    channel.basic_consume(queue='T-W',
                          auto_ack=True,
                          on_message_callback=callback)

    main()