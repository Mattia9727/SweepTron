import time
import pika
import requests
from microservices.transfer.my_utils import constants as c


def main():
    print("I will transfer something")
    while True:
        time.sleep(1)


def send_data(file_path):
    with open(file_path, "rb") as file:
        files = {'file': (file_path, file)}
        response = requests.post(c.url, files=files)

    print(response.text)


def callback_transfer_iq_data(ch, method, properties, body):
    send_data("../../data/compressed_data_{}.txt".format(body))
    ch.basic_publish(exchange='',
                     routing_key='P-T',
                     body=body)


def callback_transfer_normal_data(ch, method, properties, body):
    send_data("../../data/compressed_data_{}.txt".format(body))
    ch.basic_publish(exchange='',
                     routing_key='P-T',
                     body=body)


if __name__ == "__main__":
    print("Transfer microservice ON")
    time.sleep(60)
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))
    channel = connection.channel()

    channel.queue_declare(queue='T-S')
    channel.queue_declare(queue='S-T')
    channel.queue_declare(queue='P-T')

    channel.basic_consume(queue='P-T', on_message_callback=callback_transfer_iq_data, auto_ack=True)
    channel.basic_consume(queue='S-T', on_message_callback=callback_transfer_normal_data, auto_ack=True)

    channel.start_consuming()
    # send_files_to_server()
