import pika

from my_utils.sensing_utils import get_gps_info, measure
from my_utils.mq_utils import callbackTransferData, startTransferData
from my_utils.anritsu_conn_utils import connect_to_device, find_device, setup_anritsu_device

from my_utils import constants as c


def sensing(ch):
    # Crea un socket
    find_device()
    conn = connect_to_device()
    location_name = get_gps_info(conn)
    setup_anritsu_device(conn)

    # Monitoring of all DL frequencies
    while True:  # You might want to replace 'True' with a condition to stop the loop
        condition = True
        # condition = 4 <= datetime.datetime.now().hour <= 7
        if 4 <= condition:
            if c.transferedToday == 0:
                startTransferData(ch)
            c.transferedToday = 1
        else:
            c.transferedToday = 0

        measure(conn, location_name)


if __name__ == "__main__":
    print("Sensing microservice ON")

    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))
    channel = connection.channel()

    channel.queue_declare(queue='S-P')
    channel.queue_declare(queue='S-T')
    channel.queue_declare(queue='T-S')

    channel.basic_consume(queue='T-S',
                          auto_ack=True,
                          on_message_callback=callbackTransferData)

    sensing(channel)
