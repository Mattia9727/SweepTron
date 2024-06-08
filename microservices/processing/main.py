import datetime
import threading
import time
import os
import pika
import lzma
import constants as c
from my_utils.log_utils import print_in_log
from my_utils.mq_utils import stopToWatchdog, pingToWatchdog


def compress_iq_lzma(body):
    with open(body, "rb") as f:
        data = f.read()
    print_in_log("Compressing " + body.decode())
    body2 = body.decode().replace(c.iq_measures_dir,c.processed_iq_measures_dir)
    with lzma.open(body2, "w") as f:
        f.write(data)
    os.remove(body.decode())
    return body2


def callback_processing_data(ch, method, properties, body):
    c.compressing+=1
    print_in_log("Callback processing attivato")
    body2 = compress_iq_lzma(body)
    print_in_log("Processamento di " + body.decode() + " completato")
    ch.basic_publish(exchange='',
                     routing_key='P-T',
                     body=body2.encode("utf-8"))
    c.compressing-=1

def consume_thread():
    connection = pika.BlockingConnection(pika.ConnectionParameters(c.pika_params))
    channel = connection.channel()
    channel.queue_declare(queue='P-T')
    channel.queue_declare(queue='S-P')
    channel.queue_declare(queue='P-W')
    pingToWatchdog(channel)
    try:
        channel.basic_consume(queue='S-P', on_message_callback=callback_processing_data, auto_ack=True)
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

    if (not(4<=datetime.datetime.now().hour<7) and not c.debug_transfer):
        stopToWatchdog(channel)
        print_in_log("Orario di inizio errato (" + str(datetime.datetime.now().hour)+")")
        return

    print_in_log("Processing microservice ON (" + str(datetime.datetime.now().hour)+")")
    start_consuming_thread()

    # TODO: Provvisorio, capire come gestire bene watchdog
    now = datetime.datetime.now()
    delta = datetime.timedelta(hours=3)
    while (now + delta > datetime.datetime.now() or c.compressing > 0):
        time.sleep(30)
        pingToWatchdog(channel)
    stopToWatchdog(channel)
    connection.close()

    return


if __name__ == "__main__":
    main()
