# SweepTron - Applicazione nodo di misurazione

## Build dei servizi
1. Installare Python 3.9 o successivi
2. Creare un ambiente virtuale di Python (venv) (non necessario ma consigliato per mantenere un ambiente pulito per la build di SweepTron):
   
   ```
   python -m venv nomeambientevirtuale
   ```
   
3. Installare le librerie presenti nel file requirements.txt, situato nella root della repository:

   ```
   pip install -r requirements.txt
   ```

4. Lanciare lo script *build_all_services_onedir.bat*, situato nella root della repository (attenzione a modificare i path nello script in modo opportuno):

  ```
  .\build_all_services_onedir.bat
  ```

5. Le build dei servizi verranno messi nella cartella *onedirs*, il cui path è definito all'interno dello script *build_all_services_onedir.bat*.

## Setup PC nodo di misurazione
Per effettuare il setup del nodo di misurazione devono essere installati i seguenti programmi:

1. Driver analizzatore:
- Rack MS27201A: https://www.anritsu.com/en-us/test-measurement/support/downloads?model=MS2720xA
- Ultraportable MS2760A: https://www.anritsu.com/en-us/test-measurement/support/downloads?model=MS2760A

2. RabbitMQ: https://www.rabbitmq.com/docs/install-windows (installare anche Erlang come richiesto dall'installer di RabbitMQ)

3. Google Chrome + Chrome Remote Desktop

Inoltre, è necessario copiare sul Desktop la cartella SweepTronData presente nella repository, nella cartella *scripts e init*. La cartella SweepTronData contiene i seguenti elementi:

1. config.json: variabili di configurazione acquisite a runtime dai microservizi in esecuzione.

2. measures: cartella contenente le acquisizioni.

3. iq_measures: cartella contenente le catture IQ effettuate.

4. processed_iq_measures: cartella contenente le catture IQ compresse.

5. logs: cartella contenente i log dei microservizi in esecuzione.

Per la configurazione iniziale è importante impostare *config.json*, in particolare per i campi:

1. location: nome del nodo (es: Comune Bologna, Encelado, ecc...). Da notare che questo nome identifica i dati acquisiti su InfluxDB.

2. device_type: definisce il tipo di analizzatore (rack:MS27201A o ultraportable:MS2760A)

3. antenna_file/af_keysight: IMPORTANTE PER NON SFALSARE LE ACQUISIZIONI, definisce dei fattori per la conversione in dBm/m^2 e V/m. La stringa *antenna_file* è usata per impostare l'antenna factor sull'analizzatore rack, mentre la stringa *af_keysight* definisce il nome del file locale che contiene l'antenna factor, che viene utilizzato per convertire lato PC embedded i dati acquisiti dall'ultraportable.

4. (iq_)frequency_start/(iq_)frequency_stop: liste di frequenze da monitorare (ES: con una configurazione di questo tipo:
   ```
    "frequency_start": [3440, 3540, 3560, 3620, 3640, 3720, 758, 768, 778],
    "frequency_stop": [3500, 3560, 3620, 3640, 3720, 3800, 768, 778, 788],
   ```
   stiamo monitorando 8 bande, dove la prima va da 3440 a 3500 MHz, la seconda va da 3540 a 3560 MHz, e così via).

## Installazione servizi nodo di misurazione

1. Inviare l'archivio *services.zip*, generato tramite lo script *build_all_services_onedir.bat*, al PC Embedded del nodo da configurare, ed estrarre le cartelle contenute nell'archivio sul PC.

2. Avviare *powershell* o *cmd* come amministratore.

3. Lanciare i seguenti comandi sugli eseguibili delle cartelle estratte precedentemente per installare i servizi:

  ```
  sensing.exe install
  processing.exe install
  transfer.exe install
  watchdog.exe --startup delayed install
  ```

4. Per avviare i servizi è sufficiente lanciare il servizio di watchdog:
  
  ```
  watchdog.exe start
  ```
