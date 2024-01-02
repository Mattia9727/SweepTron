import time

import pika
import lzma
import constants as c


def compress_iq_lzma(body):
    with open(c.log_file + ".dgz", "rb") as f:
        data = f.read()

    with lzma.open("../../data/compressed_data_{}.txt".format(body), "w") as f:
        f.write(data)


def callback_processing_data(ch, method, properties, body):
    compress_iq_lzma(body)

    ch.basic_publish(exchange='',
                     routing_key='P-T',
                     body=body)


def start_processing_data():
    time.sleep(20)
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))
    channel = connection.channel()
    channel.queue_declare(queue='P-T')
    channel.queue_declare(queue='S-P')

    channel.basic_consume(queue='S-P', on_message_callback=callback_processing_data, auto_ack=True)

    channel.start_consuming()


if __name__ == "__main__":
    print("Processing microservice ON")
    start_processing_data()
