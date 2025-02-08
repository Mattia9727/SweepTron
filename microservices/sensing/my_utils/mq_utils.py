import os
import time
from datetime import datetime

import constants as c

from .log_utils import print_in_log


def callback_transfer_data(channel, method, properties, body):
    msg = body.decode()
    if msg.split("_")[0] == "IQ":
        c.isTransferingIQ = False
        if msg.split("_")[1] == "OK":
            print_in_log("[Ricezione da Transfer] Trasferimento IQ completato")
        else:
            print_in_log("[Ricezione da Transfer] Trasferimento IQ fallito")

    else:
        c.isTransfering = False
        if msg.split("_")[1] == "OK":
            print_in_log("[Ricezione da Transfer] Trasferimento cattura normale completato")
        else:
            print_in_log("[Ricezione da Transfer] Trasferimento cattura normale fallito")



def send_iq_capture(ch):
    print_in_log("[Invio a Transfer] Invio cattura IQ al processing MS per compressione.")

    # if os.path.isfile(c.log_file[:-4] + "_tosend.dgz"):
    #     print_in_log("[Invio a Transfer] Trasferimento di cattura IQ non ancora completato, attendere...")
    #     ch.basic_publish(exchange='',
    #                      routing_key='S-P',
    #                      body="iq_old")
    # else:
    iq_normal_files = os.listdir(c.iq_measures_dir)
    if len(iq_normal_files) > 0:
        for file_name in iq_normal_files:
            file_path = c.iq_measures_dir + "\\" + file_name
            # Invia il messaggio alla coda
            ch.basic_publish(exchange='',
                             routing_key='S-P',
                             body=file_path.encode("utf-8"))

def send_normal_capture(ch):
    print_in_log("[Invio a Transfer] Invio cattura normale al transfer per invio.")

    # if os.path.isfile(c.log_file[:-4] + "_tosend.dgz"):
    #     print_in_log("[Invio a Transfer] Trasferimento di cattura normale non ancora completato, attendere...")
    #     ch.basic_publish(exchange='',
    #                      routing_key='S-T',
    #                      body="old")
    # else:
    d = datetime.now()
    name_with_date = c.log_file[:-4] + "_"+str(d.date())+"_{}{}{}_{}{}{}.txt".format(d.day,d.month,d.year,d.hour,d.minute,d.second)
    new_name_list = []
    if (c.debug_transfer): # Si può effettuare sempre il trasferimento di tutti i file della cartella rimuovendo questo if e mantenendo solo la riga della prima condizione.
        new_name_list = [os.path.join(c.measures_dir,file) for file in os.listdir(c.measures_dir) if os.path.isfile(os.path.join(c.measures_dir, file)) and file.endswith('.txt')]
    else:
        new_name_list = new_name_list.append(name_with_date)

    for new_name in new_name_list:
        try:
            if (not c.debug_transfer):
                while c.lock_file == True:
                    time.sleep(0.01)
                c.lock_file = True
                os.rename(c.log_file, new_name)
                c.lock_file = False
            ch.basic_publish(exchange='',
                            routing_key='S-T',
                            body=new_name)
        except FileNotFoundError:
            print_in_log("Transfer started but no captures found. Stop transfer phase...")
        except FileExistsError:
            print_in_log("Something strange happened (datetime_now?)")
            exit(0)

def send_error_log(ch):
    print_in_log("[Invio a Transfer] Invio log di errore al transfer per invio.")

    # if os.path.isfile(c.log_file[:-4] + "_tosend.dgz"):
    #     print_in_log("[Invio a Transfer] Trasferimento di cattura normale non ancora completato, attendere...")
    #     ch.basic_publish(exchange='',
    #                      routing_key='S-T',
    #                      body="old")
    # else:
    d = datetime.now()
    new_name = c.error_log_file[:-4] + "_"+str(d.date())+"_{}{}{}_{}{}{}.txt".format(d.day,d.month,d.year,d.hour,d.minute,d.second)
    try:
        #while c.error_lock_file == True:
        #    time.sleep(0.01)
        #c.error_lock_file = True
        os.rename(c.error_log_file, new_name)
        #c.error_lock_file = False
        ch.basic_publish(exchange='',
                         routing_key='S-T',
                         body=new_name)
    except FileNotFoundError:
        print_in_log("Transfer started but no errors found. Stop transfer phase...")
    except FileExistsError:
        print_in_log("Something strange happened (datetime_now?)")
        exit(0)




def startTransferData(ch):
    print_in_log("[Invio a Transfer] Trasferimento iniziato")
    normal_files = os.listdir(c.measures_dir)
    iq_normal_files = os.listdir(c.iq_measures_dir)

    # Verifica se ci sono file nella cartella
    if len(normal_files) > 0:
        c.isTransfering = True
        send_normal_capture(ch)

    if len(iq_normal_files) > 0:
        c.isTransfering = True
        send_iq_capture(ch)

def pingToWatchdog(channel):
    channel.basic_publish(exchange='',
                     routing_key='S-W',
                     body="ping")

def stopToWatchdog(channel):
    channel.basic_publish(exchange='',
                     routing_key='S-W',
                     body="stop")
