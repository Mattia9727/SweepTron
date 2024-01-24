import time

import pika
import lzma
from data import constants as c


def compress_iq_lzma(body):
    with open(body, "rb") as f:
        data = f.read()

    with lzma.open(body+"_compressed", "w") as f:
        f.write(data)


def callback_processing_data(ch, method, properties, body):
    print("Callback processing attivato")
    compress_iq_lzma(body)
    ch.basic_publish(exchange='',
                     routing_key='P-T',
                     body=body)


def start_processing_data():
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))
    channel = connection.channel()
    channel.queue_declare(queue='P-T')
    channel.queue_declare(queue='S-P')

    channel.basic_consume(queue='S-P', on_message_callback=callback_processing_data, auto_ack=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(' [x] Consumatore interrotto.')


if __name__ == "__main__":
    print("Processing microservice ON")
    start_processing_data()
