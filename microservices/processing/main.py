import time
import os
import pika
import lzma
import constants as c


def compress_iq_lzma(body):
    with open(body, "rb") as f:
        data = f.read()
    print(body)
    body2 = body.decode().replace(c.iq_measures_dir,c.processed_iq_measures_dir)
    with lzma.open(body2, "w") as f:
        f.write(data)
    os.remove(body.decode())
    return body2


def callback_processing_data(ch, method, properties, body):
    print("Callback processing attivato")
    body2 = compress_iq_lzma(body)
    ch.basic_publish(exchange='',
                     routing_key='P-T',
                     body=body2.encode("utf-8"))


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
