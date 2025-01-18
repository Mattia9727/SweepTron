"""
# Prerequisites:
pip3 install pywin32 pyinstaller

# Build:
pyinstaller.exe --onefile --runtime-tmpdir=. --hidden-import win32timezone myservice.py

# With Administrator privilges
# Install:
dist\myservice.exe install

# Start:
dist\myservice.exe start

# Install with autostart:
dist\myservice.exe --startup delayed install

# Debug:
dist\myservice.exe debug

# Stop:
dist\myservice.exe stop

# Uninstall:
dist\myservice.exe remove


"""
import sys
import time
import servicemanager
import win32service
import win32serviceutil
import logging

from main import sensing_init

LOG_FILE = "C:\\SweepTron_Sensing_reporting.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class MyService:

    """Silly little application stub"""
    def stop(self):
        """Stop the service"""
        self.running = False

    def run(self):
        """Main service loop. This is where work is done!"""
        self.running = True
        while self.running:
            logging.info("Service is running...")
            servicemanager.LogInfoMsg("Service running...")  # Scrive nei registri eventi Windows
            try:
                sensing_init()  
            except Exception as e:
                logging.error(f"error during sensing_init(): {e}", exc_info=True)

            time.sleep(10)  # Attende 10 secondi
        


class MyServiceFramework(win32serviceutil.ServiceFramework):

    _svc_name_ = 'SweepTron_Sensing'
    _svc_display_name_ = 'SweepTron: Data capture service.'

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.service_impl.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        """Start the service; does not return until stopped"""
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.service_impl = MyService()
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        # Run the service
        self.service_impl.run()


def init():
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MyServiceFramework)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MyServiceFramework)


if __name__ == '__main__':
    init()