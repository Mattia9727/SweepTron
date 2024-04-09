import datetime
import threading
import time

import win32serviceutil
import constants as c

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
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Watchdog] Servizio Watchdog interrotto.")
        exit(0)

def start_restarter_thread():
    # Crea un thread e avvia la funzione consume()
    thread = threading.Thread(target=restarter)
    thread.daemon = True
    thread.start()
