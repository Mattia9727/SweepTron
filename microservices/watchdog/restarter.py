import datetime
import threading
import time

import win32serviceutil
import constants as c
from microservices.watchdog.my_utils.log_utils import print_in_log


def restart_service(service_name):

    win32serviceutil.RestartService(service_name)
    if service_name == "SweepTron_Sensing":
        c.sensing_activity = False
    elif service_name == "SweepTron_Processing":
        c.processing_activity = False
    elif service_name == "SweepTron_Transfer":
        c.transfer_activity = False
    print('[Watchdog] {} restarted'.format(service_name))
    return

def start_all():
    restart_service("SweepTron_Transfer")
    restart_service("SweepTron_Processing")
    restart_service("SweepTron_Sensing")
    return

def restart_system():
    import os
    print_in_log("[Watchdog] Riavvio del sistema")
    os.system("shutdown -r -f")

def restarter():
    try:
        start_all()
        while(True):
            if (c.sensing_activity != False and c.sensing_activity + datetime.timedelta(minutes=5) < datetime.datetime.now()):
                restart_service("SweepTron_Sensing")
            if (c.processing_activity != False and c.processing_activity + datetime.timedelta(minutes=5) < datetime.datetime.now()):
                restart_service("SweepTron_Processing")
            if (c.transfer_activity != False and c.transfer_activity + datetime.timedelta(minutes=5) < datetime.datetime.now()):
                restart_service("SweepTron_Transfer")
            if (c.sensing_activity != False and c.sensing_activity + datetime.timedelta(minutes=15) < datetime.datetime.now()):
                restart_system()
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Watchdog] Servizio Watchdog interrotto.")
        exit(0)

def start_restarter_thread():
    # Crea un thread e avvia la funzione consume()
    thread = threading.Thread(target=restarter)
    thread.daemon = True
    thread.start()
