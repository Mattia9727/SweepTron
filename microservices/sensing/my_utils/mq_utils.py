import os
from datetime import datetime

from . import constants as c


def callbackTransferData():
    c.isTransfering = False
    print("Trasferimento completato")


def startTransferData(ch):
    print("Trasferimento iniziato")
    if os.path.isfile(c.log_iq_file):
        print("Invio cattura IQ al processing per compressione.")

        # Invia il messaggio alla coda
        ch.basic_publish(exchange='',
                              routing_key='S-P',
                              body=datetime.now().isoformat().encode('utf-8'))

    if os.path.isfile(c.log_file):
        print("Invio cattura normale al transfer per invio.")
        ch.basic_publish(exchange='',
                              routing_key='S-T',
                              body=datetime.now().isoformat().encode('utf-8'))

    c.isTransfering = True


